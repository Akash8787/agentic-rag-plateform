"""Conversation memory architecture tests."""

from services import memory_service


def test_memory_service_module_is_available() -> None:
    assert memory_service.__doc__
