# Repository Guidelines

## Project Structure & Module Organization
- `pybookworm/` is the package: `cli.py` (argparse entry point behind the `bookworm` console script), `scraper.py` (chapter scraping with an auto engine: requests, Playwright fallback; login and resume config), `cleaner.py` (strips site metadata headers from chapter files), `converter.py` (TXT → EPUB via `ebooklib`).
- `output/` (gitignored) holds generated files. Resume state is `bookworm_config.json` in the output directory, next to the scraped file. A legacy `.current_url.txt` in that same directory is still read when no config exists, but is no longer written.
- `bookworm login` stores the browser session in `~/.config/pybookworm/auth_storage.json`.
- Supporting files: `pyproject.toml` (dependencies, `bookworm` entry point, ruff config) and `Makefile` (install, run, resume, clean, format).

## Build, Test, and Development Commands
- `make install` (`pip install -e .`) installs the package and its dependencies.
- `bookworm scrape <first_chapter_url> -o output/book/book.txt` runs the scraper (auto engine). Options: `-e auto|requests|playwright` (default `auto`), `--split-chapters` (also writes one `<stem>_NNNNN_chapter.txt` per chapter, for TTS).
- `bookworm resume output/book/bookworm_config.json` continues a scrape from the saved config.
- `bookworm login <url>` opens a visible browser for manual login and saves the session for Playwright.
- `bookworm clean output/book` removes site metadata headers from `*_chapter.txt` files.
- `bookworm convert -i output/book/book.txt -o output/book/book.epub [-t title] [-a author] [-l en]` builds an EPUB.
- Makefile wrappers: `make run URL=... OUTPUT=... [ENGINE=auto] [SPLIT=1]`, `make run-resume CONFIG=...`, `make clean OUTPUT=...`.
- `make format` (alias `make f`) runs `ruff check --fix .` and `ruff format .`.

## Coding Style & Naming Conventions
- Python is linted and formatted with `ruff` (config in `pyproject.toml`: line length 120, single-line imports); keep code compatible with it.
- Use 4-space indentation and snake_case for functions and variables.
- Output files should live under `output/`, one directory per book: the combined file passed to `-o`, plus `<stem>_00001_chapter.txt`-style chapter files and `bookworm_config.json` beside it.

## Testing Guidelines
- There is no automated test suite yet. If you add tests, place them in a `tests/` directory and name files `test_*.py`.
- Prefer small, deterministic tests that do not hit external sites unless explicitly marked as integration tests.

## Commit & Pull Request Guidelines
- Keep commit subjects concise and imperative (e.g. "Add clean subcommand to strip site metadata from chapter files").
- PRs should include: purpose, how to run the command, and any new dependencies or output files produced.
- If behavior changes the scraping flow, include example URLs and sample output filenames.

## Configuration & Runtime Notes
- The scraper rewrites `bookworm_config.json` after every chapter with the next URL (`current_url`). Do not delete it mid-run unless you want a fresh start; re-running `bookworm scrape` with the same output path also resumes from it.
- The scraper waits 3 seconds between chapters.
- Playwright runs headless Chromium with `--no-sandbox` (headed for `login`); update cautiously if changing deployment environments.
