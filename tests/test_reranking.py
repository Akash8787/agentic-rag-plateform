"""Document reranking behavior tests."""

from langchain_core.documents import Document

from services.reranking_service import rerank_documents


def test_reranker_returns_documents_in_model_score_order(monkeypatch) -> None:
    first = Document(page_content="first")
    second = Document(page_content="second")

    class FakeReranker:
        def predict(self, pairs):
            assert pairs == [("question", "first"), ("question", "second")]
            return [0.1, 0.9]

    monkeypatch.setattr(
        "services.reranking_service._get_reranker",
        lambda model_name: FakeReranker(),
    )

    results = rerank_documents(
        "question", [(first, 0.4), (second, 0.2)], "test-model"
    )

    assert results == [second, first]
