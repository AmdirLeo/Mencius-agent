#!/usr/bin/env python
"""Build structured Mencius chapters from the raw txt source."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
RAW_FILE = PROJECT_ROOT / "data" / "raw" / "孟子译注.txt"
PROCESSED_FILE = PROJECT_ROOT / "data" / "processed" / "mencius_chapters.json"

sys.path.insert(0, str(BACKEND_ROOT))

from app.data.loader import (  # noqa: E402
    load_mencius_text,
    parse_mencius_chapters,
    save_processed_chapters,
)


def main() -> None:
    text = load_mencius_text(str(RAW_FILE))
    chapters = parse_mencius_chapters(text)
    save_processed_chapters(chapters, str(PROCESSED_FILE))

    tagged_count = sum(1 for chapter in chapters if chapter.get("tags"))
    print(f"processed_file={PROCESSED_FILE}")
    print(f"chapters={len(chapters)}")
    print(f"tagged_chapters={tagged_count}")


if __name__ == "__main__":
    main()
