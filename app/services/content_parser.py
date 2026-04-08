from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup, Tag

from app.constants import BOILERPLATE_TAGS, URL_FETCH_TIMEOUT
from app.services.nlp import nlp


class ContentFetchError(Exception):
    def __init__(self, message: str, detail: str):
        self.message = message
        self.detail = detail


@dataclass
class ParsedContent:
    first_paragraph: str
    headings: list[tuple[str, str]]
    clean_text: str
    sentences: list[str]
    is_html: bool
    raw: str = field(repr=False)


async def fetch_url(url: str) -> str:
    headers = {"User-Agent": "AEOAnalyzer/1.0"}
    try:
        async with httpx.AsyncClient(timeout=URL_FETCH_TIMEOUT, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except httpx.TimeoutException:
        raise ContentFetchError(
            "Could not retrieve content from the provided URL.",
            f"Connection timeout after {URL_FETCH_TIMEOUT}s",
        )
    except httpx.HTTPStatusError as e:
        raise ContentFetchError(
            "Could not retrieve content from the provided URL.",
            f"HTTP {e.response.status_code}",
        )
    except httpx.RequestError as e:
        raise ContentFetchError(
            "Could not retrieve content from the provided URL.",
            str(e),
        )


def _is_html(text: str) -> bool:
    soup = BeautifulSoup(text, "html.parser")
    return bool(soup.find())


def _get_main_content(soup: BeautifulSoup) -> Tag:
    for tag_name in ["main", "article"]:
        tag = soup.find(tag_name)
        if tag:
            return tag
    return soup.body if soup.body else soup


def _strip_boilerplate(soup: BeautifulSoup) -> str:
    working = BeautifulSoup(str(soup), "html.parser")
    for tag_name in BOILERPLATE_TAGS:
        for tag in working.find_all(tag_name):
            tag.decompose()
    return working.get_text(separator="\n", strip=True)


def _extract_first_paragraph_html(soup: BeautifulSoup) -> str:
    working = BeautifulSoup(str(soup), "html.parser")
    main = _get_main_content(soup=working)
    for tag_name in BOILERPLATE_TAGS:
        for tag in main.find_all(tag_name):
            tag.decompose()
    p = main.find("p")
    if p:
        return p.get_text(strip=True)
    text = main.get_text(strip=True)
    return text.split("\n\n")[0].strip() if text else ""


def _extract_first_paragraph_plain(text: str) -> str:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs[0] if paragraphs else ""


def _extract_headings(soup: BeautifulSoup) -> list[tuple[str, str]]:
    main = _get_main_content(soup=BeautifulSoup(str(soup), "html.parser"))
    headings = []
    for tag in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        headings.append((tag.name, tag.get_text(strip=True)))
    return headings


def _split_sentences(text: str) -> list[str]:
    sentences = []
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        doc = nlp(paragraph)
        sentences.extend(sent.text.strip() for sent in doc.sents if sent.text.strip())
    return sentences


def parse_content(raw: str, is_url_fetched: bool = False) -> ParsedContent:
    is_html = is_url_fetched or _is_html(text=raw)

    if is_html:
        soup = BeautifulSoup(raw, "html.parser")
        first_paragraph = _extract_first_paragraph_html(soup=soup)
        headings = _extract_headings(soup=soup)
        clean_text = _strip_boilerplate(soup=soup)
    else:
        first_paragraph = _extract_first_paragraph_plain(text=raw)
        headings = []
        clean_text = raw.strip()

    sentences = _split_sentences(text=clean_text) if clean_text else []

    return ParsedContent(
        first_paragraph=first_paragraph,
        headings=headings,
        clean_text=clean_text,
        sentences=sentences,
        is_html=is_html,
        raw=raw,
    )
