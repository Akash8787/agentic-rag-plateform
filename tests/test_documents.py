"""Document API architecture tests."""

from api.document_routes import document_bp


def test_document_blueprint_uses_api_prefix() -> None:
    assert document_bp.url_prefix == "/api/documents"
