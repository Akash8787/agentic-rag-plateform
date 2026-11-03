"""API blueprint registration."""

from flask import Flask

from api.agent_routes import agent_bp
from api.chat_routes import chat_bp
from api.conversation_routes import conversation_bp
from api.document_routes import document_bp


def register_blueprints(app: Flask) -> None:
    """Register all API route blueprints with the application."""
    for blueprint in (document_bp, chat_bp, agent_bp, conversation_bp):
        app.register_blueprint(blueprint)
    app.add_url_rule(
        "/upload_pdf", view_func=app.view_functions["documents.upload_document"],
        methods=["POST"], endpoint="legacy_upload_pdf",
    )
    app.add_url_rule(
        "/delete_pdf", view_func=_legacy_delete_document,
        methods=["POST"], endpoint="legacy_delete_pdf",
    )
    app.add_url_rule(
        "/ask_question", view_func=app.view_functions["chat.ask_question"],
        methods=["POST"], endpoint="legacy_ask_question",
    )


def _legacy_delete_document():
    from flask import current_app, jsonify, request

    from services.document_service import delete_document_counts

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "A JSON object is required"}), 400
    user_code, token, filename = (
        data.get("User_Code"),
        data.get("Token"),
        data.get("pdf_name"),
    )
    if not all((user_code, token, filename)):
        return jsonify({"status": "error", "message": "User_Code, Token, and pdf_name are required"}), 400
    try:
        deleted_files, deleted_indexes = delete_document_counts(
            upload_dir=current_app.config["UPLOAD_DIR"],
            index_dir=current_app.config["INDEX_DIR"],
            user_code=str(user_code),
            token=str(token),
            filename=str(filename),
        )
    except ValueError as error:
        return jsonify({"status": "error", "message": str(error)}), 400
    if not (deleted_files or deleted_indexes):
        return jsonify({"status": "error", "message": "Document not found"}), 404
    return jsonify(
        {
            "status": "success",
            "message": "Deletion completed",
            "deleted_files": deleted_files,
            "deleted_indexes": deleted_indexes,
        }
    )
