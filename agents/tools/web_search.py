"""Tavily web search for questions that need current external information."""

from functools import lru_cache
from typing import Any, Optional


def search_web(
    query: str, api_key: Optional[str], max_results: int = 5
) -> tuple[list[str], list[str]]:
    """Return formatted search snippets and their source URLs."""
    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is required when web search is requested"
        )
    if not query.strip():
        raise ValueError("Web search query must not be empty")

    response = _get_client(api_key).search(
        query=query,
        search_depth="basic",
        max_results=max_results,
        include_answer=False,
    )
    contexts = []
    sources = []
    for result in response.get("results", []):
        title = str(result.get("title") or "Web result").strip()
        url = str(result.get("url") or "").strip()
        content = str(result.get("content") or "").strip()
        if not url or not content:
            continue
        contexts.append(f"Title: {title}\nURL: {url}\nContent: {content}")
        sources.append(url)
    return contexts, sources


@lru_cache(maxsize=4)
def _get_client(api_key: str) -> Any:
    from tavily import TavilyClient

    return TavilyClient(api_key=api_key)
