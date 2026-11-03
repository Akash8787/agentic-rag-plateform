"""Question-answering chat routes."""

from flask import Blueprint, current_app, jsonify, request

from agents.graph import run_agent
from services.document_service import validate_scope
from services.memory_service import append_exchange, get_history, parse_condition

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_bp.post("")
@chat_bp.post("/ask")
def ask_question():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "A JSON object is required", "answer": ""}), 400

    user_code = data.get("User_Code")
    token = data.get("Token")
    user_token = data.get("User_Token")
    question = data.get("Question")
    if not all((user_code, token, user_token, question)):
        return jsonify({"status": "error", "message": "Missing required fields", "answer": ""}), 400
    if not isinstance(question, str) or not question.strip():
        return jsonify({"status": "error", "message": "Question must be a non-empty string", "answer": ""}), 400
    try:
        validate_scope(str(user_code), str(token))
        validate_scope(str(user_code), str(user_token))
        strict = parse_condition(data.get("Condition", False))
        web_search = parse_condition(data.get("Web_Search", False))
        if strict and web_search:
            raise ValueError("Web_Search cannot be enabled when Condition is true")
        if web_search and not current_app.config.get("TAVILY_API_KEY"):
            raise ValueError("TAVILY_API_KEY is required when Web_Search is enabled")
        session_key = (str(user_code), str(token), str(user_token), strict)
        result = run_agent(
            question.strip(),
            str(user_code),
            str(token),
            get_history(session_key),
            strict,
            web_search,
        )
        append_exchange(session_key, question.strip(), result["answer"])
    except ValueError as error:
        return jsonify({"status": "error", "message": str(error), "answer": ""}), 400
    except Exception:
        current_app.logger.exception("Question answering failed")
        return jsonify({"status": "error", "message": "Failed to process question", "answer": ""}), 500
    return jsonify(
        {
            "status": "success",
            "message": "",
            "answer": result["answer"],
            "sources": result["sources"],
        }
    )
