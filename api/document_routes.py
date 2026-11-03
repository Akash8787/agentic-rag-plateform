"""Document upload and management routes."""

from flask import Blueprint, current_app, jsonify, request

from services.document_service import delete_document, ingest_base64_document

document_bp = Blueprint("documents", __name__, url_prefix="/api/documents")


@document_bp.post("")
@document_bp.post("/upload")
def upload_document():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "A JSON object is required"}), 400
    required = ("User_Code", "Token", "pdf_base64", "filename", "file_extension")
    if any(not data.get(field) for field in required):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
    try:
        chunk_count = ingest_base64_document(
            upload_dir=current_app.config["UPLOAD_DIR"],
            index_dir=current_app.config["INDEX_DIR"],
            user_code=str(data["User_Code"]),
            token=str(data["Token"]),
            filename=str(data["filename"]),
            file_extension=str(data["file_extension"]),
            encoded_content=str(data["pdf_base64"]),
            embedding_model=current_app.config["EMBEDDING_MODEL"],
        )
    except ValueError as error:
        return jsonify({"status": "error", "message": str(error)}), 400
    except Exception:
        current_app.logger.exception("Document ingestion failed")
        return jsonify({"status": "error", "message": "Failed to process file"}), 500
    response = jsonify(
        {
            "status": "success",
            "message": "File processed successfully",
            "chunks": chunk_count,
        }
    )
    return response, 200 if request.path == "/upload_pdf" else 201


@document_bp.delete("/<path:filename>")
def delete_document_route(filename: str):
    data = request.get_json(silent=True) or {}
    user_code = request.args.get("User_Code") or data.get("User_Code")
    token = request.args.get("Token") or data.get("Token")
    if not user_code or not token:
        return jsonify({"status": "error", "message": "User_Code and Token are required"}), 400
    try:
        deleted = delete_document(
            upload_dir=current_app.config["UPLOAD_DIR"],
            index_dir=current_app.config["INDEX_DIR"],
            user_code=str(user_code),
            token=str(token),
            filename=filename,
        )
    except ValueError as error:
        return jsonify({"status": "error", "message": str(error)}), 400
    if not deleted:
        return jsonify({"status": "error", "message": "Document not found"}), 404
    return jsonify({"status": "success", "message": "Deletion completed"})
