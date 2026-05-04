"""Shared data models for ingestion and retrieval."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageRecord:
    page_id: int
    title: str
    category: str
    extract: str
    source_url: str


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    page_id: int
    title: str
    category: str
    chunk_index: int
    text: str
    source_url: str


@dataclass(frozen=True)
class RetrievalResult:
    title: str
    category: str
    text: str
    source_url: str
    score: float


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    retrieval_latency: float
    generation_latency: float
    sources: list[RetrievalResult]
