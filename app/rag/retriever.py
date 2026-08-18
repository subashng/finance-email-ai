from pathlib import Path
import json

import faiss
from sentence_transformers import SentenceTransformer


BASE_DIR = Path(__file__).resolve().parents[2]

INDEX_PATH = BASE_DIR / "data" / "rag" / "finance_policy.index"
METADATA_PATH = BASE_DIR / "data" / "rag" / "metadata.json"

MODEL_NAME = "all-MiniLM-L6-v2"


class FinancePolicyRetriever:
    def __init__(self):
        if not INDEX_PATH.exists():
            raise FileNotFoundError(
                f"FAISS index not found: {INDEX_PATH}"
            )

        if not METADATA_PATH.exists():
            raise FileNotFoundError(
                f"Metadata not found: {METADATA_PATH}"
            )

        self.model = SentenceTransformer(MODEL_NAME)

        self.index = faiss.read_index(
            str(INDEX_PATH)
        )

        self.metadata = json.loads(
            METADATA_PATH.read_text(
                encoding="utf-8"
            )
        )

    def search(
        self,
        query: str,
        top_k: int = 3,
    ):
        if not query or not query.strip():
            return []

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        scores, indices = self.index.search(
            query_embedding,
            min(top_k, self.index.ntotal),
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):
            if index < 0:
                continue

            metadata = self.metadata[index]

            results.append(
                {
                    "score": float(score),
                    "chunk_id": metadata["chunk_id"],
                    "source": metadata["source"],
                    "text": metadata["text"],
                }
            )

        return results


def main():
    print("=" * 60)
    print("FINANCE POLICY RAG RETRIEVAL TEST")
    print("=" * 60)

    retriever = FinancePolicyRetriever()

    queries = [
        "What are the standard payment terms?",
        "What happens when an invoice becomes overdue?",
        "How should a customer dispute an invoice?",
        "What information should customer support verify before responding?",
    ]

    for query in queries:
        print()
        print("-" * 60)
        print(f"QUERY: {query}")
        print("-" * 60)

        results = retriever.search(
            query,
            top_k=2,
        )

        for position, result in enumerate(
            results,
            start=1,
        ):
            print(
                f"\nResult {position}"
            )
            print(
                f"Score:  {result['score']:.4f}"
            )
            print(
                f"Source: {result['source']}"
            )
            print(
                f"Chunk:  {result['chunk_id']}"
            )
            print(
                f"Text:   {result['text'][:500]}"
            )


if __name__ == "__main__":
    main()