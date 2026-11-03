"""Agent workflow architecture tests."""

from app import create_app
from agents.state import AgentState
from agents.graph import run_agent


def test_agent_state_exposes_workflow_fields() -> None:
    assert AgentState.__annotations__["question"] is str
    assert AgentState.__annotations__["answer"] is str


def test_agent_graph_connects_retrieval_and_answer_nodes(monkeypatch, tmp_path) -> None:
    app = create_app(
        {
            "TESTING": True,
            "INDEX_DIR": tmp_path / "indexes",
            "EMBEDDING_MODEL": "test-embedding",
            "RERANKER_MODEL": "test-reranker",
        }
    )
    events = []
    monkeypatch.setattr(
        "agents.graph.retrieve_documents",
        lambda *args: (events.append("retrieve") or ["context"], ["notes.txt"]),
    )
    monkeypatch.setattr(
        "agents.graph.generate_answer",
        lambda question, context, history, strict: (
            events.append("answer") or "grounded answer"
        ),
    )

    with app.app_context():
        result = run_agent("question", "user", "tenant", [], True)

    assert events == ["retrieve", "answer"]
    assert result == {"answer": "grounded answer", "sources": ["notes.txt"]}


def test_agent_graph_uses_tavily_for_explicit_web_search(
    monkeypatch, tmp_path
) -> None:
    app = create_app(
        {
            "TESTING": True,
            "INDEX_DIR": tmp_path / "indexes",
            "EMBEDDING_MODEL": "test-embedding",
            "RERANKER_MODEL": "test-reranker",
            "TAVILY_API_KEY": "test-key",
        }
    )
    events = []
    monkeypatch.setattr(
        "agents.graph.retrieve_documents",
        lambda *args: (["local context"], ["local.txt"]),
    )
    monkeypatch.setattr(
        "agents.graph.search_web",
        lambda query, api_key: (
            events.append((query, api_key)) or ["web context"],
            ["https://example.com"],
        ),
    )
    monkeypatch.setattr(
        "agents.graph.generate_answer",
        lambda question, context, history, strict: "\n".join(context),
    )

    with app.app_context():
        result = run_agent(
            "current question", "user", "tenant", [], False, web_search=True
        )

    assert events == [("current question", "test-key")]
    assert result == {
        "answer": "local context\nweb context",
        "sources": ["local.txt", "https://example.com"],
    }


def test_agent_graph_automatically_searches_when_no_local_context(
    monkeypatch, tmp_path
) -> None:
    app = create_app(
        {
            "TESTING": True,
            "INDEX_DIR": tmp_path / "indexes",
            "EMBEDDING_MODEL": "test-embedding",
            "RERANKER_MODEL": "test-reranker",
            "TAVILY_API_KEY": "test-key",
        }
    )
    events = []
    monkeypatch.setattr("agents.graph.retrieve_documents", lambda *args: ([], []))
    monkeypatch.setattr(
        "agents.graph.search_web",
        lambda query, api_key: (
            events.append((query, api_key)) or ["web context"],
            ["https://example.com"],
        ),
    )
    monkeypatch.setattr(
        "agents.graph.generate_answer",
        lambda question, context, history, strict: "\n".join(context),
    )

    with app.app_context():
        result = run_agent("question", "user", "tenant", [], False)

    assert events == [("question", "test-key")]
    assert result == {
        "answer": "web context",
        "sources": ["https://example.com"],
    }


def test_agent_graph_does_not_web_search_in_strict_mode(
    monkeypatch, tmp_path
) -> None:
    app = create_app(
        {
            "TESTING": True,
            "INDEX_DIR": tmp_path / "indexes",
            "EMBEDDING_MODEL": "test-embedding",
            "RERANKER_MODEL": "test-reranker",
            "TAVILY_API_KEY": "test-key",
        }
    )
    monkeypatch.setattr("agents.graph.retrieve_documents", lambda *args: ([], []))

    def unexpected_search(*args):
        raise AssertionError("strict mode must not use web search")

    monkeypatch.setattr("agents.graph.search_web", unexpected_search)
    monkeypatch.setattr(
        "agents.graph.generate_answer",
        lambda question, context, history, strict: "answer",
    )

    with app.app_context():
        result = run_agent(
            "question", "user", "tenant", [], True, web_search=False
        )

    assert result == {"answer": "answer", "sources": []}
