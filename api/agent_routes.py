"""Agent execution routes."""

from flask import Blueprint

from api.chat_routes import ask_question

agent_bp = Blueprint("agents", __name__, url_prefix="/api/agents")

agent_bp.add_url_rule("/run", view_func=ask_question, methods=["POST"])
