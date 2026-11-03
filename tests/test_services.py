"""Document processing and conversation-memory tests."""

import base64
from langchain_core.documents import Document

from services.chunking_service import chunk_documents
from services.document_service import (
    delete_document,
    ingest_base64_document,
    validate_scope,
)
from services.memory_service import append_exchange, clear_history, get_history


def test_csv_chunking_keeps_headers_and_chunks_rows() -> None:
    document = Document(
        page_content="name, value\n" + "\n".join(f"row, {index}" for index in range(11)),
        metadata={"source": "table.csv"},
    )

    chunks = chunk_documents([document])

    assert len(chunks) == 2
    assert all(chunk.page_content.startswith("name, value") for chunk in chunks)
    assert [chunk.metadata["chunk"] for chunk in chunks] == [1, 2]


def test_scope_rejects_path_components() -> None:
    try:
        validate_scope("../user", "token")
    except ValueError as error:
        assert "safe identifier" in str(error)
    else:
        raise AssertionError("unsafe scope was accepted")


def test_document_ingestion_replaces_file_and_index_atomically(
    monkeypatch, tmp_path
) -> None:
    def fake_extract(path, source_name):
        assert path.read_text(encoding="utf-8") == "replacement text"
        return [Document(page_content="replacement text")]

    def fake_save(documents, index_path, model_name):
        index_path.mkdir()
        (index_path / "index.faiss").write_text("new index", encoding="utf-8")
        return len(documents)

    monkeypatch.setattr("services.document_service.extract_documents", fake_extract)
    monkeypatch.setattr("services.document_service.save_index", fake_save)
    upload_root = tmp_path / "uploads"
    index_root = tmp_path / "indexes"
    previous_file = upload_root / "user" / "tenant" / "notes.txt"
    previous_index = index_root / "user" / "tenant" / "notes.txt"
    previous_file.parent.mkdir(parents=True)
    previous_index.mkdir(parents=True)
    previous_file.write_text("previous text", encoding="utf-8")
    (previous_index / "index.faiss").write_text("previous index", encoding="utf-8")

    count = ingest_base64_document(
        upload_dir=upload_root,
        index_dir=index_root,
        user_code="user",
        token="tenant",
        filename="notes",
        file_extension=".txt",
        encoded_content=base64.b64encode(b"replacement text").decode("ascii"),
        embedding_model="test-model",
    )

    assert count == 1
    assert previous_file.read_text(encoding="utf-8") == "replacement text"
    assert (previous_index / "index.faiss").read_text(encoding="utf-8") == "new index"


def test_failed_ingestion_preserves_existing_document(monkeypatch, tmp_path) -> None:
    def fail_extract(path, source_name):
        raise ValueError("invalid text file")

    monkeypatch.setattr("services.document_service.extract_documents", fail_extract)
    upload_root = tmp_path / "uploads"
    index_root = tmp_path / "indexes"
    previous_file = upload_root / "user" / "tenant" / "notes.txt"
    previous_file.parent.mkdir(parents=True)
    previous_file.write_text("previous text", encoding="utf-8")

    try:
        ingest_base64_document(
            upload_dir=upload_root,
            index_dir=index_root,
            user_code="user",
            token="tenant",
            filename="notes",
            file_extension=".txt",
            encoded_content=base64.b64encode(b"invalid").decode("ascii"),
            embedding_model="test-model",
        )
    except ValueError as error:
        assert str(error) == "invalid text file"
    else:
        raise AssertionError("invalid document was accepted")

    assert previous_file.read_text(encoding="utf-8") == "previous text"


def test_delete_normalizes_the_original_upload_name(tmp_path) -> None:
    upload_root = tmp_path / "uploads"
    index_root = tmp_path / "indexes"
    uploaded_file = upload_root / "user" / "tenant" / "meeting_notes.txt"
    uploaded_index = index_root / "user" / "tenant" / "meeting_notes.txt"
    uploaded_file.parent.mkdir(parents=True)
    uploaded_index.mkdir(parents=True)
    uploaded_file.write_text("notes", encoding="utf-8")

    deleted = delete_document(
        upload_dir=upload_root,
        index_dir=index_root,
        user_code="user",
        token="tenant",
        filename="meeting notes.txt",
    )

    assert deleted
    assert not uploaded_file.exists()
    assert not uploaded_index.exists()


def test_conversation_memory_is_scoped_and_bounded() -> None:
    first = ("user", "tenant", "session-a", False)
    second = ("user", "tenant", "session_b", False)
    strict_session = ("user", "tenant", "session-a", True)
    clear_history(first)
    clear_history(second)

    for index in range(6):
        append_exchange(first, f"question {index}", f"answer {index}")

    assert len(get_history(first)) == 10
    assert get_history(first)[0] == "User: question 1"
    assert get_history(second) == []
    assert get_history(strict_session) == []
    clear_history(first)
    assert get_history(first) == []
