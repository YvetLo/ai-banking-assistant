"""
Knowledge Base Index Builder
Reads Markdown FAQ files from data/knowledge_base/, chunks text,
generates embeddings via sentence-transformers, and saves FAISS indexes.

Usage:
    python backend/src/rag/build_index.py

Outputs:
    data/faiss_index/zh.index   — Chinese FAISS index
    data/faiss_index/en.index   — English FAISS index
    data/faiss_index/zh_meta.json  — chunk metadata (source file, text)
    data/faiss_index/en_meta.json

NOTE: This script is a placeholder stub for Sprint 5.
      Full implementation will be added in Sprint 5 when RAG is introduced.
      Sprint 1-4 use Context Stuffing instead (see ADR.md for rationale).
"""

# ── Dependencies (install before running) ────────────────────────────────────
# pip install sentence-transformers faiss-cpu langdetect

import json
import os
from pathlib import Path

# Sprint 5: uncomment these imports
# import faiss
# import numpy as np
# from sentence_transformers import SentenceTransformer

# ── Config ────────────────────────────────────────────────────────────────────
KB_DIR = Path("data/knowledge_base")
INDEX_DIR = Path("data/faiss_index")
EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"
CHUNK_SIZE = 400        # tokens (approximate by words)
CHUNK_OVERLAP = 80
TOP_K = 3
SIMILARITY_THRESHOLD = 0.7


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def load_documents(language: str) -> list[dict]:
    """Load all Markdown files for a given language ('zh' or 'en')."""
    lang_dir = KB_DIR / language
    documents = []

    for md_file in sorted(lang_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            documents.append({
                "source": md_file.name,
                "chunk_id": i,
                "text": chunk,
                "language": language,
            })

    return documents


def build_index(language: str) -> None:
    """Build FAISS index for the specified language. Sprint 5 placeholder."""
    print(f"\n[build_index] Building index for language: {language}")
    documents = load_documents(language)
    print(f"  Loaded {len(documents)} chunks from {KB_DIR / language}")

    # Sprint 5 TODO: generate embeddings and build FAISS index
    # model = SentenceTransformer(EMBEDDING_MODEL)
    # texts = [doc["text"] for doc in documents]
    # embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    # embeddings_np = np.array(embeddings).astype("float32")
    # dimension = embeddings_np.shape[1]
    # index = faiss.IndexFlatL2(dimension)
    # index.add(embeddings_np)
    # INDEX_DIR.mkdir(parents=True, exist_ok=True)
    # faiss.write_index(index, str(INDEX_DIR / f"{language}.index"))
    # meta_path = INDEX_DIR / f"{language}_meta.json"
    # meta_path.write_text(json.dumps(documents, ensure_ascii=False, indent=2), encoding="utf-8")
    # print(f"  Index saved to {INDEX_DIR / f'{language}.index'}")

    # Placeholder output for Sprint 1-4
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    placeholder = {
        "status": "placeholder",
        "sprint": "This index will be built in Sprint 5",
        "document_count": len(documents),
        "language": language,
        "model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
    }
    meta_path = INDEX_DIR / f"{language}_meta_placeholder.json"
    meta_path.write_text(json.dumps(placeholder, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Placeholder metadata saved to {meta_path}")


def main():
    print("=" * 60)
    print("  AI Banking Assistant — Knowledge Base Index Builder")
    print("  Status: Sprint 5 Placeholder")
    print("=" * 60)

    if not KB_DIR.exists():
        print(f"ERROR: Knowledge base directory not found: {KB_DIR}")
        print("  Run this script from the project root directory.")
        return

    for lang in ["zh", "en"]:
        lang_dir = KB_DIR / lang
        if not lang_dir.exists():
            print(f"WARNING: {lang_dir} not found, skipping.")
            continue
        build_index(lang)

    print("\nDone. Sprint 5 will replace placeholders with real FAISS indexes.")


if __name__ == "__main__":
    main()
