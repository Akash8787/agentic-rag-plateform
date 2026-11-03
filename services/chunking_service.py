"""Text chunking and preparation."""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def chunk_documents(
    documents: list[Document], chunk_size: int = 1000, chunk_overlap: int = 100
) -> list[Document]:
    """Split regular prose by characters and tabular data by rows."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = []
    for document in documents:
        content = document.page_content
        source = str(document.metadata.get("source", "")).lower()
        lines = content.splitlines()
        if source.endswith((".csv", ".xlsx")) and lines and ", " in lines[0]:
            header = lines[0] if not lines[0].startswith("Sheet: ") else ""
            rows = [line for line in lines if line.strip() and not line.startswith("Sheet: ")]
            for offset in range(0, len(rows), 10):
                text = "\n".join(part for part in (header, *rows[offset : offset + 10]) if part)
                metadata = dict(document.metadata)
                metadata["chunk"] = offset // 10 + 1
                chunks.append(Document(page_content=text, metadata=metadata))
            continue

        for index, content_chunk in enumerate(splitter.split_text(content), start=1):
            metadata = dict(document.metadata)
            metadata["chunk"] = index
            chunks.append(Document(page_content=content_chunk, metadata=metadata))
    return chunks
