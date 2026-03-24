# pybookworm/scraper.py
import json
import os
import time
from urllib.parse import urljoin
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def get_config_dir() -> str:
    config = os.path.join(os.path.expanduser("~"), ".config", "pybookworm")
    os.makedirs(config, exist_ok=True)
    return config


def get_storage_file() -> str:
    return os.path.join(get_config_dir(), "auth_storage.json")


def get_resume_file(output_dir: str) -> str:
    """Legacy resume file — kept for backwards compatibility."""
    return os.path.join(output_dir, ".current_url.txt")


def extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def fetch_html_requests(url: str) -> str:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def do_login(url: str) -> None:
    domain = extract_domain(url)
    storage_file = get_storage_file()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--no-sandbox"])
        context = browser.new_context()
        page = context.new_page()
        page.goto(domain, timeout=60000)
        print("Browser opened. Please log in manually.")
        print("Press ENTER here when you are done...")
        input()
        context.storage_state(path=storage_file)
        print(f"Session saved to {storage_file}")
        browser.close()


def fetch_html_playwright(url: str) -> str:
    storage_file = get_storage_file()
    storage = storage_file if os.path.exists(storage_file) else None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(storage_state=storage) if storage else browser.new_context()
        page = context.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_timeout(1000)
        html = page.content()
        browser.close()
        return html


def extract_title(soup: BeautifulSoup) -> str | None:
    title = soup.find("h1")
    return title.get_text(strip=True) if title else None


def extract_content(soup: BeautifulSoup) -> str | None:
    # ifreedom.su
    container = soup.find("div", class_="chapter-content")
    if container:
        text = container.get_text(separator="\n").strip()
        cleaned = "\n".join(line for line in text.splitlines() if line.strip())
        cleaned = "\n".join(line for line in cleaned.splitlines() if line.strip() != "РЕКЛАМА")
        return cleaned or None

    # data-container sites
    container = soup.find("div", {"data-container": True})
    if container:
        text = container.get_text(separator="\n").strip()
    else:
        paragraphs = soup.select("main[data-reader-content] .node-doc p")
        if not paragraphs:
            return None
        text = "\n".join(p.get_text(strip=True) for p in paragraphs)

    cleaned = "\n".join(line for line in text.splitlines() if line.strip())
    return cleaned or None


def extract_next_url(soup: BeautifulSoup, domain: str) -> str | None:
    # ifreedom.su: link with text "Следующая"
    next_link = soup.find("a", string=lambda t: t and "Следующая" in t)
    if next_link and next_link.has_attr("href"):
        return urljoin(domain, next_link["href"])

    next_link = soup.find("a", {"data-next-chapter-link": True})
    if next_link and next_link.has_attr("href"):
        return urljoin(domain, next_link["href"])

    candidates = soup.select("a.ty_a0.ty_cm[href*='/read/']")
    if candidates:
        return urljoin(domain, candidates[-1]["href"])

    return None


def parse_html(html: str, domain: str) -> tuple[str | None, str | None, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    title = extract_title(soup)
    content = extract_content(soup)
    next_url = extract_next_url(soup, domain)
    return title, content, next_url


def get_page_data(url: str, domain: str, engine: str):
    html = fetch_html_requests(url) if engine == "requests" else fetch_html_playwright(url)
    return parse_html(html, domain)


def get_config_file(output_dir: str) -> str:
    return os.path.join(output_dir, "bookworm_config.json")


def save_book_config(output_dir: str, start_url: str, output: str, engine: str,
                     split_chapters: bool, current_url: str | None = None) -> None:
    config_path = get_config_file(output_dir)
    # Load existing config to preserve fields not being updated
    cfg = {}
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
    cfg.update({
        "start_url": start_url,
        "output": output,
        "engine": engine,
        "split_chapters": split_chapters,
    })
    if current_url is not None:
        cfg["current_url"] = current_url
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def load_book_config(config_path: str) -> dict:
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def count_existing_chapters(output_dir: str, stem: str) -> int:
    """Count existing chapter files to determine next chapter number."""
    import glob

    pattern = os.path.join(output_dir, f"{stem}_*_chapter.txt")
    return len(glob.glob(pattern))


def scrape_book(start_url: str, output: str, engine: str, split_chapters: bool = False) -> None:
    output_dir = os.path.dirname(output) or "."
    os.makedirs(output_dir, exist_ok=True)

    stem = os.path.splitext(os.path.basename(output))[0]
    chapter_num = count_existing_chapters(output_dir, stem) + 1

    current_url = start_url
    domain = extract_domain(current_url)

    # Check config for resume URL
    config_path = get_config_file(output_dir)
    if os.path.exists(config_path):
        cfg = load_book_config(config_path)
        resume_url = cfg.get("current_url", "")
        if resume_url:
            print(f"Resuming from {resume_url}")
            current_url = resume_url
    else:
        # Also check legacy .current_url.txt
        resume_file = get_resume_file(output_dir)
        try:
            with open(resume_file, encoding="utf-8") as f:
                tmp_url = f.readline().strip()
                if tmp_url:
                    print(f"Legacy resume file found, continuing from {tmp_url}")
                    current_url = tmp_url
        except FileNotFoundError:
            pass

    # Save initial config
    save_book_config(output_dir, start_url, output, engine, split_chapters, current_url)

    while current_url:
        time.sleep(3)
        print(f"[{chapter_num}] Processing {current_url}...")

        try:
            if engine == "auto":
                title, content, next_url = get_page_data(current_url, domain, "requests")
                if not title or not content:
                    title, content, next_url = get_page_data(current_url, domain, "playwright")
            else:
                title, content, next_url = get_page_data(current_url, domain, engine)

            if not title or not content:
                raise RuntimeError("Failed to extract chapter content")

            # Always append to combined file
            with open(output, "a", encoding="utf-8") as f:
                f.write("\n" + "-" * 20 + "\n")
                f.write(f"{title}\n\n")
                f.write(content)

            # Save individual chapter file for TTS
            if split_chapters:
                chapter_file = os.path.join(output_dir, f"{stem}_{chapter_num:05d}_chapter.txt")
                with open(chapter_file, "w", encoding="utf-8") as f:
                    f.write(f"{title}\n")
                    f.write(content)
                print(f"  Saved {os.path.basename(chapter_file)}")

            chapter_num += 1
            current_url = next_url

            # Update config with current progress
            save_book_config(output_dir, start_url, output, engine, split_chapters, next_url or "")

        except Exception as exc:
            print(f"Error while processing {current_url}: {exc}")
            break
