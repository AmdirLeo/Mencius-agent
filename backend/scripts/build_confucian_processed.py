#!/usr/bin/env python
"""Build structured Confucian chapters from the raw txt sources."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_FILE = PROJECT_ROOT / "data" / "processed" / "confucian_chapters.json"

sys.path.insert(0, str(BACKEND_ROOT))

from app.data.loader import (  # noqa: E402
    load_or_parse_confucian_chapters,
    save_processed_chapters,
)


def main() -> None:
    chapters = load_or_parse_confucian_chapters(str(RAW_DIR))
    save_processed_chapters(chapters, str(PROCESSED_FILE))

    tagged_count = sum(1 for chapter in chapters if chapter.get("tags"))
    sources = {}
    for chapter in chapters:
        source_title = chapter.get("source_title", "unknown")
        sources[source_title] = sources.get(source_title, 0) + 1

    print(f"processed_file={PROCESSED_FILE}")
    print(f"chapters={len(chapters)}")
    print(f"tagged_chapters={tagged_count}")
    print(f"sources={sources}")


if __name__ == "__main__":
    main()
