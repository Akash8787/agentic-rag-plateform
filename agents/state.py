"""Shared state types for agent workflows."""

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """Data passed between nodes in an agent workflow."""

    question: str
    user_code: str
    token: str
    strict: bool
    web_search: bool
    history: list[str]
    context: list[str]
    sources: list[str]
    answer: str
