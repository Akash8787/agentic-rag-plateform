"""API compatibility and request validation tests."""

from pathlib import Path

from app import create_app


def test_app_registers_platform_and_legacy_routes(tmp_path: Path) -> None:
    app = create_app(
        {
            "TESTING": True,
            "UPLOAD_DIR": tmp_path / "uploads",
            "INDEX_DIR": tmp_path / "indexes",
        }
    )
    paths = {rule.rule for rule in app.url_map.iter_rules()}

    assert {
        "/api/documents",
        "/api/documents/upload",
        "/api/chat",
        "/api/agents/run",
        "/api/conversations",
        "/upload_pdf",
        "/ask_question",
        "/delete_pdf",
        "/health",
    }.issubset(paths)


def test_health_endpoint_returns_ok(tmp_path: Path) -> None:
    app = create_app(
        {
            "TESTING": True,
            "UPLOAD_DIR": tmp_path / "uploads",
            "INDEX_DIR": tmp_path / "indexes",
        }
    )

    response = app.test_client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_upload_rejects_unsafe_scope_without_writing_files(tmp_path: Path) -> None:
    app = create_app(
        {
            "TESTING": True,
            "UPLOAD_DIR": tmp_path / "uploads",
            "INDEX_DIR": tmp_path / "indexes",
        }
    )

    response = app.test_client().post(
        "/api/documents",
        json={
            "User_Code": "../outside",
            "Token": "token",
            "pdf_base64": "dGVzdA==",
            "filename": "notes",
            "file_extension": ".txt",
        },
    )

    assert response.status_code == 400
    assert not (tmp_path / "uploads").exists()


def test_legacy_question_route_keeps_request_and_response_shape(monkeypatch, tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "UPLOAD_DIR": tmp_path / "uploads",
            "INDEX_DIR": tmp_path / "indexes",
        }
    )
    monkeypatch.setattr(
        "api.chat_routes.run_agent",
        lambda *args: {"answer": "Test answer", "sources": ["notes.txt"]},
    )

    response = app.test_client().post(
        "/ask_question",
        json={
            "User_Code": "C1001",
            "Token": "TXT",
            "User_Token": "01",
            "Question": "Test question",
            "Condition": True,
        },
    )

    assert response.status_code == 200
    assert response.get_json()["answer"] == "Test answer"
    assert response.get_json()["sources"] == ["notes.txt"]


def test_chat_route_rejects_web_search_without_tavily_key(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "UPLOAD_DIR": tmp_path / "uploads",
            "INDEX_DIR": tmp_path / "indexes",
            "TAVILY_API_KEY": None,
        }
    )

    response = app.test_client().post(
        "/api/chat/ask",
        json={
            "User_Code": "C1001",
            "Token": "TXT",
            "User_Token": "01",
            "Question": "Latest news",
            "Condition": False,
            "Web_Search": True,
        },
    )

    assert response.status_code == 400
    assert "TAVILY_API_KEY" in response.get_json()["message"]


def test_chat_route_rejects_web_search_in_strict_mode(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "UPLOAD_DIR": tmp_path / "uploads",
            "INDEX_DIR": tmp_path / "indexes",
            "TAVILY_API_KEY": "test-key",
        }
    )

    response = app.test_client().post(
        "/api/chat/ask",
        json={
            "User_Code": "C1001",
            "Token": "TXT",
            "User_Token": "01",
            "Question": "Question",
            "Condition": True,
            "Web_Search": True,
        },
    )

    assert response.status_code == 400
    assert "Condition is true" in response.get_json()["message"]


def test_legacy_delete_route_returns_deletion_counts(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "UPLOAD_DIR": tmp_path / "uploads",
            "INDEX_DIR": tmp_path / "indexes",
        }
    )
    stored_file = tmp_path / "uploads" / "C1001" / "TXT" / "notes.txt"
    stored_index = tmp_path / "indexes" / "C1001" / "TXT" / "notes.txt"
    stored_file.parent.mkdir(parents=True)
    stored_index.mkdir(parents=True)
    stored_file.write_text("notes", encoding="utf-8")

    response = app.test_client().post(
        "/delete_pdf",
        json={"User_Code": "C1001", "Token": "TXT", "pdf_name": "notes.txt"},
    )

    assert response.status_code == 200
    assert response.get_json()["deleted_files"] == 1
    assert response.get_json()["deleted_indexes"] == 1
