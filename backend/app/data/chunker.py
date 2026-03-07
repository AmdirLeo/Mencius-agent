import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def chunk_text(text: str, chunk_size: int = 300, overlap: int = 50) -> list:
    """
    Split text into overlapping chunks
    
    Args:
        text: Input text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Overlap between chunks in characters
    
    Returns:
        List of text chunks
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    
    chunks = []
    step = chunk_size - overlap
    
    for i in range(0, len(text), step):
        chunk = text[i:i + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
    
    logger.info(f"Chunked text into {len(chunks)} parts (size={chunk_size}, overlap={overlap})")
    return chunks

def chunk_by_sentences(text: str, target_chars: int = 300) -> List[Dict[str, str]]:
    """
    Split text by sentence boundaries to preserve meaning
    
    Better than character-based chunking for Chinese text
    
    Args:
        text: Input text
        target_chars: Target characters per chunk
    
    Returns:
        List of meaningful chunks with metadata
    """
    # Chinese sentence delimiters
    delimiters = ['。', '！', '？']
    
    chunks = []
    current_chunk = ""
    
    # Split by Chinese punctuation
    sentences = []
    temp_sent = ""
    
    for char in text:
        temp_sent += char
        if char in delimiters:
            sentences.append(temp_sent)
            temp_sent = ""
    
    if temp_sent:
        sentences.append(temp_sent)
    
    # Group sentences into chunks
    for sent in sentences:
        if len(current_chunk) + len(sent) <= target_chars:
            current_chunk += sent
        else:
            if current_chunk.strip():
                chunks.append({
                    "text": current_chunk,
                    "length": len(current_chunk)
                })
            current_chunk = sent
    
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk,
            "length": len(current_chunk)
        })
    
    logger.info(f"Created {len(chunks)} sentence-based chunks")
    return chunks
