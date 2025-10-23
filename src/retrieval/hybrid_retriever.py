"""
Hybrid Retriever: BM25 + Dense + Interpretation-Aware Boosting
"""

import os
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from elasticsearch import Elasticsearch
import faiss
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from src.database.models.interpretation_link import InterpretationLink
from src.database.models import Document
# Note: Update this import if you have an IndexUnit model elsewhere

logger = logging.getLogger(__name__)


@dataclass
class RetrievalConfig:
    """Configuration for hybrid retrieval"""
    top_k: int = 10
    bm25_weight: float = 0.4
    dense_weight: float = 0.4
    lepard_weight: float = 0.2
    max_interpretive_cases: int = 3
    interpretation_boost_enabled: bool = True
    diversification_enabled: bool = True


class HybridRetriever:
    """
    Hybrid retrieval combining:
    1. BM25 (Elasticsearch) - keyword matching
    2. Dense (FAISS) - semantic similarity
    3. Interpretation-aware boosting - query interpretation_links
    """
    
    def __init__(
        self,
        db_session: Session,
        es_client: Elasticsearch,
        faiss_index: faiss.Index,
        embedding_client: OpenAI,
        config: RetrievalConfig = None
    ):
        self.db = db_session
        self.es = es_client
        self.faiss = faiss_index
        self.embedder = embedding_client
        self.config = config or RetrievalConfig()
        
        # Load FAISS mapping
        mapping_path = 'data/faiss/doc_id_mapping.json'
        if os.path.exists(mapping_path):
            import json
            with open(mapping_path, 'r') as f:
                self.faiss_mapping = json.load(f)
            logger.info(f"Loaded FAISS mapping with {len(self.faiss_mapping)} entries")
        else:
            self.faiss_mapping = {}
            logger.warning(f"FAISS mapping not found at {mapping_path}")
        
        # Embedding model
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-large')
        
        logger.info("HybridRetriever initialized")
    
    def retrieve(
        self,
        query: str,
        k: int = None,
        use_interpretation_links: bool = True
    ) -> List[Dict]:
        """
        Main retrieval pipeline
        
        Args:
            query: User query
            k: Number of results to return (default: config.top_k)
            use_interpretation_links: Whether to boost interpretive cases
        
        Returns:
            List of document dictionaries with scores and metadata
        """
        k = k or self.config.top_k
        
        # Step 1: BM25 retrieval
        bm25_results = self._bm25_search(query, k=200)
        logger.debug(f"BM25 returned {len(bm25_results)} results")
        
        # Step 2: Dense retrieval
        dense_results = self._dense_search(query, k=200)
        logger.debug(f"Dense returned {len(dense_results)} results")
        
        # Step 3: Merge and rerank
        merged_results = self._merge_results(
            bm25_results,
            dense_results,
            k=500
        )
        logger.debug(f"Merged to {len(merged_results)} results")
        
        # Step 4: Apply interpretation-aware boosting
        if use_interpretation_links and self.config.interpretation_boost_enabled:
            boosted_results = self._apply_interpretation_boost(
                merged_results,
                query
            )
        else:
            boosted_results = merged_results
        
        # Step 5: Diversification (max 3 interpretive cases per statute)
        if self.config.diversification_enabled:
            final_results = self._diversify_results(boosted_results, k)
        else:
            final_results = sorted(
                boosted_results,
                key=lambda x: x['score'],
                reverse=True
            )[:k]
        
        logger.info(f"Retrieval complete: returned {len(final_results)} docs")
        return final_results
    
    def _bm25_search(self, query: str, k: int) -> List[Dict]:
        """BM25 search using Elasticsearch"""
        try:
            response = self.es.search(
                index="legal_documents",
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^2", "text", "citation^1.5"],
                            "type": "best_fields",
                            "tie_breaker": 0.3
                        }
                    },
                    "size": k
                }
            )
            
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    'doc_id': hit['_source']['unit_id'],
                    'content': hit['_source']['text'],
                    'citation': hit['_source'].get('citation'),
                    'doc_type': hit['_source']['doc_type'],
                    'score': hit['_score'],
                    'retrieval_method': 'bm25'
                })
            
            return results
        
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
    
    def _dense_search(self, query: str, k: int) -> List[Dict]:
        """Dense search using FAISS"""
        try:
            # Generate query embedding
            query_embedding = self._get_embedding(query)
            
            # Search FAISS index
            distances, indices = self.faiss.search(
                np.array([query_embedding]),
                k
            )
            
            # Retrieve document metadata from database using mapping
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1:  # Invalid index
                    continue
                
                # Get doc_id from mapping
                idx_str = str(idx)
                if idx_str not in self.faiss_mapping:
                    logger.warning(f"Index {idx} not in mapping")
                    continue
                
                doc_id = self.faiss_mapping[idx_str]['doc_id']
                
                # Get document from database
                doc = self.db.query(Document).filter(Document.id == doc_id).first()
                
                if doc:
                    # Convert distance to similarity score
                    similarity = 1.0 / (1.0 + distance)
                    
                    results.append({
                        'doc_id': doc.id,
                        'doc_type': doc.doc_type,  # CRITICAL for interpretation boost
                        'content': doc.full_text or doc.title,
                        'title': doc.title,
                        'citation': doc.citation,
                        'score': similarity,
                        'source': 'dense'
                    })
            
            return results
            
        except Exception as e:
            logger.error(
                f"Dense search failed: {type(e).__name__}: {str(e)}",
                exc_info=True,
                extra={
                    'query_length': len(query) if query else 0,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            return []


    def _get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding using OpenAI"""
        response = self.embedder.embeddings.create(
            model=self.embedding_model,
            input=text
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    
    def _merge_results(
        self,
        bm25_results: List[Dict],
        dense_results: List[Dict],
        k: int
    ) -> List[Dict]:
        """
        Merge BM25 and dense results using weighted scores
        
        Score = (bm25_weight * normalized_bm25_score) + 
                (dense_weight * normalized_dense_score)
        """
        # Normalize scores to [0, 1]
        bm25_normalized = self._normalize_scores(bm25_results)
        dense_normalized = self._normalize_scores(dense_results)
        
        # Merge by doc_id
        merged = {}
        
        for result in bm25_normalized:
            doc_id = result['doc_id']
            merged[doc_id] = result
            merged[doc_id]['bm25_score'] = result['score']
            merged[doc_id]['dense_score'] = 0.0
            merged[doc_id]['combined_score'] = (
                self.config.bm25_weight * result['score']
            )
        
        for result in dense_normalized:
            doc_id = result['doc_id']
            if doc_id in merged:
                merged[doc_id]['dense_score'] = result['score']
                merged[doc_id]['combined_score'] += (
                    self.config.dense_weight * result['score']
                )
            else:
                merged[doc_id] = result
                merged[doc_id]['bm25_score'] = 0.0
                merged[doc_id]['dense_score'] = result['score']
                merged[doc_id]['combined_score'] = (
                    self.config.dense_weight * result['score']
                )
        
        # Update main score to combined score
        for doc_id in merged:
            merged[doc_id]['score'] = merged[doc_id]['combined_score']
        
        # Sort by combined score
        sorted_results = sorted(
            merged.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return sorted_results[:k]
    
    def _normalize_scores(self, results: List[Dict]) -> List[Dict]:
        """Normalize scores to [0, 1] range"""
        if not results:
            return results
        
        scores = [r['score'] for r in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All scores are the same
            for r in results:
                r['score'] = 1.0
        else:
            for r in results:
                r['score'] = (r['score'] - min_score) / (max_score - min_score)
        
        return results
    
    def _apply_interpretation_boost(
        self,
        results: List[Dict],
        query: str
    ) -> List[Dict]:
        """
        Boost interpretive cases when statute appears in results
        
        Algorithm:
        1. Detect statutes in top-K results
        2. Query interpretation_links for each statute
        3. Boost matching cases (score *= boost_factor)
        4. Add missing interpretive cases (synthetic score = 0.7 * avg_score)
        """
        # Step 1: Identify statutes in results
        statute_ids = set()
        for result in results[:20]:  # Check top 20
            if result['doc_type'] == 'statute':
                statute_ids.add(result['doc_id'])
        
        if not statute_ids:
            logger.debug("No statutes in top-20, skipping interpretation boost")
            return results
        
        logger.debug(f"Found {len(statute_ids)} statutes in top-20")
        
        # Step 2: Query interpretation_links
        interpretive_cases = self.db.execute(
            text("""
                SELECT 
                    statute_id,
                    case_id,
                    boost_factor,
                    interpretation_type,
                    authority
                FROM interpretation_links
                WHERE statute_id = ANY(:statute_ids)
                  AND (verified = true OR verified IS NULL)
                ORDER BY boost_factor DESC, applicability_score DESC
            """),
            {"statute_ids": list(statute_ids)}
        ).fetchall()
        
        logger.debug(f"Found {len(interpretive_cases)} interpretation links")
        
        if not interpretive_cases:
            return results
        
        # Step 3: Build lookup map
        case_boost_map = {}
        for link in interpretive_cases:
            case_id = link.case_id
            if case_id not in case_boost_map:
                case_boost_map[case_id] = {
                    'boost_factor': link.boost_factor,
                    'statute_id': link.statute_id,
                    'interpretation_type': link.interpretation_type,
                    'authority': link.authority
                }
        
        # Step 4: Boost existing cases
        boosted_count = 0
        for result in results:
            if result['doc_id'] in case_boost_map:
                boost_info = case_boost_map[result['doc_id']]
                result['score'] *= boost_info['boost_factor']
                result['interpretive_boost'] = boost_info['boost_factor']
                result['interprets_statute'] = boost_info['statute_id']
                boosted_count += 1
        
        logger.debug(f"Boosted {boosted_count} existing interpretive cases")
        
        # Step 5: Add missing interpretive cases
        existing_case_ids = {r['doc_id'] for r in results if r.get('doc_type') == 'case'}
        
        # Calculate avg score for synthetic scoring
        avg_score = sum(r['score'] for r in results[:10]) / min(10, len(results)) if results else 0.5
        synthetic_score = 0.7 * avg_score
        
        added_count = 0
        
        for case_id, boost_info in case_boost_map.items():
            if case_id not in existing_case_ids:
                # Fetch case document
                case_doc = self.db.query(Document).filter(Document.id == case_id).first()
                
                if case_doc:
                    # Add with synthetic score
                    results.append({
                        'doc_id': case_doc.id,
                        'doc_type': 'case',
                        'content': case_doc.full_text or case_doc.title,
                        'title': case_doc.title,
                        'citation': case_doc.citation,
                        'score': synthetic_score * boost_info['boost_factor'],
                        'source': 'interpretation_link',
                        'is_interpretive_case': True,
                        'interprets_statute': boost_info['statute_id'],
                        'interpretation_type': boost_info['interpretation_type']
                    })
                    added_count += 1
        
        logger.debug(f"Added {added_count} missing interpretive cases")
        
        return results
        return results
    
    def _diversify_results(
        self,
        results: List[Dict],
        k: int
    ) -> List[Dict]:
        """
        Ensure max 3 interpretive cases per statute in final results
        """
        statute_case_count = {}
        diversified = []
        
        for result in sorted(results, key=lambda x: x['score'], reverse=True):
            # Check if this is an interpretive case
            if 'interprets_statute' in result:
                statute_id = result['interprets_statute']
                count = statute_case_count.get(statute_id, 0)
                
                if count >= self.config.max_interpretive_cases:
                    logger.debug(
                        f"Skipping {result['doc_id']} "
                        f"(already {count} cases for {statute_id})"
                    )
                    continue
                
                statute_case_count[statute_id] = count + 1
            
            diversified.append(result)
            
            if len(diversified) >= k:
                break
        
        return diversified
