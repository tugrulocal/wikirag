# Product Requirements Document
## HW3 - Local Wikipedia RAG Assistant

| Field | Value |
|---|---|
| Project Name | HW3 - Local Wikipedia RAG Assistant |
| Version | 1.0 |
| Course | ITU AI Aided Computer Engineering |
| Status | Active Draft |
| Date | 2026-05-04 |
| Architecture Decision | Native-first local RAG with Option B metadata filtering |

## 1. Goal

Build a fully local ChatGPT-style assistant that answers questions about famous people and famous places using Wikipedia as the only content source. The system must run entirely on the user's laptop and must not rely on external LLM or embedding APIs.

The output must include both:

1. A working local Streamlit application
2. A clear, reproducible ingestion and retrieval pipeline with traceable storage

## 2. Core Functional Requirements

### 2.1 Ingest

Collect Wikipedia data for at least 20 famous people and 20 famous places.

Minimum required entries include the assignment list for people and places. The implementation may include additional pages, but it must cover the full minimum set.

Rules:

1. Wikipedia pages must be fetched locally through code, not manually copied
2. Ingestion must be repeatable and idempotent
3. Each record must carry a category metadata value of `person` or `place`
4. SQLite must keep a traceable registry of pages and chunks

### 2.2 Chunk

Split documents into smaller chunks before embedding.

Design requirement:

1. The chunking strategy must be documented
2. Chunk size and overlap must be chosen intentionally for retrieval quality
3. Each chunk must be traceable back to its source page

### 2.3 Embed and Store

Generate embeddings locally and store them in Chroma.

Required design choice:

1. Use one Chroma collection
2. Add metadata fields including `category=person|place`
3. Store source identity and chunk lineage for debugging and grading transparency

### 2.4 Retrieve

Determine whether a query is about a person, a place, or both.

Rules:

1. Use a simple keyword or rule-based intent router
2. Filter retrieval with metadata based on the detected category
3. For mixed queries, retrieve from both categories and merge the results

### 2.5 Generate

Generate answers using the local LLM and only the retrieved context.

Rules:

1. The model must not invent facts
2. If the answer is not in context, return exactly `I don't know`
3. Stream the answer to the UI as it is generated

### 2.6 UI

Provide a Streamlit interface that behaves like a chat application.

UI requirements:

1. Accept natural language questions
2. Stream answers progressively
3. Show Retrieval Latency for each response
4. Show Generation Latency for each response
5. Show matched source pages in a compact view

## 3. Technical Constraints

### 3.1 Native-Only Core Logic

The core logic must be implemented directly with Python libraries.

Allowed direct integrations:

- `requests` for Wikipedia and Ollama HTTP calls
- `chromadb` for vector storage
- `sqlite3` for registry persistence
- `streamlit` for the UI

### 3.2 No High-Level RAG Frameworks

Do not use LangChain, LlamaIndex, or similar frameworks to hide retrieval and generation behavior.

### 3.3 Environment

- Localhost execution only
- No external API keys
- The system must function on a single laptop, including an M4 Pro MacBook Pro

## 4. Architecture Decision

### 4.1 Decision

Use Option B:

1. One Chroma collection
2. Metadata-based routing and filtering using `category`

### 4.2 Why This Decision

1. It keeps the design simple and explainable
2. It supports mixed questions more flexibly
3. It matches the assignment constraint to explain category-aware retrieval

### 4.3 Rejected Alternatives

1. Separate vector stores for people and places were rejected because they complicate mixed-query handling
2. External APIs were rejected because the project must remain fully local

## 5. System Design

### 5.1 Ingestion Pipeline

1. A fixed list of people and places is used as the starting corpus
2. Wikipedia pages are fetched through the MediaWiki API
3. Extracted text is normalized
4. Page records are stored in SQLite
5. Chunk records are created and stored with lineage metadata

### 5.2 Vector Pipeline

1. Chunks are embedded locally with Ollama `nomic-embed-text`
2. Embeddings are written to Chroma
3. Metadata includes title, category, source URL, page id, and chunk index

### 5.3 Retrieval Pipeline

1. A simple router classifies each query as person, place, or both
2. Chroma search is filtered using the metadata category
3. Top-k chunks are merged into a grounded context block

### 5.4 Generation Pipeline

1. The local Ollama chat model receives a strict system prompt
2. The prompt tells the model to answer only from context
3. If the evidence is missing, it must return `I don't know`
4. Streaming output is shown in the UI

## 6. Acceptance Criteria

### 6.1 Functionality

1. The app ingests the minimum Wikipedia corpus
2. The app builds a persistent Chroma index
3. The app answers questions about people and places
4. The app returns `I don't know` when context is missing

### 6.2 UI and Metrics

1. Streamlit shows partial output during generation
2. Retrieval Latency is visible below each answer
3. Generation Latency is visible below each answer

### 6.3 Local-Only Behavior

1. No external LLM APIs are used
2. No external embedding APIs are used
3. All runtime artifacts are stored locally


1. Crawler state can be resumed after interruption
2. Snapshot files remain parseable and consistent

### 8.5 Multi-Agent Evidence

1. Workflow includes prompts, interactions, decisions
2. Agent files exist for every declared agent

## 9. Test Strategy

### 9.1 Unit Tests

1. Parser behavior
2. Crawler state controls
3. Search ranking + triple shaping

### 9.2 Integration Tests

1. `/index` to `/search` end-to-end
2. Dashboard/API consistency

### 9.3 Concurrency Tests

1. Index active while search queries run
2. Queue-pressure and throttle behavior

### 9.4 Recovery Tests

1. Interruption followed by resume
2. Snapshot load correctness

## 10. Deliverables

1. Working codebase
2. `README.md`
3. `product_prd.md`
4. `recommendation.md` (1-2 paragraphs)
5. `multi_agent_workflow.md`
6. Agent description files in `agents/`
