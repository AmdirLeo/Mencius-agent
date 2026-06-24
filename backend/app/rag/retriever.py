from typing import List, Dict
import hashlib
import logging
import numpy as np
import faiss
import json
import os
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

    def build_from_documents(self, documents: List[Dict[str, any]], batch_size: int = 100):
        """Create a new in-memory FAISS index from documents."""
        self.init_collection()
        self.add_documents(documents, batch_size=batch_size)

    def build_from_documents_cached(
        self,
        documents: List[Dict[str, any]],
        embedding_cache_path: str,
        batch_size: int = 100,
    ):
        """
        Create a FAISS index while reusing cached embeddings by document text hash.

        If one source file is added or changed, unchanged chunks reuse their old
        vectors and only new/changed chunks are embedded again.
        """
        if not documents:
            self.init_collection()
            return

        cache = self._load_embedding_cache(embedding_cache_path)
        ordered_hashes = [self._hash_text(doc["text"]) for doc in documents]
        unique_missing_hashes = []
        unique_missing_texts = []
        seen_missing = set()

        for doc_hash, doc in zip(ordered_hashes, documents):
            if doc_hash in cache or doc_hash in seen_missing:
                continue
            seen_missing.add(doc_hash)
            unique_missing_hashes.append(doc_hash)
            unique_missing_texts.append(doc["text"])

        if unique_missing_texts:
            logger.info(
                f"Embedding {len(unique_missing_texts)} new/changed documents "
                f"({len(documents)} total documents)"
            )
            new_embeddings = embedder.embed_batch(unique_missing_texts, batch_size=batch_size)
            new_embeddings = new_embeddings / np.linalg.norm(new_embeddings, axis=1, keepdims=True)
            for doc_hash, embedding in zip(unique_missing_hashes, new_embeddings):
                cache[doc_hash] = embedding.astype(np.float32)
        else:
            logger.info(f"Reusing cached embeddings for all {len(documents)} documents")

        embeddings = np.vstack([cache[doc_hash] for doc_hash in ordered_hashes]).astype(np.float32)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index.add(embeddings)
        self.documents = documents

        self._save_embedding_cache(embedding_cache_path, ordered_hashes, cache)
        logger.info(f"Built FAISS index with {len(documents)} documents")

    def save(self, index_path: str, documents_path: str):
        """Persist FAISS index and document metadata to disk."""
        if self.index is None:
            raise RuntimeError("Index not initialized")

        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        faiss.write_index(self.index, index_path)
        with open(documents_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, ensure_ascii=False)
        logger.info(f"Saved FAISS index to {index_path} and documents to {documents_path}")

    def load(self, index_path: str, documents_path: str):
        """Load persisted FAISS index and document metadata from disk."""
        self.index = faiss.read_index(index_path)
        with open(documents_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        if self.index.d != self.embedding_dim:
            raise RuntimeError(
                f"Index dimension mismatch: index={self.index.d}, model={self.embedding_dim}"
            )
        if self.index.ntotal != len(self.documents):
            raise RuntimeError(
                f"Index/document count mismatch: index={self.index.ntotal}, docs={len(self.documents)}"
            )

        logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors from {index_path}")

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _load_embedding_cache(self, embedding_cache_path: str) -> Dict[str, np.ndarray]:
        if not os.path.exists(embedding_cache_path):
            return {}

        try:
            data = np.load(embedding_cache_path, allow_pickle=False)
            hashes = data["hashes"].astype(str)
            embeddings = data["embeddings"].astype(np.float32)
            if embeddings.shape[1] != self.embedding_dim:
                logger.warning("Ignoring embedding cache due to dimension mismatch")
                return {}
            return {
                doc_hash: embedding
                for doc_hash, embedding in zip(hashes, embeddings)
            }
        except Exception as e:
            logger.warning(f"Ignoring invalid embedding cache: {str(e)}")
            return {}

    def _save_embedding_cache(
        self,
        embedding_cache_path: str,
        ordered_hashes: List[str],
        cache: Dict[str, np.ndarray],
    ):
        os.makedirs(os.path.dirname(embedding_cache_path), exist_ok=True)

        unique_hashes = []
        seen = set()
        for doc_hash in ordered_hashes:
            if doc_hash in seen:
                continue
            seen.add(doc_hash)
            unique_hashes.append(doc_hash)

        embeddings = np.vstack([cache[doc_hash] for doc_hash in unique_hashes]).astype(np.float32)
        np.savez(
            embedding_cache_path,
            hashes=np.array(unique_hashes),
            embeddings=embeddings,
        )
        logger.info(f"Saved embedding cache with {len(unique_hashes)} vectors to {embedding_cache_path}")
    
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
