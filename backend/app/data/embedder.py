from sentence_transformers import SentenceTransformer
from app.config.settings import settings
import logging
import numpy as np
from typing import List, Union

logger = logging.getLogger(__name__)

class TextEmbedder:
    def __init__(self):
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        try:
            self.model = SentenceTransformer(settings.embedding_model)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded successfully (dim={self.embedding_dim})")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise
    
    def embed(self, text: str) -> np.ndarray:
        """
        Convert text to embedding vector
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector (numpy array)
        """
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Failed to embed text: {str(e)}")
            raise
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Convert multiple texts to embedding vectors
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
        
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = self.model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
            logger.info(f"Embedded {len(texts)} texts successfully")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to embed batch: {str(e)}")
            raise

embedder = TextEmbedder()
