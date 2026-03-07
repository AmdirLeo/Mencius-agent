import logging
import os
from typing import List, Dict

logger = logging.getLogger(__name__)

def load_mencius_text(file_path: str) -> str:
    """
    Load Mencius translation and annotation from txt file
    
    Args:
        file_path: Path to the mencius txt file
    
    Returns:
        Raw text content
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Successfully loaded {len(content)} characters from {file_path}")
        return content
    except Exception as e:
        logger.error(f"Failed to load text from {file_path}: {str(e)}")
        raise Exception(f"Failed to load text: {str(e)}")

def parse_mencius_sections(text: str) -> List[Dict[str, str]]:
    """
    Parse mencius text into sections with metadata
    
    Extracts meaningful sections based on【原文】【注释】structure
    
    Args:
        text: Raw mencius text
    
    Returns:
        List of sections with content and metadata
    """
    sections = []
    current_section = {
        "title": "",
        "content": "",
        "type": "intro"
    }
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        # Detect section titles (篇章名)
        if line and not line.startswith('【') and len(line) < 20:
            if current_section["content"].strip():
                sections.append(current_section.copy())
            current_section = {
                "title": line,
                "content": "",
                "type": "section"
            }
        # Detect original text marker
        elif line.startswith('【原文】'):
            if current_section["content"].strip():
                sections.append(current_section.copy())
            current_section = {
                "title": current_section.get("title", ""),
                "content": line,
                "type": "original"
            }
        # Detect annotation marker
        elif line.startswith('【注释】'):
            if current_section["content"].strip():
                sections.append(current_section.copy())
            current_section = {
                "title": current_section.get("title", ""),
                "content": line,
                "type": "annotation"
            }
        else:
            current_section["content"] += line + "\n"
    
    if current_section["content"].strip():
        sections.append(current_section)
    
    logger.info(f"Parsed {len(sections)} sections from text")
    return sections
