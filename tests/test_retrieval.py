"""Retrieval service architecture tests."""

from services import retrieval_service


def test_retrieval_service_module_is_available() -> None:
    assert retrieval_service.__doc__
