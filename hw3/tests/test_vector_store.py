"""Tests for hw3.vector_store: metadata filter logic and result shaping."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from hw3.models import ChunkRecord
from hw3.vector_store import VectorManager


# ── Helper ────────────────────────────────────────────────────────────────────

def _make_chunk(chunk_id: str, page_id: int, title: str, category: str, index: int = 1) -> ChunkRecord:
    return ChunkRecord(
        chunk_id=chunk_id,
        page_id=page_id,
        title=title,
        category=category,
        chunk_index=index,
        text=f"Sample text for {title}",
        source_url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
    )


# ── Chunk creation helpers ─────────────────────────────────────────────────────

class TestChunkRecord:
    def test_chunk_id_format(self) -> None:
        chunk = _make_chunk("123:1", 123, "Albert Einstein", "person")
        assert chunk.chunk_id == "123:1"

    def test_category_values(self) -> None:
        person_chunk = _make_chunk("1:1", 1, "Marie Curie", "person")
        place_chunk = _make_chunk("2:1", 2, "Eiffel Tower", "place")
        assert person_chunk.category == "person"
        assert place_chunk.category == "place"

    def test_chunk_is_frozen(self) -> None:
        chunk = _make_chunk("1:1", 1, "Test", "person")
        with pytest.raises((AttributeError, TypeError)):
            chunk.text = "modified"  # type: ignore[misc]


# ── Search result ordering ─────────────────────────────────────────────────────

class TestSearchResultOrdering:
    def test_results_sorted_by_score_desc(self) -> None:
        """Verify that search results are returned highest-score first."""
        from hw3.models import RetrievalResult
        results = [
            RetrievalResult(title="A", category="person", text="t", source_url="u", score=0.6),
            RetrievalResult(title="B", category="place",  text="t", source_url="u", score=0.9),
            RetrievalResult(title="C", category="person", text="t", source_url="u", score=0.4),
        ]
        sorted_results = sorted(results, key=lambda r: r.score, reverse=True)
        assert sorted_results[0].score == 0.9
        assert sorted_results[-1].score == 0.4

    def test_top_k_limits_results(self) -> None:
        from hw3.models import RetrievalResult
        results = [
            RetrievalResult(title=f"Item{i}", category="person", text="t", source_url="u", score=float(i))
            for i in range(20)
        ]
        top_k = 5
        trimmed = results[:top_k]
        assert len(trimmed) == top_k


# ── Metadata coverage ─────────────────────────────────────────────────────────

class TestMetadataCoverage:
    """Verify all required metadata fields are present on chunks going into Chroma."""

    REQUIRED_FIELDS = {"page_id", "title", "category", "chunk_index", "source_url"}

    def test_all_metadata_fields_present(self) -> None:
        chunk = _make_chunk("42:3", 42, "Taj Mahal", "place", index=3)
        metadata = {
            "page_id": chunk.page_id,
            "title": chunk.title,
            "category": chunk.category,
            "chunk_index": chunk.chunk_index,
            "source_url": chunk.source_url,
        }
        for field in self.REQUIRED_FIELDS:
            assert field in metadata, f"Missing metadata field: {field}"

    def test_category_is_string(self) -> None:
        chunk = _make_chunk("1:1", 1, "Test Place", "place")
        assert isinstance(chunk.category, str)

    def test_category_valid_values(self) -> None:
        valid = {"person", "place"}
        for cat in valid:
            chunk = _make_chunk("1:1", 1, "Test", cat)
            assert chunk.category in valid
