"""Answer generation using retrieved context and conversation history."""

import re

from llm.fallback import generate_completion
from prompts import load_prompt


def generate_answer(
    question: str, context: list[str], history: list[str], strict: bool
) -> str:
    template = load_prompt(strict)
    prompt = template.format(
        context="\n\n".join(context),
        history="\n".join(history),
        question=question,
        input=question,
    )
    answer = generate_completion(prompt)
    return re.sub(r"^According to[^,.]+[,.]\s*", "", answer).strip()
