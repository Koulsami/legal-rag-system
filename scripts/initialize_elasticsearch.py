"""
Initialize Elasticsearch index with documents from database
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from dotenv import load_dotenv
import logging

from src.database.connection import get_session
from src.database.models.document import Document

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_index(es: Elasticsearch, index_name: str = "legal_documents"):
    """Create Elasticsearch index with proper mapping"""
    
    mapping = {
        "mappings": {
            "properties": {
                "unit_id": {"type": "keyword"},
                "doc_id": {"type": "keyword"},
                "doc_type": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}}
                },
                "text": {"type": "text"},
                "citation": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}}
                },
                "court": {"type": "keyword"},
                "year": {"type": "integer"},
                "para_no": {"type": "integer"}
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "legal_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "stop"]
                    }
                }
            }
        }
    }
    
    if es.indices.exists(index=index_name):
        logger.warning(f"Deleting existing index: {index_name}")
        es.indices.delete(index=index_name)
    
    es.indices.create(index=index_name, body=mapping)
    logger.info(f"Created index: {index_name}")


def index_documents(
    es: Elasticsearch,
    session,
    index_name: str = "legal_documents",
    batch_size: int = 1000
):
    """Index documents from database into Elasticsearch"""
    
    logger.info("Querying documents from database...")
    documents = session.query(Document).all()
    logger.info(f"Found {len(documents)} documents")
    
    if not documents:
        logger.warning("No documents found in database!")
        return
    
    actions = []
    for doc in documents:
        es_doc = {
            "_index": index_name,
            "_id": doc.id,
            "_source": {
                "unit_id": doc.id,
                "doc_id": doc.id,
                "doc_type": getattr(doc, 'doc_type', 'unknown'),
                "title": getattr(doc, 'title', ''),
                "text": doc.full_text,
                "citation": getattr(doc, 'citation', None),
                "court": getattr(doc, 'court', None),
                "year": getattr(doc, 'year', None),
                "para_no": getattr(doc, 'para_no', None)
            }
        }
        actions.append(es_doc)
        
        if len(actions) >= batch_size:
            success, failed = bulk(es, actions, raise_on_error=False)
            logger.info(f"Indexed {success} documents, {len(failed)} failed")
            actions = []
    
    if actions:
        success, failed = bulk(es, actions, raise_on_error=False)
        logger.info(f"Indexed {success} documents, {len(failed)} failed")
    
    es.indices.refresh(index=index_name)
    
    count = es.count(index=index_name)['count']
    logger.info(f"✅ Total documents in index: {count}")


def main():
    """Main initialization function"""
    
    es_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    
    logger.info(f"Connecting to Elasticsearch: {es_url}")
    es = Elasticsearch([es_url])
    
    if not es.ping():
        logger.error("Cannot connect to Elasticsearch!")
        logger.error("Make sure Elasticsearch is running:")
        logger.error("  docker run -d -p 9200:9200 -e 'discovery.type=single-node' elasticsearch:8.11.0")
        sys.exit(1)
    
    logger.info("✓ Connected to Elasticsearch")
    
    session = get_session()
    
    logger.info("Creating Elasticsearch index...")
    create_index(es, index_name="legal_documents")
    
    logger.info("Indexing documents...")
    index_documents(es, session, index_name="legal_documents")
    
    logger.info("🚀 Elasticsearch initialization complete!")


if __name__ == "__main__":
    main()
