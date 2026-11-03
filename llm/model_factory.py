"""Lazy construction of external model clients."""

from functools import lru_cache
from typing import Any


def get_groq_client() -> Any:
    from flask import current_app

    api_key = current_app.config.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is required to generate answers")
    return _create_groq_client(api_key)


@lru_cache(maxsize=4)
def _create_groq_client(api_key: str) -> Any:
    from groq import Groq

    return Groq(api_key=api_key)
