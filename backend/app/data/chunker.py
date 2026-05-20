from typing import List, Dict

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
    
    return chunks
