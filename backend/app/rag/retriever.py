from typing import List, Dict
import logging
import numpy as np
import faiss
from app.data.embedder import embedder

logger = logging.getLogger(__name__)

class RAGRetriever:
    """Retrieval-Augmented Generation retriever using FAISS (in-memory vector index)"""
    
    def __init__(self):
        """Initialize FAISS-based retriever (in-memory, no external service needed)"""
        self.index = None
        self.documents = []
        self.embedding_dim = embedder.embedding_dim
        logger.info(f"FAISS Retriever initialized (embedding_dim={self.embedding_dim})")
    
    def init_collection(self):
        """Initialize FAISS index (creates empty index in memory)"""
        try:
            # Create FAISS index with cosine similarity
            # Using IndexFlatIP for cosine similarity (normalized vectors)
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.documents = []
            logger.info(f"Initialized FAISS index in memory (dimension={self.embedding_dim})")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Dict[str, any]], batch_size: int = 100):
        """
        Add documents to the FAISS index
        
        Args:
            documents: List of dicts with 'text' and 'metadata' keys
            batch_size: Batch size for embedding processing
        """
        try:
            if self.index is None:
                raise RuntimeError("Index not initialized. Call init_collection() first.")
            
            # Extract texts for embedding
            texts = [doc['text'] for doc in documents]
            logger.info(f"Embedding {len(texts)} documents...")
            
            # Get embeddings - normalize for cosine similarity
            embeddings = embedder.embed_batch(texts, batch_size=batch_size)
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add embeddings to FAISS index
            self.index.add(embeddings.astype(np.float32))
            
            # Store document metadata
            self.documents.extend(documents)
            
            logger.info(f"Successfully added {len(documents)} documents to FAISS index")
        except Exception as e:
            logger.error(f"Failed to add documents to FAISS: {str(e)}")
            raise
    
    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieve relevant passages from Mencius texts based on query
        
        Args:
            query: User question/query
            top_k: Number of top results to return
        
        Returns:
            List of relevant documents with scores
        """
        try:
            if self.index is None or len(self.documents) == 0:
                logger.warning("No documents in index. Returning empty results.")
                return []
            
            # Generate query embedding and normalize
            query_embedding = embedder.embed(query)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
            
            # Search FAISS index
            distances, indices = self.index.search(query_embedding, top_k)
            
            # Format results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.documents):
                    doc = self.documents[idx]
                    results.append({
                        'text': doc.get('text', ''),
                        'metadata': doc.get('metadata', {}),
                        'score': float(distance)  # Higher is more similar
                    })
            
            logger.info(f"Retrieved {len(results)} documents for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {str(e)}")
            raise
    
    def get_collection_info(self) -> Dict:
        """Get information about the FAISS index"""
        try:
            if self.index is None:
                return {
                    'name': 'faiss_index',
                    'vectors_count': 0,
                    'vector_size': self.embedding_dim
                }
            return {
                'name': 'faiss_index',
                'vectors_count': self.index.ntotal,
                'vector_size': self.embedding_dim,
                'backend': 'FAISS (In-Memory)'
            }
        except Exception as e:
            logger.error(f"Failed to get index info: {str(e)}")
            return {}

retriever = RAGRetriever()
