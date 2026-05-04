# WikiRAG - Local Wikipedia RAG Assistant 🧠

WikiRAG is a fully local, 100% offline Retrieval-Augmented Generation (RAG) assistant designed to accurately answer complex questions about famous people and places using data fetched from Wikipedia.

## Features ✨
- **100% Local Stack:** No external API calls are made during inference. It uses **Ollama** for running LLMs securely on your machine.
- **Advanced Embeddings:** Utilizes `mxbai-embed-large` for high-quality semantic vector representations.
- **Fast Generation:** Employs `llama3.2` as the core reasoning engine, optimized with hardware-safe limits and strict encyclopedic instruction sets.
- **Robust Storage:** Built on top of **ChromaDB** for vector persistence and **SQLite** for document metadata registry.
- **Premium UI:** Features a modern, Glassmorphism-inspired dark theme built with Streamlit, complete with popover modals and latency metrics.

## Prerequisites 📦
- Python 3.9+
- [Ollama](https://ollama.com) installed and running locally.

## How to Install Dependencies 🚀
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

## How to Run the Local Model 🤖
Make sure Ollama is running in the background. Then, pull the required models:
```bash
ollama pull llama3.2
ollama pull mxbai-embed-large
```

## How to Ingest Data 📚
The system allows automated data ingestion from Wikipedia. 
If it is your first time, the application will automatically prompt you to build the index.
To manually ingest data or rebuild the index from scratch, you can either:
1. Click the **"Rebuild Vector Index"** button in the Streamlit Sidebar.
2. Or run the ingestion script directly from the terminal:
   ```bash
   python hw3/ingest_runner.py
   ```

## How to Start the Application 🖥️
Run the Streamlit application:
```bash
streamlit run streamlit_app.py
```
This will open the user interface in your default web browser at `http://localhost:8501`.

## Example Queries ❓
You can ask questions regarding the ingested Wikipedia entities. The system will safely reject unknown queries (e.g., "President of Mars") with a fallback "I don't know" response.

**People:**
- *Who was Albert Einstein and what is he known for?*
- *What did Marie Curie discover?*
- *Compare Lionel Messi and Cristiano Ronaldo.*

**Places:**
- *Where is the Eiffel Tower located?*
- *What was the Colosseum used for?*

**Mixed & Fallbacks:**
- *Which famous place is located in Turkey?*
- *Compare Albert Einstein and Nikola Tesla.*
- *Who is the president of Mars?* (Returns "I don't know")