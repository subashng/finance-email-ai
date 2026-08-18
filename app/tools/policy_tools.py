from typing import Any

from app.rag.retriever import FinancePolicyRetriever


_retriever = FinancePolicyRetriever()


def search_finance_policy(
    query: str,
    top_k: int = 3,
) -> dict[str, Any]:
    """
    Search approved finance policy documents.

    This is a read-only RAG operation.

    Returns:
    - FOUND when relevant policy context is retrieved
    - NOT_FOUND when no usable context is available
    """

    if not query or not query.strip():
        return {
            "status": "NOT_FOUND",
            "message": "Policy search query was not provided.",
            "results": [],
        }

    results = _retriever.search(
        query=query.strip(),
        top_k=top_k,
    )

    if not results:
        return {
            "status": "NOT_FOUND",
            "message": "No relevant finance policy information was found.",
            "results": [],
        }

    formatted_results = [
        {
            "source": result["source"],
            "chunk_id": result["chunk_id"],
            "score": round(result["score"], 4),
            "text": result["text"],
        }
        for result in results
    ]

    return {
        "status": "FOUND",
        "message": (
            f"{len(formatted_results)} relevant "
            "policy result(s) found."
        ),
        "results": formatted_results,
    }