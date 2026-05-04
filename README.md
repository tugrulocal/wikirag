# WikiRAG - Local Wikipedia RAG Assistant 🧠

WikiRAG is a fully local, 100% offline Retrieval-Augmented Generation (RAG) assistant designed to accurately answer complex questions about famous people and places using data fetched from Wikipedia.

## Features ✨
- **100% Local Stack:** No external API calls are made during inference. It uses **Ollama** for running LLMs securely on your machine.
- **Advanced Embeddings:** Utilizes `mxbai-embed-large` for high-quality semantic vector representations.
- **Fast Generation:** Employs `llama3.2` as the core reasoning engine, optimized with hardware-safe limits and strict encyclopedic instruction sets to prevent overheating and hallucination.
- **Robust Storage:** Built on top of **ChromaDB** for vector persistence and **SQLite** for document metadata registry.
- **Premium UI:** Features a modern, Glassmorphism-inspired dark theme built with Streamlit, complete with popover modals and Material icons.

## Prerequisites 📦
- Python 3.9+
- [Ollama](https://ollama.com) installed and running locally.
- Ollama models pulled:
  ```bash
  ollama pull llama3.2
  ollama pull mxbai-embed-large
  ```

## Installation 🚀
1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/wikirag.git
   cd wikirag
   ```
2. Set up the virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage 💡
Run the Streamlit application:
```bash
streamlit run streamlit_app.py
```
*Note: Upon first launch, if the index is empty, use the "Rebuild Vector Index" button in the sidebar to fetch Wikipedia data and build the local ChromaDB index.*

## Architecture 🏗️
- **Ingestion (`hw3/ingestor.py`):** Fetches predefined Wikipedia pages, chunks text, and stores them in SQLite.
- **Vector Store (`hw3/vector_store.py`):** Interfaces with ChromaDB to map document chunks into a semantic vector space.
- **RAG Engine (`hw3/rag.py`):** Routes intents, retrieves top-k relevant chunks, and orchestrates the Ollama generation stream.
- **UI (`streamlit_app.py`):** Provides a seamless, interactive front-end experience.