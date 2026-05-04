"""Chroma-based vector manager with Ollama embeddings."""

from __future__ import annotations

import chromadb
import requests

from hw3.config import CHROMA_COLLECTION, CHROMA_PATH, OLLAMA_EMBED_MODEL, OLLAMA_URL
from hw3.models import ChunkRecord, RetrievalResult


def _ollama_embedding(text: str) -> list[float]:
    import time
    for attempt in range(3):
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
                timeout=120,
            )
            response.raise_for_status()
            # small delay to prevent overwhelming Ollama API
            time.sleep(0.01)
            return response.json()["embedding"]
        except Exception as e:
            if attempt == 2:
                print(f"Warning: Failed to embed text: {str(e)[:100]}")
                # return zero vector if it consistently fails
                return [0.0] * 1024  # mxbai-embed-large uses 1024 dims
            time.sleep(1)
    return [0.0] * 1024


class VectorManager:
    def __init__(self) -> None:
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        self.collection = self.client.get_or_create_collection(name=CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"})

    def reset(self) -> None:
        try:
            self.client.delete_collection(CHROMA_COLLECTION)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(name=CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"})

    def upsert_chunks(self, chunks: list[ChunkRecord]) -> int:
        if not chunks:
            return 0

        # Process in batches to avoid overloading Ollama
        batch_size = 50
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            # mxbai-embed-large doesn't need a prefix for documents
            embeddings = [_ollama_embedding(chunk.text) for chunk in batch]
            self.collection.upsert(
                ids=[chunk.chunk_id for chunk in batch],
                embeddings=embeddings,
                documents=[chunk.text for chunk in batch],
                metadatas=[
                    {
                        "page_id": chunk.page_id,
                        "title": chunk.title,
                        "category": chunk.category,
                        "chunk_index": chunk.chunk_index,
                        "source_url": chunk.source_url,
                    }
                    for chunk in batch
                ],
            )
        return len(chunks)

    def search(self, query: str, categories: list[str] | None = None, top_k: int = 6) -> list[RetrievalResult]:
        categories = categories or ["person", "place"]
        # mxbai-embed-large requires this specific prefix for query vectors
        query_embedding = _ollama_embedding("Represent this sentence for searching relevant passages: " + query)
        results: list[RetrievalResult] = []

        for category in categories:
            response = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"category": category},
                include=["documents", "metadatas", "distances"],
            )
            documents = response.get("documents", [[]])[0]
            metadatas = response.get("metadatas", [[]])[0]
            distances = response.get("distances", [[]])[0]

            for document, metadata, distance in zip(documents, metadatas, distances):
                results.append(
                    RetrievalResult(
                        title=metadata["title"],
                        category=metadata["category"],
                        text=document,
                        source_url=metadata["source_url"],
                        score=max(0.0, 1.0 - float(distance)),
                    )
                )

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]


def rebuild_index(vector_manager: VectorManager, chunks: list[ChunkRecord]) -> int:
    vector_manager.reset()
    return vector_manager.upsert_chunks(chunks)
