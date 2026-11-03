"""Document upload, indexing, listing, and deletion orchestration."""

import base64
import binascii
import os
import re
import shutil
import tempfile
from pathlib import Path

from services.extraction_service import SUPPORTED_EXTENSIONS, extract_documents
from services.indexing_service import save_index

_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def validate_scope(user_code: str, token: str) -> tuple[str, str]:
    """Reject path-like or empty tenant identifiers before using them in paths."""
    if not _SAFE_SEGMENT.fullmatch(user_code) or user_code in {".", ".."}:
        raise ValueError("User_Code must be a safe identifier")
    if not _SAFE_SEGMENT.fullmatch(token) or token in {".", ".."}:
        raise ValueError("Token must be a safe identifier")
    return user_code, token


def ingest_base64_document(
    *,
    upload_dir: Path,
    index_dir: Path,
    user_code: str,
    token: str,
    filename: str,
    file_extension: str,
    encoded_content: str,
    embedding_model: str,
) -> int:
    validate_scope(user_code, token)
    extension = file_extension.lower()
    if not extension.startswith("."):
        extension = f".{extension}"
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    safe_name = _safe_filename(filename, extension)
    try:
        content = base64.b64decode(encoded_content, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError("pdf_base64 must contain valid base64 data") from error
    if not content:
        raise ValueError("Uploaded file is empty")

    scope = Path(user_code) / token
    file_path = upload_dir / scope / safe_name
    target_index = index_dir / scope / safe_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    target_index.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=file_path.parent) as upload_temp:
        staged_file = Path(upload_temp) / safe_name
        staged_file.write_bytes(content)
        documents = extract_documents(staged_file, safe_name)
        if not documents:
            raise ValueError("No valid content extracted")

        with tempfile.TemporaryDirectory(dir=target_index.parent) as index_temp:
            staged_index = Path(index_temp) / "index"
            backup_file = Path(upload_temp) / "previous-file"
            backup_index = Path(index_temp) / "previous-index"
            chunk_count = save_index(documents, staged_index, embedding_model)
            file_backed_up = False
            index_backed_up = False
            new_file_installed = False
            new_index_installed = False
            try:
                if file_path.exists():
                    os.replace(file_path, backup_file)
                    file_backed_up = True
                if target_index.exists():
                    os.replace(target_index, backup_index)
                    index_backed_up = True
                os.replace(staged_file, file_path)
                new_file_installed = True
                os.replace(staged_index, target_index)
                new_index_installed = True
            except Exception:
                if new_file_installed:
                    file_path.unlink(missing_ok=True)
                if new_index_installed:
                    shutil.rmtree(target_index)
                if file_backed_up:
                    os.replace(backup_file, file_path)
                if index_backed_up:
                    os.replace(backup_index, target_index)
                raise
            return chunk_count


def delete_document(
    *, upload_dir: Path, index_dir: Path, user_code: str, token: str, filename: str
) -> bool:
    deleted_files, deleted_indexes = delete_document_counts(
        upload_dir=upload_dir,
        index_dir=index_dir,
        user_code=user_code,
        token=token,
        filename=filename,
    )
    return bool(deleted_files or deleted_indexes)


def delete_document_counts(
    *, upload_dir: Path, index_dir: Path, user_code: str, token: str, filename: str
) -> tuple[int, int]:
    validate_scope(user_code, token)
    if not filename or Path(filename).name != filename:
        raise ValueError("filename must be a simple file name")
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError("filename must have a supported file extension")
    safe_name = _safe_filename(filename, extension)
    scope = Path(user_code) / token
    file_path = upload_dir / scope / safe_name
    index_path = index_dir / scope / safe_name
    deleted_files = int(file_path.is_file())
    deleted_indexes = int(index_path.is_dir())
    if deleted_files:
        file_path.unlink()
    if deleted_indexes:
        shutil.rmtree(index_path)
    return deleted_files, deleted_indexes


def _safe_filename(filename: str, extension: str) -> str:
    from werkzeug.utils import secure_filename

    stem = secure_filename(Path(filename).stem)
    if not stem:
        raise ValueError("filename must include at least one valid character")
    return f"{stem}{extension}"
