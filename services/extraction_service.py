"""Text and metadata extraction for supported document types."""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from langchain_core.documents import Document

logger = logging.getLogger(__name__)
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".txt"}


def extract_documents(file_path: Path, source_name: str) -> list[Document]:
    """Extract text from a supported file, including OCR for PDF images."""
    extension = file_path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension or '(none)'}")

    if extension == ".pdf":
        return _extract_pdf(file_path, source_name)
    if extension == ".docx":
        from docx import Document as DocxDocument

        document = DocxDocument(str(file_path))
        content = [paragraph.text for paragraph in document.paragraphs]
        content.extend(
            cell.text
            for table in document.tables
            for row in table.rows
            for cell in row.cells
        )
        return _document_if_nonempty("\n".join(content), source_name)
    if extension == ".xlsx":
        sheets = pd.read_excel(file_path, engine="openpyxl", sheet_name=None)
        pages = []
        for sheet_name, frame in sheets.items():
            frame = frame.fillna("")
            rows = [
                ", ".join(f"{column}: {value}" for column, value in row.items())
                for _, row in frame.iterrows()
            ]
            pages.append(f"Sheet: {sheet_name}\n" + "\n".join(rows))
        return _document_if_nonempty(
            "\n\n".join(pages),
            source_name,
            columns=", ".join(str(column) for column in next(iter(sheets.values())).columns)
            if sheets
            else "",
        )
    if extension == ".csv":
        try:
            frame = pd.read_csv(file_path, encoding="utf-8").fillna("")
        except UnicodeDecodeError:
            frame = pd.read_csv(file_path, encoding="latin1").fillna("")
        content = "\n".join(
            ", ".join(f"{column}: {value}" for column, value in row.items())
            for _, row in frame.iterrows()
        )
        return _document_if_nonempty(
            content,
            source_name,
            columns=", ".join(str(column) for column in frame.columns),
        )

    content = file_path.read_text(encoding="utf-8-sig", errors="replace")
    return _document_if_nonempty(content, source_name)


def _document_if_nonempty(content: str, source_name: str, **metadata: Any) -> list[Document]:
    if not content.strip():
        return []
    return [
        Document(
            page_content=content,
            metadata={"source": source_name, "page": 1, **metadata},
        )
    ]


def _extract_pdf(file_path: Path, source_name: str) -> list[Document]:
    import fitz

    pages = []
    with fitz.open(file_path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            page_text = page.get_text()
            image_text = _extract_page_image_text(pdf, page)
            combined = "\n".join(part for part in (page_text, image_text) if part)
            if combined.strip():
                pages.append(
                    Document(
                        page_content=combined,
                        metadata={"source": source_name, "page": page_number},
                    )
                )
    return pages


def _extract_page_image_text(pdf: Any, page: Any) -> str:
    images = page.get_images(full=True)
    if not images:
        return ""

    from PIL import Image
    import numpy as np

    ocr = _get_ocr()
    texts = []
    for image_info in images:
        image_bytes = pdf.extract_image(image_info[0])["image"]
        image = Image.open(__import__("io").BytesIO(image_bytes)).convert("RGB")
        for result in ocr.predict(np.asarray(image)) or []:
            if hasattr(result, "get"):
                recognized = result.get("rec_texts", [])
            else:
                recognized = result.json.get("res", {}).get("rec_texts", [])
            texts.extend(text.strip() for text in recognized if text and text.strip())
    return "\n".join(texts)


def _get_ocr() -> Any:
    return _load_ocr()


@lru_cache(maxsize=1)
def _load_ocr() -> Any:
    from paddleocr import PaddleOCR

    return PaddleOCR(
        lang="en",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
    )
