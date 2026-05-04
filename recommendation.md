# Production Deployment Recommendations

Transitioning WikiRAG from a localized, single-machine architecture to a production-ready cloud deployment requires fundamental shifts in scaling, latency management, and state persistence. Below is the architectural recommendation for deploying this RAG system to production.

## 1. LLM Hosting and Inference (Ollama -> vLLM / TGI)
While Ollama is phenomenal for local prototyping, it is not optimized for high-concurrency production requests. 
- **Recommendation:** Replace the local Ollama daemon with a dedicated GPU inference server using **vLLM** or **Text Generation Inference (TGI)**. 
- **Reasoning:** vLLM implements PagedAttention, which drastically improves memory efficiency and allows batching of concurrent generation requests, increasing throughput by up to 24x compared to naive HuggingFace/Ollama pipelines.
- **Hardware:** Deploy on AWS EC2 `g5.xlarge` or GCP `g2-standard` instances equipped with NVIDIA L4/A10G GPUs.

## 2. Vector Database Scaling (Local ChromaDB -> Pinecone / Qdrant)
Currently, ChromaDB writes to a local `chroma_db` folder, which makes it stateful and impossible to horizontally scale across multiple Docker containers.
- **Recommendation:** Migrate from local ChromaDB to a managed vector database like **Pinecone**, or a distributed hosted cluster of **Qdrant / Milvus**.
- **Reasoning:** This allows the embedding layer and the Streamlit front-end to be completely stateless. Multiple instances of the app can query the same centralized vector store simultaneously.

## 3. Asynchronous Data Ingestion (Celery + Redis)
Data ingestion (scraping Wikipedia) currently blocks the main thread or requires manual script execution.
- **Recommendation:** Implement an asynchronous task queue using **Celery** with **Redis** as a message broker.
- **Reasoning:** When new Wikipedia pages need to be ingested, the web app can dispatch a background task to Celery. The worker will fetch the Wikipedia data, chunk it, generate embeddings, and upsert them to Pinecone without slowing down the user-facing web server.

## 4. Caching for Cost and Latency Reduction
- **Recommendation:** Implement semantic caching using **Redis** or a specialized tool like **GPTCache**.
- **Reasoning:** If 1,000 users ask "Who is Albert Einstein?", generating the same answer 1,000 times wastes GPU resources. By caching the semantic intent of the question, the system can instantly return the cached LLM response for identical or highly similar queries, reducing latency to milliseconds and cutting inference costs.

## 5. Security & Fallback Mechanisms
- **Guardrails:** Add an input validation layer (e.g., Llama Guard) to prevent prompt injection and ensure users only ask questions related to historical figures and places.
- **Streaming & Load Balancing:** Place the Streamlit/FastAPI backend behind an **NGINX** reverse proxy and an AWS Application Load Balancer (ALB) to handle traffic spikes smoothly.
