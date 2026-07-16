"""
Knowledge Base Index Builder — Sprint 5
Reads Markdown FAQ files, chunks text, generates embeddings via
sentence-transformers, and saves FAISS indexes (one per language).

Usage (run from project root):
    python -m backend.src.rag.build_index

Outputs:
    data/faiss_index/zh.index        Chinese FAISS index (IndexFlatIP)
    data/faiss_index/en.index        English FAISS index
    data/faiss_index/zh_meta.json    chunk metadata (source, text, chunk_id)
    data/faiss_index/en_meta.json
"""

import json
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

KB_DIR = Path("data/knowledge_base")
INDEX_DIR = Path("data/faiss_index")
EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"
CHUNK_SIZE = 400   # words per chunk (approximate)
CHUNK_OVERLAP = 80


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunk = " ".join(words[start : start + chunk_size])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def load_documents(language: str) -> list[dict]:
    docs = []
    lang_dir = KB_DIR / language
    for md_file in sorted(lang_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        for i, chunk in enumerate(chunk_text(content)):
            docs.append({"source": md_file.name, "chunk_id": i, "text": chunk, "language": language})
    return docs


def build_index(language: str, model: SentenceTransformer) -> None:
    print(f"\n[build_index] Language: {language}")
    docs = load_documents(language)
    print(f"  {len(docs)} chunks loaded from {KB_DIR / language}")

    texts = [d["text"] for d in docs]
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    embeddings_np = np.array(embeddings).astype("float32")

    # IndexFlatIP + normalized vectors → cosine similarity scores (0–1)
    index = faiss.IndexFlatIP(embeddings_np.shape[1])
    index.add(embeddings_np)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_DIR / f"{language}.index"))
    meta_path = INDEX_DIR / f"{language}_meta.json"
    meta_path.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Saved: {INDEX_DIR / f'{language}.index'} ({index.ntotal} vectors, dim={embeddings_np.shape[1]})")


def main():
    print("=" * 60)
    print("  AI Banking Assistant — Knowledge Base Index Builder")
    print(f"  Model: {EMBEDDING_MODEL}")
    print("=" * 60)

    if not KB_DIR.exists():
        print(f"ERROR: {KB_DIR} not found. Run from project root.")
        return

    model = SentenceTransformer(EMBEDDING_MODEL)
    for lang in ["zh", "en"]:
        if not (KB_DIR / lang).exists():
            print(f"WARNING: {KB_DIR / lang} not found, skipping.")
            continue
        build_index(lang, model)

    print("\nDone. Index ready for Sprint 5 RAG retrieval.")


if __name__ == "__main__":
    main()
