"""Thread-safe in-process conversation history."""

from threading import RLock

_history: dict[tuple[str, str, str, bool], list[str]] = {}
_lock = RLock()
_MAX_MESSAGES = 10


def get_history(session_key: tuple[str, str, str, bool]) -> list[str]:
    with _lock:
        return list(_history.get(session_key, []))


def append_exchange(
    session_key: tuple[str, str, str, bool], question: str, answer: str
) -> None:
    with _lock:
        messages = _history.setdefault(session_key, [])
        messages.extend((f"User: {question}", f"Assistant: {answer}"))
        _history[session_key] = messages[-_MAX_MESSAGES:]


def clear_history(session_key: tuple[str, str, str, bool]) -> None:
    with _lock:
        _history.pop(session_key, None)


def parse_condition(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off", ""}:
            return False
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    raise ValueError("Condition must be a boolean")
