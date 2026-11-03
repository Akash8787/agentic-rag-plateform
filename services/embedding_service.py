"""Local sentence-transformer embeddings."""

from functools import lru_cache
from typing import Any

from langchain_core.embeddings import Embeddings


class LocalEmbeddings(Embeddings):
    """Sentence-transformer embeddings with a CPU/GPU-aware device choice."""

    def __init__(self, model_name: str) -> None:
        import torch
        from sentence_transformers import SentenceTransformer

        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        prepared = []
        for text in texts:
            if ", " in text:
                columns = " ".join(
                    line.split(", ")[0].split(":")[0]
                    for line in text.splitlines()
                    if line
                )
                prepared.append(f"{columns} {text}")
            else:
                prepared.append(text)
        return self.model.encode(
            prepared, convert_to_tensor=False, show_progress_bar=False
        ).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode(
            text, convert_to_tensor=False, show_progress_bar=False
        ).tolist()


@lru_cache(maxsize=4)
def get_embeddings(model_name: str) -> LocalEmbeddings:
    """Load each configured embedding model only when first needed."""
    return LocalEmbeddings(model_name)
