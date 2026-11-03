"""Application factory smoke tests."""

from app import create_app


def test_create_app_registers_api_blueprints() -> None:
    app = create_app({"TESTING": True})

    assert {
        "documents",
        "chat",
        "agents",
        "conversations",
    }.issubset(app.blueprints)
