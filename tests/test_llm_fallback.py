"""LLM fallback architecture tests."""

from llm import fallback


def test_fallback_module_is_available() -> None:
    assert fallback.__doc__
