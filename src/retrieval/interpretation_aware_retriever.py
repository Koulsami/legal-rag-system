#!/usr/bin/env python3
"""
Interpretation-Aware Retriever

Enhances dense retrieval with interpretation links:
1. Retrieve documents via FAISS (dense search)
2. Identify statutes in results
3. Query interpretation_links for interpretive cases
4. Boost interpretive cases or add them to results
5. Ensure max 3 interpretive cases per statute (diversification)

This is the PRIMARY INNOVATION of the system.
"""

import sys
sys.path.insert(0, '/home/amee/legal-rag-poc')

import logging
from typing import List, Dict, Set
from dataclasses import dataclass
import faiss
import numpy as np
from openai import OpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


@dataclass
class RetrievalConfig:
    """Configuration for interpretation-aware retrieval"""
    top_k: int = 10
    dense_k_multiplier: int = 3  # Retrieve 3x more for reranking
    max_interpretive_per_statute: int = 3  # Max interpretive cases per statute
    min_interpretation_boost: float = 1.5  # Minimum boost factor
    synthetic_penalty: float = 0.7  # Penalty for adding non-retrieved cases


class InterpretationAwareRetriever:
    """
    Enhanced retriever that uses interpretation links to boost relevant cases.
    
    Workflow:
    1. Dense search via FAISS → Get initial candidates
    2. Identify statutes in candidates
    3. Look up interpretation_links for each statute
    4. Boost existing interpretive cases or add missing ones
    5. Diversify: max 3 interpretive cases per statute
    6. Re-rank and return top-k
    """
    
    def __init__(
        self,
        db_session,
        faiss_index,
        doc_id_mapping: Dict,
        openai_client: OpenAI,
        config: RetrievalConfig = None
    ):
        self.db = db_session
        self.index = faiss_index
        self.doc_id_mapping = doc_id_mapping
        self.client = openai_client
        self.config = config or RetrievalConfig()
        
        # Embedding configuration (must match FAISS index)
        self.embedding_model = "text-embedding-3-large"
        
        logger.info(
            f"InterpretationAwareRetriever initialized: "
            f"top_k={self.config.top_k}, "
            f"max_interpretive={self.config.max_interpretive_per_statute}"
        )
    
    def retrieve(self, query: str, k: int = None) -> List[Dict]:
        """
        Main retrieval method with interpretation boost.
        
        Args:
            query: User query
            k: Number of results to return (default: config.top_k)
        
        Returns:
            List of document dicts with scores and metadata
        """
        k = k or self.config.top_k
        
        # Step 1: Dense search
        logger.info(f"Step 1: Dense search for top-{k * self.config.dense_k_multiplier} candidates")
        candidates = self._dense_search(query, k * self.config.dense_k_multiplier)
        
        if not candidates:
            logger.warning("No candidates found in dense search")
            return []
        
        # Step 2: Identify statutes
        logger.info("Step 2: Identifying statutes in candidates")
        statute_ids = self._extract_statute_ids(candidates)
        logger.info(f"Found {len(statute_ids)} statutes in candidates")
        
        # Step 3: Get interpretation links
        logger.info("Step 3: Querying interpretation_links")
        interpretation_map = self._get_interpretation_links(statute_ids)
        logger.info(f"Found {sum(len(cases) for cases in interpretation_map.values())} interpretation links")
        
        # Step 4: Apply interpretation boost
        logger.info("Step 4: Applying interpretation boost")
        boosted_candidates = self._apply_interpretation_boost(
            candidates,
            interpretation_map
        )
        
        # Step 5: Diversify and re-rank
        logger.info("Step 5: Diversifying and re-ranking")
        final_results = self._diversify_and_rerank(boosted_candidates, k)
        
        logger.info(f"Returning {len(final_results)} results")
        return final_results
    
    def _dense_search(self, query: str, k: int) -> List[Dict]:
        """Perform dense search via FAISS"""
        # Embed query
        logger.debug(f"Embedding query: {query[:60]}...")
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=query
        )
        query_embedding = np.array([response.data[0].embedding], dtype='float32')
        
        # Search FAISS
        logger.debug(f"Searching FAISS index for {k} candidates...")
        distances, indices = self.index.search(query_embedding, k)
        
        # Load documents from database
        candidates = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            
            # Get doc_id from mapping
            mapping_entry = self.doc_id_mapping.get(str(idx))
            if not mapping_entry:
                continue
            
            doc_id = mapping_entry.get('doc_id') if isinstance(mapping_entry, dict) else mapping_entry
            if not doc_id:
                continue
            
            # Query database
            result = self.db.execute(
                text("""
                    SELECT id, doc_type, title, full_text, citation, 
                           court, year, section_number, para_no
                    FROM documents
                    WHERE id = :doc_id
                    LIMIT 1
                """),
                {"doc_id": doc_id}
            ).fetchone()
            
            if result:
                # Convert distance to similarity score (lower distance = higher similarity)
                similarity = 1.0 / (1.0 + float(distance))
                
                candidates.append({
                    'id': result.id,
                    'doc_type': result.doc_type,
                    'title': result.title or '',
                    'content': result.full_text,
                    'citation': result.citation or '',
                    'court': result.court or '',
                    'year': result.year,
                    'section_number': result.section_number or '',
                    'para_no': result.para_no,
                    'score': float(similarity),
                    'retrieval_method': 'dense',
                    'is_interpretive': False,
                    'interprets_statute': None,
                    'interpretation_type': None
                })
        
        return candidates
    
    def _extract_statute_ids(self, candidates: List[Dict]) -> List[str]:
        """Extract statute IDs from candidates"""
        statute_ids = []
        for doc in candidates:
            if doc['doc_type'] == 'statute':
                statute_ids.append(doc['id'])
        return statute_ids
    
    def _get_interpretation_links(self, statute_ids: List[str]) -> Dict[str, List[Dict]]:
        """
        Query interpretation_links table for all statute IDs.
        
        Returns:
            Dict mapping statute_id -> list of interpretive case info
        """
        if not statute_ids:
            return {}
        
        # Query interpretation links
        result = self.db.execute(
            text("""
                SELECT 
                    il.statute_id,
                    il.case_id,
                    il.interpretation_type,
                    il.authority,
                    il.boost_factor,
                    il.confidence,
                    d.citation,
                    d.title,
                    d.court,
                    d.year,
                    d.full_text
                FROM interpretation_links il
                JOIN documents d ON il.case_id = d.id
                WHERE il.statute_id = ANY(:statute_ids)
                  AND il.verified = TRUE
                ORDER BY il.boost_factor DESC, il.confidence DESC
            """),
            {"statute_ids": statute_ids}
        )
        
        # Organize by statute_id
        interpretation_map = {}
        for row in result:
            statute_id = row.statute_id
            if statute_id not in interpretation_map:
                interpretation_map[statute_id] = []
            
            interpretation_map[statute_id].append({
                'case_id': row.case_id,
                'interpretation_type': row.interpretation_type,
                'authority': row.authority,
                'boost_factor': row.boost_factor,
                'confidence': row.confidence,
                'citation': row.citation,
                'title': row.title,
                'court': row.court,
                'year': row.year,
                'content': row.full_text
            })
        
        return interpretation_map
    
    def _apply_interpretation_boost(
        self,
        candidates: List[Dict],
        interpretation_map: Dict[str, List[Dict]]
    ) -> List[Dict]:
        """
        Apply interpretation boost to candidates.
        
        Strategy:
        1. For each statute in candidates, get its interpretive cases
        2. Check if interpretive cases are already in candidates
        3. If yes: boost their score
        4. If no: add them with synthetic score (original * penalty)
        """
        # Create lookup of existing case IDs
        existing_ids = {doc['id'] for doc in candidates}
        
        # Track which interpretive cases we've added/boosted
        boosted_candidates = list(candidates)  # Copy
        added_case_ids = set()
        
        for statute_id, interpretive_cases in interpretation_map.items():
            # Find the statute in candidates (for synthetic score calculation)
            statute_score = next(
                (doc['score'] for doc in candidates if doc['id'] == statute_id),
                0.5  # Default if not found
            )
            
            # Limit to max N interpretive cases per statute
            for interp_case in interpretive_cases[:self.config.max_interpretive_per_statute]:
                case_id = interp_case['case_id']
                
                if case_id in existing_ids:
                    # Case already in candidates → boost its score
                    for doc in boosted_candidates:
                        if doc['id'] == case_id:
                            doc['score'] *= interp_case['boost_factor']
                            doc['is_interpretive'] = True
                            doc['interprets_statute'] = statute_id
                            doc['interpretation_type'] = interp_case['interpretation_type']
                            logger.debug(
                                f"Boosted existing case {doc['citation']} by "
                                f"{interp_case['boost_factor']}x (interprets {statute_id})"
                            )
                            break
                
                elif case_id not in added_case_ids:
                    # Case not in candidates → add it with synthetic score
                    synthetic_score = statute_score * self.config.synthetic_penalty * interp_case['boost_factor']
                    
                    boosted_candidates.append({
                        'id': case_id,
                        'doc_type': 'case',
                        'title': interp_case['title'] or '',
                        'content': interp_case['content'],
                        'citation': interp_case['citation'],
                        'court': interp_case['court'],
                        'year': interp_case['year'],
                        'section_number': '',
                        'para_no': None,
                        'score': synthetic_score,
                        'retrieval_method': 'interpretation_link',
                        'is_interpretive': True,
                        'interprets_statute': statute_id,
                        'interpretation_type': interp_case['interpretation_type']
                    })
                    
                    added_case_ids.add(case_id)
                    logger.debug(
                        f"Added interpretive case {interp_case['citation']} "
                        f"(score={synthetic_score:.3f}, interprets {statute_id})"
                    )
        
        return boosted_candidates
    
    def _diversify_and_rerank(self, candidates: List[Dict], k: int) -> List[Dict]:
        """
        Diversify results and return top-k.
        
        Ensures:
        - Max N interpretive cases per statute
        - Balance between statutes and cases
        - Highest scored documents first
        """
        # Sort by score (descending)
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Track how many interpretive cases per statute
        interp_count_per_statute = {}
        
        final_results = []
        for doc in candidates:
            # Check if this is an interpretive case
            if doc['is_interpretive']:
                statute_id = doc['interprets_statute']
                count = interp_count_per_statute.get(statute_id, 0)
                
                # Skip if we already have max interpretive cases for this statute
                if count >= self.config.max_interpretive_per_statute:
                    logger.debug(
                        f"Skipping {doc['citation']} - already have {count} "
                        f"interpretive cases for {statute_id}"
                    )
                    continue
                
                interp_count_per_statute[statute_id] = count + 1
            
            final_results.append(doc)
            
            # Stop when we have k results
            if len(final_results) >= k:
                break
        
        return final_results


# Convenience function
def create_interpretation_aware_retriever(
    db_url: str,
    faiss_index_path: str,
    doc_id_mapping_path: str,
    openai_api_key: str,
    config: RetrievalConfig = None
) -> InterpretationAwareRetriever:
    """
    Factory function to create retriever with all dependencies.
    
    Args:
        db_url: PostgreSQL connection string
        faiss_index_path: Path to FAISS index file
        doc_id_mapping_path: Path to doc_id_mapping.json
        openai_api_key: OpenAI API key
        config: Optional retrieval configuration
    
    Returns:
        Configured InterpretationAwareRetriever
    """
    import json
    
    # Database
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # FAISS
    faiss_index = faiss.read_index(faiss_index_path)
    
    # Mapping
    with open(doc_id_mapping_path, 'r') as f:
        doc_id_mapping = json.load(f)
    
    # OpenAI
    client = OpenAI(api_key=openai_api_key)
    
    return InterpretationAwareRetriever(
        db_session=db,
        faiss_index=faiss_index,
        doc_id_mapping=doc_id_mapping,
        openai_client=client,
        config=config
    )
