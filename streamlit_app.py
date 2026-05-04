"""Premium Streamlit UI for the HW3 Local Wikipedia RAG Assistant.

Run with:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import time

import streamlit as st

from hw3.config import DEFAULT_PEOPLE, DEFAULT_PLACES
from hw3.ingestor import build_chunks, build_corpus, initialize_registry, load_chunks, load_pages
from hw3.rag import LocalRAGAssistant
from hw3.vector_store import VectorManager

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="WikiRAG — Local Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark background */
    .stApp {
        background: linear-gradient(135deg, #0f1123 0%, #171d36 50%, #10162a 100%);
        color: #ffffff; /* Brighter base text */
    }

    /* Make Streamlit default header transparent instead of hiding it (keeps sidebar toggle visible) */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .stAppHeader {
        background: transparent !important;
    }
    footer {
        display: none !important;
    }
    
    /* Fix the white bottom block behind the chat input for ALL Streamlit versions aggressively */
    .stChatFloatingInputContainer,
    .stChatInputContainer,
    [data-testid="stBottomBlock"], 
    [data-testid="stBottom"],
    [data-testid="stBottom"] > div,
    .stAppBottomBlock,
    div[data-testid="stBottomBlockContainer"] {
        background: transparent !important;
        background-color: transparent !important;
    }

    /* Header gradient */
    .wiki-header {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.4rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        margin-bottom: 0.2rem;
    }

    .wiki-subtitle {
        color: #cbd5e1; /* Much brighter subtitle */
        font-size: 0.95rem;
        font-weight: 400;
        letter-spacing: 0.04em;
        margin-bottom: 1.5rem;
    }

    /* Sidebar - Glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(30, 41, 59, 0.6) !important; /* Lighter, more modern slate */
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #f1f5f9 !important; /* Very bright for sidebar */
    }

    [data-testid="stSidebar"] .stMarkdown p {
        color: #f1f5f9 !important; 
        font-size: 0.85rem;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 0.75rem;
    }

    [data-testid="metric-container"] label {
        color: #94a3b8 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #a78bfa !important;
        font-weight: 600;
    }

    /* Chat messages - Glassmorphism */
    [data-testid="stChatMessage"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px;
        margin-bottom: 0.75rem;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        color: #ffffff !important;
    }
    
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] a {
        color: #ffffff !important; /* Force pure white for ALL text including bullets */
        line-height: 1.6;
    }

    /* User message accent */
    [data-testid="stChatMessage"][data-testid*="user"] {
        border-left: 3px solid #6366f1;
    }

    /* Assistant message accent */
    [data-testid="stChatMessage"][data-testid*="assistant"] {
        border-left: 3px solid #8b5cf6;
    }

    /* Chat input - Glassmorphism */
    [data-testid="stChatInput"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border-radius: 14px !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    [data-testid="stChatInputTextArea"] {
        color: #ffffff !important;
        background: transparent !important;
    }

    [data-testid="stChatInput"] * {
        color: #ffffff !important;
    }

    /* Remove ugly double focus outlines */
    [data-testid="stChatInputTextArea"]:focus {
        border-color: transparent !important;
        box-shadow: none !important;
    }

    /* Latency badge */
    .latency-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(17, 24, 39, 0.8);
        border: 1px solid #1e293b;
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        color: #64748b;
        margin-top: 0.5rem;
    }

    .latency-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #6366f1;
        display: inline-block;
    }

    /* Source card */
    .source-card {
        background: rgba(99, 102, 241, 0.06);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 10px;
        padding: 0.6rem 0.9rem;
        margin: 0.3rem 0;
    }

    .source-title {
        color: #a78bfa;
        font-weight: 500;
        font-size: 0.85rem;
    }

    .source-url {
        color: #475569;
        font-size: 0.72rem;
    }

    .source-badge {
        display: inline-block;
        padding: 0.1rem 0.5rem;
        border-radius: 8px;
        font-size: 0.7rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .badge-person {
        background: rgba(99, 102, 241, 0.15);
        color: #a78bfa;
    }

    .badge-place {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
    }

    /* Status indicators */
    .status-ok {
        color: #34d399;
    }

    .status-warn {
        color: #fbbf24;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35) !important;
    }

    /* Expander (e.g. '5 sources used') fixes */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.03) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    [data-testid="stExpander"] details, 
    [data-testid="stExpander"] summary {
        background: transparent !important;
        background-color: transparent !important;
    }

    [data-testid="stExpander"] summary:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #ffffff !important;
    }

    [data-testid="stExpanderDetails"] {
        background: transparent !important;
    }

    /* Dividers */
    hr {
        border-color: #1e293b !important;
    }

    /* Expander */
    [data-testid="stExpander"] {
        background: rgba(17, 24, 39, 0.5);
        border: 1px solid #1e293b;
        border-radius: 10px;
    }

    /* Spinner */
    [data-testid="stSpinner"] {
        color: #6366f1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Cached resources ─────────────────────────────────────────────────────────

@st.cache_resource
def get_vector_manager() -> VectorManager:
    return VectorManager()


@st.cache_resource
def get_assistant() -> LocalRAGAssistant:
    return LocalRAGAssistant(get_vector_manager())


# ── Index helpers ─────────────────────────────────────────────────────────────

def get_index_stats() -> dict[str, int]:
    initialize_registry()
    pages = load_pages()
    chunks = load_chunks()
    vm = get_vector_manager()
    vec_count = vm.collection.count()
    return {
        "pages": len(pages),
        "chunks": len(chunks),
        "vectors": vec_count,
        "people": sum(1 for p in pages if p.category == "person"),
        "places": sum(1 for p in pages if p.category == "place"),
    }


def build_demo_index() -> dict[str, int]:
    """Re-embed all pages already in SQLite into Chroma. Only fetches from Wikipedia if SQLite is empty."""
    initialize_registry()
    pages = load_pages()

    if not pages:
        # SQLite is empty — fetch from Wikipedia (first-time setup)
        pages = build_corpus()
        build_chunks(pages)

    chunks = load_chunks()
    vector_manager = get_vector_manager()
    vector_manager.reset()
    vector_manager.upsert_chunks(chunks)
    return {"pages": len(pages), "chunks": len(chunks)}


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### WikiRAG")
    st.markdown("*Local Wikipedia RAG Assistant*")
    st.divider()

    # Index stats
    stats = get_index_stats()
    is_ready = stats["pages"] >= 40 and stats["vectors"] > 0

    if is_ready:
        st.markdown('<span class="status-ok">● Index Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-warn">⚠ Index not built</span>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Pages", stats["pages"])
        st.metric("Vectors", stats["vectors"])
    with col2:
        st.metric("People", stats["people"])
        st.metric("Places", stats["places"])

    st.metric("Chunks", stats["chunks"])

    colA, colB = st.columns(2)
    with colA:
        with st.popover(":material/person: People", use_container_width=True):
            st.markdown(
                "<div style='max-height: 300px; overflow-y: auto;'>", 
                unsafe_allow_html=True
            )
            for p in DEFAULT_PEOPLE:
                st.write(f"• {p}")
            st.markdown("</div>", unsafe_allow_html=True)
            
    with colB:
        with st.popover(":material/place: Places", use_container_width=True):
            st.markdown(
                "<div style='max-height: 300px; overflow-y: auto;'>", 
                unsafe_allow_html=True
            )
            for p in DEFAULT_PLACES:
                st.write(f"• {p}")
            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    st.markdown("**Index Controls**")
    st.caption("Re-embed existing SQLite data into Chroma. Fetches Wikipedia only if index is empty.")

    if st.button(":material/sync: Rebuild Vector Index", use_container_width=True):
        with st.spinner("Re-embedding into Chroma..."):
            new_stats = build_demo_index()
        st.success(
            f"Done! {new_stats['pages']} pages, {new_stats['chunks']} chunks indexed."
        )
        st.rerun()

    st.divider()

    st.markdown("**Local Stack**")
    st.caption("LLM: llama3.2 (Ollama)")
    st.caption("Embeds: mxbai-embed-large")
    st.caption("Vector DB: ChromaDB (persistent)")
    st.caption("Registry: SQLite")
    st.caption("100% local — no external API calls")

    st.divider()

    if st.button(":material/delete: Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ── Main area ─────────────────────────────────────────────────────────────────

st.markdown('<div class="wiki-header">WikiRAG</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="wiki-subtitle">LOCAL WIKIPEDIA RAG &nbsp;·&nbsp; OLLAMA + CHROMA + SQLITE &nbsp;·&nbsp; '
    'OPTION B METADATA FILTERING &nbsp;·&nbsp; "I DON\'T KNOW" FALLBACK</div>',
    unsafe_allow_html=True,
)

if not is_ready:
    st.warning(
        "⚠️ **Index not ready.** Click **Build / Rebuild Index** in the sidebar to fetch Wikipedia "
        "data and build the vector index before asking questions.",
        icon="⚠️",
    )

# ── Chat history ──────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            r_lat = message.get("retrieval_latency", 0.0)
            g_lat = message.get("generation_latency", 0.0)
            st.markdown(
                f'<div class="latency-badge">'
                f'<span class="latency-dot"></span>'
                f"Retrieval: <strong>{r_lat:.2f}s</strong>&nbsp;&nbsp;"
                f'<span class="latency-dot" style="background:#8b5cf6"></span>'
                f"Generation: <strong>{g_lat:.2f}s</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if message.get("sources"):
                with st.expander(f":material/library_books: {len(message['sources'])} source(s) used"):
                    for src in message["sources"]:
                        badge_cls = "badge-person" if src["category"] == "person" else "badge-place"
                        icon = "👤" if src["category"] == "person" else "📍"
                        st.markdown(
                            f'<div class="source-card">'
                            f'<span class="source-badge {badge_cls}">{icon} {src["category"]}</span>'
                            f'&nbsp;&nbsp;<span class="source-title">{src["title"]}</span><br>'
                            f'<span class="source-url">{src["source_url"]}</span>'
                            f"</div>",
                            unsafe_allow_html=True,
                        )


# ── Chat input ────────────────────────────────────────────────────────────────

assistant = get_assistant()
prompt = st.chat_input("Ask about a famous person or place…", disabled=not is_ready)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        final_payload: dict | None = None
        streamed_text = ""

        for event in assistant.stream_answer(prompt):
            if event["type"] == "chunk":
                streamed_text += event["chunk"]
                placeholder.markdown(streamed_text + "▌")
            else:
                final_payload = event
                placeholder.markdown(final_payload["answer"])

        if final_payload is not None:
            r_lat = final_payload["retrieval_latency"]
            g_lat = final_payload["generation_latency"]
            st.markdown(
                f'<div class="latency-badge">'
                f'<span class="latency-dot"></span>'
                f"Retrieval: <strong>{r_lat:.2f}s</strong>&nbsp;&nbsp;"
                f'<span class="latency-dot" style="background:#8b5cf6"></span>'
                f"Generation: <strong>{g_lat:.2f}s</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )

            raw_sources = final_payload.get("sources", [])
            if raw_sources:
                with st.expander(f"📚 {len(raw_sources)} source(s) used"):
                    for src in raw_sources:
                        badge_cls = "badge-person" if src.category == "person" else "badge-place"
                        icon = "👤" if src.category == "person" else "📍"
                        st.markdown(
                            f'<div class="source-card">'
                            f'<span class="source-badge {badge_cls}">{icon} {src.category}</span>'
                            f'&nbsp;&nbsp;<span class="source-title">{src.title}</span><br>'
                            f'<span class="source-url">{src.source_url}</span>'
                            f"</div>",
                            unsafe_allow_html=True,
                        )

        if final_payload is not None:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": final_payload["answer"],
                    "retrieval_latency": final_payload["retrieval_latency"],
                    "generation_latency": final_payload["generation_latency"],
                    "sources": [
                        {
                            "title": s.title,
                            "category": s.category,
                            "source_url": s.source_url,
                        }
                        for s in final_payload.get("sources", [])
                    ],
                }
            )
