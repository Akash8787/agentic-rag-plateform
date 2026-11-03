"""Knowledge retrieval from stored FAISS indexes."""

from pathlib import Path
from langchain_community.vectorstores import FAISS

from services.embedding_service import get_embeddings
from services.reranking_service import rerank_documents


def retrieve_documents(
    question: str,
    index_root: Path,
    user_code: str,
    token: str,
    embedding_model: str,
    reranker_model: str,
    *,
    max_indexes: int = 3,
    documents_per_index: int = 5,
) -> tuple[list[str], list[str]]:
    index_dir = index_root / user_code / token
    if not index_dir.is_dir():
        return [], []

    embeddings = get_embeddings(embedding_model)
    ranked_indexes: list[tuple[float, str, FAISS]] = []
    for path in index_dir.iterdir():
        if not path.is_dir() or not (path / "index.faiss").is_file():
            continue
        try:
            vector_store = FAISS.load_local(
                str(path), embeddings, allow_dangerous_deserialization=True
            )
            matches = vector_store.similarity_search_with_score(question, k=1)
            if matches:
                ranked_indexes.append((float(matches[0][1]), path.name, vector_store))
        except (OSError, ValueError, RuntimeError) as error:
            raise RuntimeError(f"Could not load document index '{path.name}'") from error

    if not ranked_indexes:
        return [], []

    ranked_indexes.sort(key=lambda result: result[0])
    threshold = ranked_indexes[0][0] * 1.1
    selected = [
        result for result in ranked_indexes if result[0] <= threshold
    ][:max_indexes]

    context: list[str] = []
    sources: list[str] = []
    for _, name, vector_store in selected:
        matches = vector_store.similarity_search_with_score(
            question, k=documents_per_index
        )
        documents = rerank_documents(question, matches, reranker_model)
        context.extend(document.page_content for document in documents)
        sources.append(name)
    return context, sources
