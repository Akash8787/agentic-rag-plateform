"""Prompt loading helpers."""

from pathlib import Path


def load_prompt(strict: bool = True) -> str:
    prompt_name = "rag_prompt.txt" if strict else "fallback_prompt.txt"
    prompt_path = Path(__file__).with_name(prompt_name)
    return prompt_path.read_text(encoding="utf-8")
