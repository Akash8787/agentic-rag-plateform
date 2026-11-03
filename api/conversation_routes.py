"""Conversation history routes."""

from flask import Blueprint, jsonify, request

from services.document_service import validate_scope
from services.memory_service import clear_history, get_history, parse_condition

conversation_bp = Blueprint(
    "conversations", __name__, url_prefix="/api/conversations"
)


@conversation_bp.route("", methods=["GET", "DELETE"])
def conversation_history():
    user_code = request.args.get("User_Code")
    token = request.args.get("Token")
    user_token = request.args.get("User_Token")
    if not all((user_code, token, user_token)):
        return jsonify({"status": "error", "message": "User_Code, Token, and User_Token are required"}), 400
    try:
        validate_scope(user_code, token)
        validate_scope(user_code, user_token)
        strict = parse_condition(request.args.get("Condition", "false"))
    except ValueError as error:
        return jsonify({"status": "error", "message": str(error)}), 400
    session_key = (user_code, token, user_token, strict)
    if request.method == "DELETE":
        clear_history(session_key)
        return jsonify({"status": "success", "message": "Conversation cleared"})
    return jsonify({"status": "success", "history": get_history(session_key)})
