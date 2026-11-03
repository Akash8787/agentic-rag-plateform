"""Tavily web search tool tests."""

import pytest

from agents.tools.web_search import search_web


def test_search_web_formats_results_and_returns_urls(monkeypatch) -> None:
    class FakeTavilyClient:
        def search(self, **kwargs):
            assert kwargs == {
                "query": "latest weather",
                "search_depth": "basic",
                "max_results": 5,
                "include_answer": False,
            }
            return {
                "results": [
                    {
                        "title": "Weather",
                        "url": "https://example.com/weather",
                        "content": "Current forecast details",
                    },
                    {"title": "Incomplete result", "url": "", "content": "ignored"},
                ]
            }

    monkeypatch.setattr(
        "agents.tools.web_search._get_client",
        lambda api_key: FakeTavilyClient(),
    )

    contexts, sources = search_web("latest weather", "test-key")

    assert contexts == [
        "Title: Weather\nURL: https://example.com/weather\nContent: Current forecast details"
    ]
    assert sources == ["https://example.com/weather"]


def test_search_web_requires_api_key() -> None:
    with pytest.raises(RuntimeError, match="TAVILY_API_KEY"):
        search_web("latest weather", None)


def test_search_web_rejects_empty_query() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        search_web(" ", "test-key")
