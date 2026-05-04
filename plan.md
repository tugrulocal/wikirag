## Plan: Local Wikipedia RAG Assistant HW3

Build a fully local RAG assistant for celebrities and famous places using Ollama + Chroma + SQLite + Streamlit. The implementation must stay native-first, use Option B metadata filtering in one vector collection, avoid LangChain/LlamaIndex, and return "I don't know" when the retrieved context does not contain the answer.

**Architecture Summary**
- Ingestor Modülü: Wikipedia sayfalarını çeker, temizler, canonical kayıt üretir ve veri tabanına yazar.
- Vector Manager: chunk + embedding + Chroma index + metadata yönetimini yapar.
- RAG Core: intent routing, retrieval filtering, context assembly ve grounded generation akışını yönetir.
- UI/Dashboard: Streamlit chat, streaming cevaplar, latency metrikleri ve demo görünümü sağlar.

**Implementation Order**
1. Scope and contract freeze: finalize local-only stack, Option B metadata, target list, output schema, and file layout before writing code.
2. Ingestor pipeline: collect at least 20 people and 20 places from Wikipedia and persist clean source records.
3. Chunking + embedding: split documents deterministically, embed locally with Ollama nomic-embed-text, and persist vectors with metadata.
4. Retrieval routing: detect person/place/both and filter Chroma queries by metadata before rank assembly.
5. Generation policy: create grounded prompts, stream local LLM output, and enforce fallback to "I don't know".
6. Streamlit UX: expose chat interface, streaming token display, retrieval latency, generation latency, and optional source context inspector.
7. Tests and verification: validate coverage, metadata correctness, routing, fallback behavior, and latency reporting.
8. Documentation and demo: update README, PRD, recommendation, requirements, and prepare a 5-minute demo script.

---

## ✅ Detailed Task Checklist

### 1. Ingestor Modülü
- [x] Define the fixed seed list of required people and places from the assignment → `hw3/config.py`
- [x] Build a Wikipedia fetch layer using the MediaWiki API → `hw3/ingestor.py::mediawiki_extract`
- [x] Normalize page title, summary text, infobox-like key facts, and source URL
- [x] Store each canonical page in SQLite as a durable registry entry → `hw3/ingestor.py::save_pages`
- [x] Mark each record with category = person or category = place
- [x] Make ingestion idempotent so reruns update existing records instead of duplicating them (ON CONFLICT DO UPDATE)
- [x] Add a failure-safe fallback for pages that cannot be fetched or parsed
- [x] Create CLI runner for ingestion → `hw3/ingest_runner.py`

### 2. Vector Manager
- [x] Split each source document into chunks with a chosen size and overlap → `hw3/ingestor.py::chunk_text`
- [x] Persist chunk lineage in SQLite so each vector can be traced back to its page and chunk id → `hw3/ingestor.py::save_chunks`
- [x] Generate embeddings locally with Ollama nomic-embed-text → `hw3/vector_store.py::_ollama_embedding`
- [x] Store all vectors in one Chroma collection using Option B metadata → `hw3/vector_store.py::VectorManager`
- [x] Add metadata fields for category, title, source_url, chunk_id, and source_type
- [x] Implement collection reset/rebuild support for full reindexing → `hw3/vector_store.py::VectorManager.reset`

### 3. RAG Core
- [x] Build a lightweight intent router using keyword/rule-based logic → `hw3/rag.py::route_intent`
- [x] Detect whether a query is about a person, a place, or both
- [x] Filter Chroma search by metadata category before retrieval → `hw3/vector_store.py::VectorManager.search`
- [x] For mixed queries, merge top-k results from both categories in a controlled way
- [x] Assemble context with source traceability → `hw3/rag.py::LocalRAGAssistant._build_context`
- [x] Craft the system prompt so the model only answers from provided context → `hw3/rag.py::SYSTEM_PROMPT`
- [x] Enforce the exact fallback behavior: if context is insufficient, reply "I don't know"
- [x] Measure retrieval latency and generation latency separately → `hw3/rag.py::LocalRAGAssistant.answer`

### 4. UI/Dashboard
- [x] Create a Streamlit chat-style interface → `streamlit_app.py`
- [x] Stream the response token-by-token with streaming cursor animation
- [x] Display retrieval latency and generation latency under each assistant message (latency badge)
- [x] Show a compact sources panel with the matched Wikipedia pages and categories (source cards)
- [x] Add a sidebar status area for local model availability and index health
- [x] Premium dark-mode design with gradient header and micro-interactions

### 5. Tests
- [x] `hw3/tests/test_ingestor.py`: chunk_text, normalize_whitespace, _looks_like_person
- [x] `hw3/tests/test_rag.py`: route_intent (person/place/mixed/ambiguous), fallback behavior
- [x] `hw3/tests/test_vector_store.py`: metadata fields, result ordering, top_k enforcement

### 6. Data Ingestion (Runtime)
- [ ] Run `python -m hw3.ingest_runner` to fetch 40 Wikipedia pages
- [ ] Verify 20 people + 20 places are in SQLite registry
- [ ] Verify Chroma index has vectors for all chunks

### 7. Quality Gates
- [ ] Confirm the repository contains at least 20 people and 20 places ingested successfully
- [ ] Validate that person-only queries never retrieve place-only chunks unless the query is mixed
- [ ] Validate that out-of-scope questions produce exactly "I don't know"
- [ ] Validate that streaming UI renders partial output before completion
- [ ] Validate that no external API calls are made in ingest, retrieve, or generate flows

### 8. Documentation
- [ ] Update README.md for HW3 setup, local model setup, ingestion, and Streamlit run instructions
- [ ] Keep requirements.txt minimal and correct

---

**Design Decisions**
- Use Option B: one Chroma collection with metadata category filtering.
- Use Ollama for both chat LLM and embeddings through direct native integration.
- Keep a small SQLite registry for traceability, auditing, and grading transparency.
- Prefer deterministic rules over heavier frameworks for intent routing and answer control.
- Optimize for M4 Pro by starting with the lightest acceptable local model and only upgrading if quality requires it.

**Open Notes**
- If Wikipedia text extraction is fragile, prefer the MediaWiki API over HTML scraping.
- If the first embedding model is too slow, re-evaluate sentence-transformers as a fallback, but do not switch unless necessary.
- Preserve the fallback contract exactly: when evidence is missing, the answer must not improvise.
