# pybookworm/converter.py
import html
import re

from ebooklib import epub


def parse_chapters(content: str) -> list[tuple[str, str]]:
    separator = re.compile(r"\n-{20,}\n")
    parts = separator.split(content)

    chapters = []
    for raw_part in parts:
        stripped = raw_part.strip()
        if not stripped:
            continue

        lines = stripped.split("\n", 1)
        title = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        if not body:
            continue

        chapters.append((title or "Chapter", body))

    return chapters


def text_to_html(text: str) -> str:
    text = html.escape(text)
    paragraphs = re.split(r"\n\n+", text)
    html_parts = []
    for paragraph in paragraphs:
        cleaned = paragraph.strip()
        if cleaned:
            cleaned = cleaned.replace("\n", "<br/>")
            html_parts.append(f"<p>{cleaned}</p>")

    if not html_parts:
        text = text.strip()
        if text:
            html_parts.append(f"<p>{text.replace(chr(10), '<br/>')}</p>")
        else:
            html_parts.append("<p>&#160;</p>")

    return "\n".join(html_parts)


def create_epub(chapters: list[tuple[str, str]], title: str, author: str, language: str) -> epub.EpubBook:
    book = epub.EpubBook()
    book.set_title(title)
    book.add_author(author)
    book.set_language(language)

    epub_chapters = []
    for i, (chapter_title, chapter_body) in enumerate(chapters, 1):
        safe_title = html.escape(chapter_title)
        chapter = epub.EpubHtml(
            title=chapter_title,
            file_name=f"chapter_{i:04d}.xhtml",
            lang=language,
        )
        body_content = text_to_html(chapter_body)
        html_content = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"'
            ' "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
            '<html xmlns="http://www.w3.org/1999/xhtml">\n'
            f"<head><title>{safe_title}</title></head>\n"
            "<body>\n"
            f"<h1>{safe_title}</h1>\n"
            f"{body_content}\n"
            "</body>\n"
            "</html>"
        )
        chapter.content = html_content.encode("utf-8")
        book.add_item(chapter)
        epub_chapters.append(chapter)

    book.toc = epub_chapters
    book.spine = ["nav", *epub_chapters]

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    return book


def txt_to_epub(input_path: str, output_path: str, title: str, author: str, language: str) -> None:
    with open(input_path, encoding="utf-8") as f:
        content = f.read()

    chapters = parse_chapters(content)
    if not chapters:
        raise ValueError("No chapters found in input file")

    print(f"Found {len(chapters)} chapters")

    book = create_epub(chapters, title, author, language)
    epub.write_epub(output_path, book)
    print(f"EPUB written to {output_path}")
