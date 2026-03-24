# pybookworm/cli.py
import argparse
import sys


def cli() -> int:
    parser = argparse.ArgumentParser(prog="bookworm", description="Scrape web novels and convert to EPUB")
    subparsers = parser.add_subparsers(dest="command")

    # scrape
    sp_scrape = subparsers.add_parser("scrape", help="Scrape a book from a URL")
    sp_scrape.add_argument("url", help="URL of the first chapter")
    sp_scrape.add_argument("-o", "--output", required=True, help="Output file path (e.g. ~/books/novel.txt)")
    sp_scrape.add_argument(
        "-e",
        "--engine",
        choices=("auto", "requests", "playwright"),
        default="auto",
        help="HTML fetch engine (default: auto)",
    )
    sp_scrape.add_argument(
        "--split-chapters",
        action="store_true",
        help="Save each chapter as a separate file (for TTS)",
    )

    # login
    sp_login = subparsers.add_parser("login", help="Open browser for manual login, save session")
    sp_login.add_argument("url", help="URL of the site to log in to")

    # resume
    sp_resume = subparsers.add_parser("resume", help="Resume scraping from saved config")
    sp_resume.add_argument("config", help="Path to bookworm_config.json")

    # convert
    sp_convert = subparsers.add_parser("convert", help="Convert scraped TXT to EPUB")
    sp_convert.add_argument("-i", "--input", required=True, help="Input TXT file")
    sp_convert.add_argument("-o", "--output", required=True, help="Output EPUB file")
    sp_convert.add_argument("-t", "--title", default="Untitled", help="Book title")
    sp_convert.add_argument("-a", "--author", default="Unknown", help="Book author")
    sp_convert.add_argument("-l", "--language", default="en", help="Book language code")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "scrape":
        from .scraper import scrape_book

        scrape_book(args.url, args.output, args.engine, args.split_chapters)

    elif args.command == "resume":
        from .scraper import load_book_config, scrape_book

        cfg = load_book_config(args.config)
        print(f"Resuming with config: {args.config}")
        scrape_book(cfg["start_url"], cfg["output"], cfg["engine"], cfg.get("split_chapters", False))

    elif args.command == "login":
        from .scraper import do_login

        do_login(args.url)

    elif args.command == "convert":
        from .converter import txt_to_epub

        txt_to_epub(args.input, args.output, args.title, args.author, args.language)

    return 0


def main():
    sys.exit(cli())
