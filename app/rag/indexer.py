from pathlib import Path
import json

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parents[2]

KNOWLEDGE_DIR = BASE_DIR / "data" / "knowledge"
RAG_DATA_DIR = BASE_DIR / "data" / "rag"

INDEX_PATH = RAG_DATA_DIR / "finance_policy.index"
METADATA_PATH = RAG_DATA_DIR / "metadata.json"

MODEL_NAME = "all-MiniLM-L6-v2"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 150


def load_documents():
    documents = []

    for file_path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        text = file_path.read_text(encoding="utf-8").strip()

        if not text:
            continue

        documents.append(
            {
                "source": file_path.name,
                "text": text,
            }
        )

    if not documents:
        raise RuntimeError(
            f"No knowledge documents found in {KNOWLEDGE_DIR}"
        )

    return documents


def chunk_text(text: str):
    words = text.split()

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + CHUNK_SIZE, len(words))

        chunk = " ".join(words[start:end]).strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def build_chunks(documents):
    chunks = []

    for document in documents:
        document_chunks = chunk_text(document["text"])

        for index, chunk in enumerate(document_chunks):
            chunks.append(
                {
                    "chunk_id": f"{document['source']}::{index}",
                    "source": document["source"],
                    "text": chunk,
                }
            )

    return chunks


def build_index(chunks):
    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]

    print(f"Generating embeddings for {len(texts)} chunks...")

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    embeddings = embeddings.astype("float32")

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return index


def save_index(index, chunks):
    RAG_DATA_DIR.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(INDEX_PATH))

    METADATA_PATH.write_text(
        json.dumps(
            chunks,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def main():
    print("=" * 60)
    print("FINANCE POLICY RAG INDEXER")
    print("=" * 60)

    documents = load_documents()

    print(f"Documents loaded: {len(documents)}")

    for document in documents:
        print(f"  ✓ {document['source']}")

    chunks = build_chunks(documents)

    print(f"Total chunks created: {len(chunks)}")

    index = build_index(chunks)

    save_index(index, chunks)

    print()
    print("RAG index created successfully.")
    print(f"FAISS index: {INDEX_PATH}")
    print(f"Metadata:    {METADATA_PATH}")
    print(f"Vector count: {index.ntotal}")
    print(f"Vector dimension: {index.d}")


if __name__ == "__main__":
    main()