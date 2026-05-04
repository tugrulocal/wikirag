"""Wikipedia ingestion pipeline for the local HW3 RAG assistant."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import asdict
from typing import Iterable

import requests

from hw3.config import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_PEOPLE,
    DEFAULT_PLACES,
    SQLITE_PATH,
)
from hw3.models import ChunkRecord, PageRecord

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_HEADERS = {
    "User-Agent": "HW3-WikiRAG/1.0 (BLG483E course project; local-only RAG assistant) python-requests/2.x",
}


def ensure_storage() -> None:
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[str]:
    words = _normalize_whitespace(text).split()
    if not words:
        return []

    step = max(1, chunk_size - overlap)
    chunks: list[str] = []
    for start in range(0, len(words), step):
        chunk = words[start:start + chunk_size]
        if chunk:
            chunks.append(" ".join(chunk))
    return chunks


def _looks_like_person(title: str) -> bool:
    lower = title.lower()
    person_tokens = {
        "einstein",
        "curie",
        "tesla",
        "swift",
        "messi",
        "ronaldo",
        "shakespeare",
        "lovelace",
        "kahlo",
        "newton",
        "gandhi",
        "mandela",
        "hawking",
        "christie",
        "musk",
        "beyoncé",
        "picasso",
        "lovelace",
    }
    place_tokens = {"tower", "wall", "temple", "falls", "city", "mount", "giza", "canyon", "opera", "castle", "mahal", "hagia", "statue", "colosseum"}
    if any(token in lower for token in person_tokens):
        return True
    if any(token in lower for token in place_tokens):
        return False
    return " " in title


def mediawiki_extract(title: str, category: str | None = None) -> PageRecord:
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|info",
        "explaintext": 1,
        "redirects": 1,
        "inprop": "url",
        "titles": title,
    }
    response = requests.get(WIKIPEDIA_API_URL, params=params, headers=WIKIPEDIA_HEADERS, timeout=30)
    response.raise_for_status()
    payload = response.json().get("query", {}).get("pages", {})
    page = next(iter(payload.values()))

    extract = _normalize_whitespace(page.get("extract", ""))
    if not extract:
        raise ValueError(f"Wikipedia page has no extract: {title}")

    canonical_title = page.get("title", title)
    source_url = page.get("fullurl") or f"https://en.wikipedia.org/wiki/{canonical_title.replace(' ', '_')}"
    category = category or ("person" if _looks_like_person(title) else "place")
    page_id = int(page.get("pageid", 0))
    return PageRecord(page_id=page_id, title=canonical_title, category=category, extract=extract, source_url=source_url)


def _open_database() -> sqlite3.Connection:
    ensure_storage()
    connection = sqlite3.connect(SQLITE_PATH)
    connection.execute("PRAGMA journal_mode=WAL")
    return connection


def initialize_registry() -> None:
    with _open_database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS pages (
                page_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                extract TEXT NOT NULL,
                source_url TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                page_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                source_url TEXT NOT NULL,
                FOREIGN KEY(page_id) REFERENCES pages(page_id)
            )
            """
        )


def save_pages(pages: Iterable[PageRecord]) -> None:
    initialize_registry()
    with _open_database() as connection:
        connection.executemany(
            """
            INSERT INTO pages(page_id, title, category, extract, source_url)
            VALUES(:page_id, :title, :category, :extract, :source_url)
            ON CONFLICT(title) DO UPDATE SET
                page_id=excluded.page_id,
                category=excluded.category,
                extract=excluded.extract,
                source_url=excluded.source_url
            """,
            [asdict(page) for page in pages],
        )


def save_chunks(chunks: Iterable[ChunkRecord]) -> None:
    initialize_registry()
    with _open_database() as connection:
        connection.executemany(
            """
            INSERT INTO chunks(chunk_id, page_id, title, category, chunk_index, text, source_url)
            VALUES(:chunk_id, :page_id, :title, :category, :chunk_index, :text, :source_url)
            ON CONFLICT(chunk_id) DO UPDATE SET
                page_id=excluded.page_id,
                title=excluded.title,
                category=excluded.category,
                chunk_index=excluded.chunk_index,
                text=excluded.text,
                source_url=excluded.source_url
            """,
            [asdict(chunk) for chunk in chunks],
        )


def build_corpus() -> list[PageRecord]:
    titles = [(title, "person") for title in DEFAULT_PEOPLE] + [(title, "place") for title in DEFAULT_PLACES]
    corpus: list[PageRecord] = []
    for title, category in titles:
        try:
            corpus.append(mediawiki_extract(title, category=category))
        except Exception:
            continue
    save_pages(corpus)
    return corpus


def build_chunks(pages: Iterable[PageRecord]) -> list[ChunkRecord]:
    chunks: list[ChunkRecord] = []
    for page in pages:
        for chunk_index, text in enumerate(chunk_text(page.extract), start=1):
            chunks.append(
                ChunkRecord(
                    chunk_id=f"{page.page_id}:{chunk_index}",
                    page_id=page.page_id,
                    title=page.title,
                    category=page.category,
                    chunk_index=chunk_index,
                    text=text,
                    source_url=page.source_url,
                )
            )
    save_chunks(chunks)
    return chunks


def load_pages() -> list[PageRecord]:
    initialize_registry()
    with _open_database() as connection:
        rows = connection.execute("SELECT page_id, title, category, extract, source_url FROM pages ORDER BY title").fetchall()
    return [PageRecord(*row) for row in rows]


def load_chunks() -> list[ChunkRecord]:
    initialize_registry()
    with _open_database() as connection:
        rows = connection.execute(
            "SELECT chunk_id, page_id, title, category, chunk_index, text, source_url FROM chunks ORDER BY title, chunk_index"
        ).fetchall()
    return [ChunkRecord(*row) for row in rows]
