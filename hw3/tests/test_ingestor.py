"""Tests for hw3.ingestor: chunking and normalization logic."""

from __future__ import annotations

import pytest

from hw3.ingestor import _normalize_whitespace, chunk_text, _looks_like_person


# ── _normalize_whitespace ────────────────────────────────────────────────────

class TestNormalizeWhitespace:
    def test_collapses_multiple_spaces(self) -> None:
        assert _normalize_whitespace("hello   world") == "hello world"

    def test_strips_leading_trailing(self) -> None:
        assert _normalize_whitespace("  hello ") == "hello"

    def test_collapses_newlines(self) -> None:
        assert _normalize_whitespace("line1\n\nline2\t  line3") == "line1 line2 line3"

    def test_empty_string(self) -> None:
        assert _normalize_whitespace("") == ""


# ── chunk_text ───────────────────────────────────────────────────────────────

class TestChunkText:
    def test_short_text_single_chunk(self) -> None:
        text = " ".join(["word"] * 50)
        chunks = chunk_text(text, chunk_size=180, overlap=40)
        assert len(chunks) == 1

    def test_long_text_multiple_chunks(self) -> None:
        text = " ".join([f"word{i}" for i in range(500)])
        chunks = chunk_text(text, chunk_size=180, overlap=40)
        assert len(chunks) > 1

    def test_no_chunk_exceeds_size(self) -> None:
        text = " ".join([f"word{i}" for i in range(600)])
        chunks = chunk_text(text, chunk_size=180, overlap=40)
        for chunk in chunks:
            assert len(chunk.split()) <= 180

    def test_overlap_provides_continuity(self) -> None:
        """Last words of chunk N should appear at start of chunk N+1."""
        words = [f"w{i}" for i in range(300)]
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        if len(chunks) >= 2:
            last_words_of_first = set(chunks[0].split()[-20:])
            first_words_of_second = set(chunks[1].split()[:20])
            assert last_words_of_first & first_words_of_second, "Overlap words should appear in both chunks"

    def test_empty_text(self) -> None:
        assert chunk_text("") == []

    def test_whitespace_only_text(self) -> None:
        assert chunk_text("   \n\t  ") == []

    def test_chunk_ids_are_deterministic(self) -> None:
        text = " ".join([f"word{i}" for i in range(400)])
        assert chunk_text(text) == chunk_text(text)


# ── _looks_like_person ────────────────────────────────────────────────────────

class TestLooksLikePerson:
    @pytest.mark.parametrize("title", [
        "Albert Einstein",
        "Marie Curie",
        "Nikola Tesla",
        "Taylor Swift",
        "Lionel Messi",
    ])
    def test_known_people_detected(self, title: str) -> None:
        assert _looks_like_person(title) is True

    @pytest.mark.parametrize("title", [
        "Eiffel Tower",
        "Great Wall of China",
        "Hagia Sophia",
        "Grand Canyon",
        "Niagara Falls",
    ])
    def test_known_places_not_detected_as_person(self, title: str) -> None:
        assert _looks_like_person(title) is False
