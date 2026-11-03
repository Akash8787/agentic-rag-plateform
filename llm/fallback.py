"""Groq-backed answer generation, including no-document fallback."""

from llm.model_factory import get_groq_client


def generate_completion(prompt: str) -> str:
    completion = get_groq_client().chat.completions.create(
        model=_model_name(),
        messages=[{"role": "user", "content": prompt}],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )
    answer = []
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            answer.append(chunk.choices[0].delta.content)
    result = "".join(answer).strip()
    if not result:
        raise RuntimeError("The language model returned an empty response")
    return result


def _model_name() -> str:
    from flask import current_app

    return current_app.config["GROQ_MODEL"]
