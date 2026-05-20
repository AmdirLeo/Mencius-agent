import logging
import json
import os
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

BOOK_RE = re.compile(r"^(?:[一二三四五六七八九十]+、)?(梁惠王[上下]|公孙丑[上下]|滕文公[上下]|离娄[上下]|万章[上下]|告子[上下]|尽心[上下])\s*$")
NEXT_TITLE_RE = re.compile(r"^下一篇\((.+?)\)")

BLOCK_MARKERS = {
    "【原文】": "original",
    "【注释】": "annotation",
    "【注解】": "annotation",
    "【译文】": "translation",
    "【读解】": "commentary",
}

TAG_KEYWORDS = {
    "义利之辨": ["利", "仁义", "何必曰利", "舍生取义", "鱼与熊掌"],
    "性善论": ["性善", "本心", "良知", "良能", "人皆可以为尧舜"],
    "四端之心": ["恻隐", "羞恶", "辞让", "是非", "四端", "不忍人之心"],
    "仁政": ["仁政", "不忍人之政", "养民", "教民"],
    "民本": ["民为贵", "百姓", "民心", "得民", "老百姓"],
    "王道霸道": ["王道", "霸道", "以力", "以德", "得道者多助"],
    "浩然之气": ["浩然", "养气", "大丈夫", "富贵不能淫", "威武不能屈"],
    "反求诸己": ["反求诸己", "求诸己", "自反", "放心"],
    "修身立志": ["养心", "寡欲", "持志", "尚志", "大人"],
    "教育": ["教", "学", "师", "大匠", "规矩"],
    "亲亲伦理": ["孝", "父", "母", "兄", "亲亲"],
}

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

def load_processed_chapters(file_path: str) -> List[Dict[str, str]]:
    """Load structured chapters from a processed JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        chapters = json.load(f)
    logger.info(f"Loaded {len(chapters)} processed chapters from {file_path}")
    return chapters

def save_processed_chapters(chapters: List[Dict[str, str]], file_path: str) -> None:
    """Persist structured chapters for inspection and faster startup."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {len(chapters)} processed chapters to {file_path}")

def load_or_parse_mencius_chapters(raw_file_path: str, processed_file_path: str = "") -> List[Dict[str, str]]:
    """
    Load processed chapters when available; otherwise parse raw txt and
    optionally write the processed JSON cache.
    """
    if processed_file_path and os.path.exists(processed_file_path):
        raw_mtime = os.path.getmtime(raw_file_path)
        processed_mtime = os.path.getmtime(processed_file_path)
        if processed_mtime >= raw_mtime:
            return load_processed_chapters(processed_file_path)

    text = load_mencius_text(raw_file_path)
    chapters = parse_mencius_chapters(text)

    if processed_file_path:
        save_processed_chapters(chapters, processed_file_path)

    return chapters

def _normalize_block(lines: List[str]) -> str:
    """Normalize source lines that are visually wrapped in the raw txt."""
    text = " ".join(line.strip() for line in lines if line.strip())
    text = re.sub(r"\s+", " ", text).strip()
    for marker in BLOCK_MARKERS:
        text = re.sub(rf"^{re.escape(marker)}\s*", "", text)
    return text.strip()

def _detect_block_type(line: str) -> str:
    for marker, block_type in BLOCK_MARKERS.items():
        if line.startswith(marker):
            return block_type
    return ""

def _infer_title(chapter: Dict[str, str], chapter_number: int) -> str:
    text = chapter.get("translation") or chapter.get("original") or ""
    text = re.sub(r"\s+", "", text)
    if text:
        title = re.split(r"[。！？；：，,.!?;:]", text, maxsplit=1)[0]
        if 4 <= len(title) <= 18:
            return title
    return f"第{chapter_number}章"

def _tag_chapter(chapter: Dict[str, str]) -> List[str]:
    haystack = " ".join(
        str(chapter.get(field, ""))
        for field in ("chapter_title", "original", "translation", "commentary")
    )
    tags = []
    for tag, keywords in TAG_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            tags.append(tag)
    return tags

def parse_mencius_chapters(text: str) -> List[Dict[str, str]]:
    """
    Parse the source txt into chapter-level structured records.

    Each chapter keeps original text, annotation, translation, commentary,
    book title, chapter title, and coarse thought tags. This avoids mixing
    translation/commentary into arbitrary short chunks before retrieval.
    """
    chapters = []
    current_book = ""
    pending_title = ""
    current_chapter = None
    current_block = ""
    block_lines: List[str] = []
    book_counts: Dict[str, int] = {}

    def flush_block():
        nonlocal block_lines, current_block, current_chapter
        if current_chapter is not None and current_block:
            current_chapter[current_block] = _normalize_block(block_lines)
        block_lines = []

    def finish_chapter():
        nonlocal current_chapter, current_block, block_lines
        if current_chapter is None:
            return
        flush_block()
        if any(current_chapter.get(field) for field in ("original", "translation", "commentary")):
            if not current_chapter.get("chapter_title"):
                current_chapter["chapter_title"] = _infer_title(
                    current_chapter,
                    current_chapter["chapter_number"]
                )
            current_chapter["tags"] = _tag_chapter(current_chapter)
            chapters.append(current_chapter)
        current_chapter = None
        current_block = ""
        block_lines = []

    lines = text.splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        next_title_match = NEXT_TITLE_RE.match(line)
        if next_title_match:
            pending_title = next_title_match.group(1).strip()
            continue

        book_match = BOOK_RE.match(line)
        if book_match:
            finish_chapter()
            current_book = book_match.group(1)
            continue

        if line.startswith("本篇"):
            finish_chapter()
            pending_title = ""
            continue

        block_type = _detect_block_type(line)
        if block_type:
            if block_type == "original":
                finish_chapter()
                book_counts[current_book] = book_counts.get(current_book, 0) + 1
                current_chapter = {
                    "book": current_book,
                    "chapter_title": pending_title,
                    "chapter_number": book_counts[current_book],
                    "original": "",
                    "annotation": "",
                    "translation": "",
                    "commentary": "",
                    "tags": [],
                }
                pending_title = ""
            elif current_chapter is None:
                book_counts[current_book] = book_counts.get(current_book, 0) + 1
                current_chapter = {
                    "book": current_book,
                    "chapter_title": pending_title,
                    "chapter_number": book_counts[current_book],
                    "original": "",
                    "annotation": "",
                    "translation": "",
                    "commentary": "",
                    "tags": [],
                }
                pending_title = ""

            flush_block()
            current_block = block_type
            block_lines = [line]
            continue

        # The visible title after "下一篇(...)" belongs to the next chapter,
        # even if the previous chapter's commentary block has not closed yet.
        if current_book and pending_title and len(line) <= 40 and not line.startswith("《"):
            pending_title = line
            continue

        if current_block and current_chapter is not None:
            block_lines.append(line)
            continue

        # Some later chapters repeat the human title after the book name.
        # Prefer that visible title over the "下一篇(...)" teaser when present.
        if current_book and not pending_title and len(line) <= 40 and not line.startswith("《"):
            pending_title = line

    finish_chapter()
    logger.info(f"Parsed {len(chapters)} structured chapters from text")
    return chapters
