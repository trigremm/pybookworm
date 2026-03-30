# pybookworm/cleaner.py
import glob
import os


def clean_chapter(filepath: str) -> bool:
    """Remove site metadata header from a chapter file.

    Header pattern (from ranobehub.org):
        Line 1: chapter title (from scraper)
        Line 2: [optional book title]
        Line N-1: number (comment count)
        Line N: rating like "9.3 (37)"
        Line N+1: chapter title repeated (from page content)
        <actual text>

    Strategy: find the second occurrence of line 1 and drop everything before it.
    """
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    if len(lines) < 3:
        return False

    first_line = lines[0].strip()

    # Find the second occurrence of the first line
    for i in range(1, min(len(lines), 8)):
        if lines[i].strip() == first_line:
            # Keep everything from this duplicate onward
            cleaned = lines[i:]
            break
    else:
        return False

    if cleaned == lines:
        return False

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(cleaned)

    return True


def clean_chapters(directory: str) -> tuple[int, int]:
    """Clean all chapter files in a directory. Returns (cleaned, skipped)."""
    pattern = os.path.join(directory, "*_chapter.txt")
    files = sorted(glob.glob(pattern))

    if not files:
        print(f"No chapter files found in {directory}")
        return 0, 0

    cleaned = 0
    skipped = 0
    for filepath in files:
        if clean_chapter(filepath):
            cleaned += 1
        else:
            skipped += 1

    return cleaned, skipped
