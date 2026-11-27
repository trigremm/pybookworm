# bookworm

Scrape web novels chapter-by-chapter and convert them to EPUB.

- install: `make install` (`pip install -e .`)
- download a book: `bookworm scrape <first_chapter_url> -o output/book/book.txt` (add `--split-chapters` for one file per chapter, e.g. for TTS)
- resume an interrupted download: `bookworm resume output/book/bookworm_config.json`
- convert to EPUB: `bookworm convert -i output/book/book.txt -o output/book/book.epub -t "Title" -a "Author"`
- `make run` / `make run-resume` / `make clean` / `make format` wrap the same commands; see `AGENTS.md` for details
