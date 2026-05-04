"""Local RAG core: routing, retrieval, and grounded generation."""

from __future__ import annotations

import json
import re
import time
from typing import Generator

import requests

from hw3.config import DEFAULT_TOP_K, OLLAMA_CHAT_MODEL, OLLAMA_URL, PERSON_KEYWORDS, PLACE_KEYWORDS
from hw3.models import AnswerResult, RetrievalResult
from hw3.vector_store import VectorManager


SYSTEM_PROMPT = (
    "You are a Wikipedia assistant that answers questions about famous people and famous places. "
    "You are given numbered context excerpts from Wikipedia. "
    "Your job is to read the excerpts carefully and answer the user's specific question. "
    "Write a clear, direct, and concise answer. Focus strictly on answering the question asked. "
    "Keep your answer under 3 paragraphs. Do not write a massive essay. "
    "Do NOT make up information that is not in the excerpts. "
    "If none of the excerpts contain relevant information to answer the question, "
    "reply with exactly: I don't know"
)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def route_intent(question: str) -> list[str]:
    tokens = set(_tokenize(question))
    person_hits = len(tokens & PERSON_KEYWORDS)
    place_hits = len(tokens & PLACE_KEYWORDS)

    if person_hits and place_hits:
        return ["person", "place"]
    if person_hits:
        return ["person"]
    if place_hits:
        return ["place"]

    lowered = question.lower()
    if any(word in lowered for word in ("who is", "who was", "biography", "born")):
        return ["person"]
    if any(word in lowered for word in ("where is", "located", "where was", "place")):
        return ["place"]
    return ["person", "place"]


class LocalRAGAssistant:
    def __init__(self, vector_manager: VectorManager | None = None) -> None:
        self.vector_manager = vector_manager or VectorManager()

    def retrieve(self, question: str, top_k: int = DEFAULT_TOP_K) -> tuple[list[RetrievalResult], float]:
        start = time.perf_counter()
        categories = route_intent(question)
        results = self.vector_manager.search(question, categories=categories, top_k=top_k)
        return results, time.perf_counter() - start

    def _build_context(self, sources: list[RetrievalResult]) -> str:
        if not sources:
            return ""
        blocks = []
        for index, source in enumerate(sources, start=1):
            blocks.append(
                f"--- Excerpt {index} ---\n"
                f"Source: {source.title} ({source.category})\n"
                f"{source.text}"
            )
        return "\n\n".join(blocks)

    def _generate_stream(self, question: str, context: str) -> Generator[str, None, None]:
        payload = {
            "model": OLLAMA_CHAT_MODEL,
            "stream": True,
            "options": {
                "temperature": 0.1,  # Focused, deterministic, less hallucination
                "top_p": 0.9,
                "num_ctx": 4096,     # Restrict context size memory usage
                "num_predict": 350,  # HARD STOP: Max 350 tokens to prevent Mac overheating
            },
            "keep_alive": "10m",     # Keep model in memory for 10 minutes to avoid cold starts
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Wikipedia Context Excerpts:\n\n{context}\n\nQuestion: {question}\n\nAnswer based on the excerpts above:"},
            ],
        }
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, stream=True, timeout=300)
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            payload_line = json.loads(line)
            chunk = payload_line.get("message", {}).get("content", "")
            if chunk:
                yield chunk
            if payload_line.get("done"):
                break

    def answer(self, question: str) -> AnswerResult:
        sources, retrieval_latency = self.retrieve(question)
        if not sources:
            return AnswerResult(answer="I don't know", retrieval_latency=retrieval_latency, generation_latency=0.0, sources=[])

        context = self._build_context(sources)
        start = time.perf_counter()
        answer_text = ""
        for chunk in self._generate_stream(question, context):
            answer_text += chunk
        generation_latency = time.perf_counter() - start
        cleaned = answer_text.strip() or "I don't know"
        return AnswerResult(
            answer=cleaned,
            retrieval_latency=retrieval_latency,
            generation_latency=generation_latency,
            sources=sources,
        )

    def stream_answer(self, question: str):
        sources, retrieval_latency = self.retrieve(question)
        if not sources:
            yield {
                "type": "final",
                "answer": "I don't know",
                "retrieval_latency": retrieval_latency,
                "generation_latency": 0.0,
                "sources": [],
            }
            return

        context = self._build_context(sources)
        start = time.perf_counter()
        answer_text = ""
        for chunk in self._generate_stream(question, context):
            answer_text += chunk
            yield {"type": "chunk", "chunk": chunk}
        generation_latency = time.perf_counter() - start
        yield {
            "type": "final",
            "answer": answer_text.strip() or "I don't know",
            "retrieval_latency": retrieval_latency,
            "generation_latency": generation_latency,
            "sources": sources,
        }
