"""
Initialize FAISS index with document embeddings
Fixed dimension handling
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv
import logging
from tqdm import tqdm
import time

from src.database.connection import get_session
from src.database.models.document import Document

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def truncate_text(text: str, max_chars: int = 20000) -> str:
    """Truncate text to max characters"""
    if len(text) > max_chars:
        return text[:max_chars]
    return text


def generate_embeddings(
    texts: list,
    client: OpenAI,
    model: str = "text-embedding-3-large",
    batch_size: int = 20,
    dimension: int = 3072
) -> np.ndarray:
    """Generate embeddings with proper dimension handling"""
    embeddings = []
    
    logger.info(f"Generating embeddings for {len(texts)} texts...")
    
    truncated_texts = [truncate_text(text) for text in texts]
    
    for i in tqdm(range(0, len(truncated_texts), batch_size)):
        batch = truncated_texts[i:i + batch_size]
        
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                response = client.embeddings.create(
                    model=model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                break
            
            except Exception as e:
                error_msg = str(e)
                retry_count += 1
                
                if 'rate_limit' in error_msg.lower() or '429' in error_msg:
                    wait_time = min(60, 2 ** retry_count)
                    logger.warning(f"Rate limit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                elif 'maximum context length' in error_msg or '400' in error_msg:
                    logger.warning(f"Batch {i} too long, truncating further...")
                    batch = [text[:10000] for text in batch]
                    try:
                        response = client.embeddings.create(model=model, input=batch)
                        batch_embeddings = [item.embedding for item in response.data]
                        embeddings.extend(batch_embeddings)
                        break
                    except:
                        logger.error(f"Failed even with aggressive truncation: batch {i}")
                        # Add zero vectors with correct shape
                        embeddings.extend([[0.0] * dimension for _ in range(len(batch))])
                        break
                else:
                    logger.error(f"Error for batch {i}: {error_msg}")
                    embeddings.extend([[0.0] * dimension for _ in range(len(batch))])
                    break
        
        if retry_count >= max_retries:
            logger.error(f"Failed after {max_retries} retries for batch {i}")
            embeddings.extend([[0.0] * dimension for _ in range(len(batch))])
        
        time.sleep(0.5)
    
    # Convert to proper numpy array (N, dimension)
    embeddings_array = np.array(embeddings, dtype=np.float32)
    
    # Validate shape
    assert embeddings_array.shape == (len(texts), dimension), \
        f"Shape mismatch: got {embeddings_array.shape}, expected ({len(texts)}, {dimension})"
    
    return embeddings_array


def create_faiss_index(
    session,
    client: OpenAI,
    output_path: str = "./data/faiss_index.bin",
    embedding_model: str = "text-embedding-3-large",
    dimension: int = 3072
):
    """Create FAISS index from database documents"""
    
    logger.info("Querying documents from database...")
    documents = session.query(Document).all()
    logger.info(f"Found {len(documents)} documents")
    
    if not documents:
        logger.warning("Creating empty FAISS index...")
        index = faiss.IndexFlatL2(dimension)
        os.makedirs(Path(output_path).parent, exist_ok=True)
        faiss.write_index(index, output_path)
        return
    
    texts = []
    doc_ids = []
    
    for doc in documents:
        title = getattr(doc, 'title', '')
        combined_text = f"{title} {doc.full_text}"
        texts.append(combined_text)
        doc_ids.append(doc.id)
    
    logger.info("Generating embeddings (aggressive truncation for long docs)...")
    
    embeddings = generate_embeddings(
        texts,
        client,
        model=embedding_model,
        batch_size=20,
        dimension=dimension
    )
    
    logger.info(f"Generated embeddings with shape: {embeddings.shape}")
    
    # Check for failed embeddings
    zero_count = np.sum(np.all(embeddings == 0, axis=1))
    if zero_count > 0:
        logger.warning(f"⚠️  {zero_count}/{len(embeddings)} documents failed ({zero_count/len(embeddings)*100:.1f}%)")
    else:
        logger.info("✅ All embeddings generated successfully!")
    
    logger.info("Creating FAISS index...")
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    logger.info(f"✅ FAISS index created with {index.ntotal} vectors")
    
    os.makedirs(Path(output_path).parent, exist_ok=True)
    faiss.write_index(index, output_path)
    logger.info(f"✅ FAISS index saved to {output_path}")
    
    mapping_path = output_path.replace('.bin', '_mapping.json')
    import json
    with open(mapping_path, 'w') as f:
        json.dump({
            'doc_ids': doc_ids,
            'total_vectors': index.ntotal,
            'dimension': dimension,
            'model': embedding_model,
            'failed_embeddings': int(zero_count),
            'success_rate': f"{(len(embeddings) - zero_count) / len(embeddings) * 100:.1f}%"
        }, f, indent=2)
    
    logger.info(f"✅ Mapping saved to {mapping_path}")


def main():
    """Main initialization function"""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY not set!")
        sys.exit(1)
    
    logger.info("✓ OpenAI API key found")
    
    client = OpenAI(api_key=api_key)
    session = get_session()
    
    output_path = os.getenv('FAISS_INDEX_PATH', './data/faiss_index.bin')
    embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-large')
    
    logger.info("⚠️  Long documents will be truncated to ~20,000 characters")
    
    create_faiss_index(
        session=session,
        client=client,
        output_path=output_path,
        embedding_model=embedding_model
    )
    
    logger.info("🚀 FAISS initialization complete!")
    logger.info("Estimated cost: ~$0.05-0.09")


if __name__ == "__main__":
    main()
