# Product Requirements Document (PRD)

## 1. Product Overview
**WikiRAG** is an AI-powered educational assistant designed to provide accurate, fact-based answers about famous historical figures and global landmarks. It replaces traditional search engines by synthesizing direct answers from Wikipedia excerpts, ensuring users never receive hallucinated information. 

## 2. Target Audience
- Students needing quick summaries for assignments.
- History and geography enthusiasts.
- General users seeking reliable, encyclopedic knowledge without reading through long articles.

## 3. Core Features & Requirements

### 3.1. Accurate Retrieval (RAG)
- **Requirement:** The system must scrape context directly from Wikipedia to prevent the LLM from relying on its internal, potentially flawed memory.
- **Constraint:** The system must strictly say "I don't know" if the answer is not present in the ingested Wikipedia database (e.g., "President of Mars").

### 3.2. Local Execution
- **Requirement:** The entire stack must run locally to ensure 100% data privacy and zero API costs.
- **Tech Stack:** Ollama (`llama3.2` for generation, `mxbai-embed-large` for embeddings), ChromaDB, SQLite.

### 3.3. Intuitive UI/UX
- **Requirement:** A chat-based interface that is easy to navigate.
- **Features:** 
  - Glassmorphism dark mode for readability.
  - Sidebar with visual stats (number of pages, vectors, chunks).
  - Explainer modals displaying currently supported entities (People and Places).

### 3.4. Citation & Transparency
- **Requirement:** Users must know *where* the AI got its information.
- **Implementation:** Every response must include a dropdown expander listing the exact Wikipedia sources used to generate the answer.

## 4. Success Metrics
- **Retrieval Accuracy:** >95% precision in matching user queries to the correct Wikipedia chunks.
- **Latency:** Sub-second retrieval (<1.0s) and fast generation (<5.0s on Mac M-series chips).
- **Zero Hallucination:** 100% compliance with the "I don't know" fallback when asked out-of-scope questions.
