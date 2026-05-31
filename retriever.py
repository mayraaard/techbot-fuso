"""
retriever.py — Load ChromaDB + BM25, bangun EnsembleRetriever.
Di-import oleh llm.py dan app.py. Tidak menjalankan ingest.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_classic.retrievers import EnsembleRetriever

load_dotenv()

CHROMA_DIR = "chroma_db"
BM25_CHUNKS_FILE = "bm25_chunks.json"
EMBED_MODEL = "gemini-embedding-001"
K = 4


# ─── Loaders ──────────────────────────────────────────────────────────────────

def load_vectorstore() -> Chroma:
    """Load ChromaDB yang sudah ada dari chroma_db/."""
    if not Path(CHROMA_DIR).exists():
        raise FileNotFoundError(
            f"Folder '{CHROMA_DIR}/' tidak ditemukan. "
            "Jalankan ingest.py terlebih dahulu lalu commit hasilnya ke GitHub."
        )

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY tidak ditemukan. "
            "Set di file .env atau Streamlit Cloud Secrets."
        )

    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBED_MODEL,
        google_api_key=api_key,
    )
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )


def load_bm25_retriever() -> BM25Retriever:
    """Load bm25_chunks.json dan rebuild BM25Retriever dari Document objects."""
    if not Path(BM25_CHUNKS_FILE).exists():
        raise FileNotFoundError(
            f"File '{BM25_CHUNKS_FILE}' tidak ditemukan. "
            "Jalankan ingest.py terlebih dahulu."
        )

    with open(BM25_CHUNKS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    docs = [
        Document(page_content=item["page_content"], metadata=item["metadata"])
        for item in data
    ]

    retriever = BM25Retriever.from_documents(docs)
    retriever.k = K
    return retriever


# ─── Ensemble Retriever ───────────────────────────────────────────────────────

def get_ensemble_retriever() -> EnsembleRetriever:
    """Gabungkan ChromaDB (semantic) + BM25 (keyword) dengan weights 50/50."""
    vectorstore = load_vectorstore()
    chroma_retriever = vectorstore.as_retriever(search_kwargs={"k": K})

    bm25_retriever = load_bm25_retriever()

    return EnsembleRetriever(
        retrievers=[bm25_retriever, chroma_retriever],
        weights=[0.5, 0.5],
    )


# ─── Format Sources ───────────────────────────────────────────────────────────

import re  # tambahkan di bagian import atas retriever.py jika belum ada

def format_sources(docs: list[Document]) -> list[str]:
    """Format metadata dokumen hasil retrieval untuk ditampilkan di Streamlit.

    Siap di-loop dengan: st.markdown(f"• {s}")
    Deduplikasi berdasarkan source — satu file tampil sekali.
    """
    seen: set[str] = set()
    result: list[str] = []

    for doc in docs:
        meta = doc.metadata
        source = meta.get("source", "")

        if source in seen:
            continue
        seen.add(source)

        doc_type = meta.get("doc_type", "")
        vehicle_model = meta.get("vehicle_model", "")

        if doc_type == "case_report":
            chunk_id = meta.get("chunk_id", "")
            case_num = chunk_id[-2:] if len(chunk_id) >= 2 else chunk_id
            source_stem = Path(source).stem if source else source
            # Strip prefix "case_04_", replace underscore, title case
            clean = re.sub(r'^case_\d+_', '', source_stem)
            clean = clean.replace('_', ' ').title()
            result.append(f"Case #{case_num} — {clean} ({vehicle_model})")

        elif doc_type in ("sop", "troubleshooting"):
            section = meta.get("section", "")
            result.append(f"{doc_type.title()} {vehicle_model} → {section}")

        else:
            result.append(source)

    return result

# ─── Test ─────────────────────────────────────────────────────────────────────

def test_retriever() -> None:
    query = "Fighter overheat di tanjakan panjang, radiator normal"
    print(f"Query  : {query}")
    print("-" * 60)

    retriever = get_ensemble_retriever()
    results = retriever.invoke(query)

    print(f"Hasil  : {len(results)} dokumen\n")
    for i, doc in enumerate(results, 1):
        meta = doc.metadata
        preview = doc.page_content[:200].replace("\n", " ")
        print(
            f"[{i}] source   : {meta.get('source', '-')}\n"
            f"     doc_type  : {meta.get('doc_type', '-')}\n"
            f"     chunk_id  : {meta.get('chunk_id', '-')}\n"
            f"     vehicle   : {meta.get('vehicle_model', '-')}\n"
            f"     preview   : {preview}...\n"
        )

    print("Format sources:")
    for s in format_sources(results):
        print(f"  • {s}")


if __name__ == "__main__":
    test_retriever()
