"""Tests for hw3.rag: intent routing and fallback behavior."""

from __future__ import annotations

import pytest

from hw3.rag import route_intent, LocalRAGAssistant
from hw3.models import RetrievalResult


# ── route_intent ─────────────────────────────────────────────────────────────

class TestRouteIntent:
    @pytest.mark.parametrize("question,expected", [
        ("Who is Albert Einstein?", ["person"]),
        ("Who was Marie Curie?", ["person"]),
        ("Tell me about the biography of Tesla", ["person"]),
        ("When was Newton born?", ["person"]),
    ])
    def test_person_queries(self, question: str, expected: list[str]) -> None:
        result = route_intent(question)
        assert result == expected, f"Expected {expected} for: {question!r}"

    @pytest.mark.parametrize("question,expected", [
        ("Where is the Eiffel Tower located?", ["place"]),
        ("Where was the Taj Mahal built?", ["place"]),
        ("Tell me about the city of Paris", ["place"]),
        ("How tall is the mountain?", ["place"]),
    ])
    def test_place_queries(self, question: str, expected: list[str]) -> None:
        result = route_intent(question)
        assert result == expected, f"Expected {expected} for: {question!r}"

    def test_mixed_query_returns_both(self) -> None:
        question = "Who built the tower and what scientist was born there?"
        result = route_intent(question)
        assert set(result) == {"person", "place"}

    def test_ambiguous_query_returns_both(self) -> None:
        result = route_intent("Tell me something interesting")
        assert set(result) == {"person", "place"}

    def test_result_is_list(self) -> None:
        result = route_intent("Who is Messi?")
        assert isinstance(result, list)
        assert len(result) >= 1


# ── LocalRAGAssistant fallback ────────────────────────────────────────────────

class _EmptyVectorManager:
    """Stub that always returns no results."""
    def search(self, query: str, categories=None, top_k: int = 5) -> list:
        return []


class TestFallbackBehavior:
    def test_returns_i_dont_know_when_no_sources(self) -> None:
        assistant = LocalRAGAssistant(vector_manager=_EmptyVectorManager())  # type: ignore[arg-type]
        result = assistant.answer("What is the population of Mars?")
        assert result.answer == "I don't know"

    def test_fallback_has_zero_generation_latency(self) -> None:
        assistant = LocalRAGAssistant(vector_manager=_EmptyVectorManager())  # type: ignore[arg-type]
        result = assistant.answer("What is the population of Mars?")
        assert result.generation_latency == 0.0

    def test_fallback_sources_are_empty(self) -> None:
        assistant = LocalRAGAssistant(vector_manager=_EmptyVectorManager())  # type: ignore[arg-type]
        result = assistant.answer("Random nonsense question xyz123")
        assert result.sources == []

    def test_stream_fallback_emits_final_event(self) -> None:
        assistant = LocalRAGAssistant(vector_manager=_EmptyVectorManager())  # type: ignore[arg-type]
        events = list(assistant.stream_answer("Random nonsense xyz"))
        assert len(events) == 1
        assert events[0]["type"] == "final"
        assert events[0]["answer"] == "I don't know"
