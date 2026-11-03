"""Retrieved-result reranking."""

from functools import lru_cache
from typing import Any

from langchain_core.documents import Document


def rerank_documents(
    question: str, matches: list[tuple[Document, float]], model_name: str
) -> list[Document]:
    if not matches:
        return []
    pairs = [(question, document.page_content) for document, _ in matches]
    scores = _get_reranker(model_name).predict(pairs)
    ranked = sorted(
        zip(matches, scores),
        key=lambda result: float(result[1]),
        reverse=True,
    )
    return [document for (document, _), _ in ranked]


@lru_cache(maxsize=2)
def _get_reranker(model_name: str) -> Any:
    from sentence_transformers import CrossEncoder

    return CrossEncoder(model_name)
