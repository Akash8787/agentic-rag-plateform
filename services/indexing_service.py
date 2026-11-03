"""FAISS vector index creation and persistence."""

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from services.chunking_service import chunk_documents
from services.embedding_service import get_embeddings


def create_index(documents: list[Document], model_name: str) -> FAISS:
    chunks = chunk_documents(documents)
    if not chunks:
        raise ValueError("No searchable text was extracted from the document")
    return FAISS.from_documents(chunks, get_embeddings(model_name))


def save_index(documents: list[Document], index_path: Path, model_name: str) -> int:
    index = create_index(documents, model_name)
    index_path.mkdir(parents=True, exist_ok=True)
    index.save_local(str(index_path))
    return len(index.index_to_docstore_id)
