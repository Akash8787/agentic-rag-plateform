# Agentic RAG Platform

This Flask application organizes document ingestion, retrieval, conversation memory, and answer generation into API, service, and LangGraph agent layers. Supported uploads are PDF, DOCX, XLSX, CSV, and TXT. Scanned PDF images are processed with PaddleOCR.

## Run locally

From this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set GROQ_API_KEY in .env
python app.py
```

The embedding and reranking models are loaded on first use. The Groq key is required when answering a question. Set `TAVILY_API_KEY` to enable web search; keep it empty to disable automatic web fallback.

## Docker deployment

1. Copy `.env.example` to `.env` and set `GROQ_API_KEY`.
2. From this directory, build and start the service:

   ```powershell
   docker compose up --build -d
   ```

3. Check `http://localhost:5000/health` or run `docker compose ps`.

Uploads and FAISS indexes are stored in persistent Compose volumes. Stop the service with `docker compose down`; the volumes remain intact. To also remove stored documents and indexes, run `docker compose down --volumes`.

The GitHub Actions workflow runs tests for this platform and publishes `ghcr.io/<owner>/agentic-rag-platform:latest` and a commit-SHA tag to GitHub Container Registry after a successful push to `main`. To deploy that published image on a server, authenticate Docker to GHCR, set `IMAGE` to the published tag, and run `docker compose pull` followed by `docker compose up -d`. The Compose file uses the latest image by default.

## API

`POST /api/documents` uploads and indexes a base64-encoded file:

```json
{
  "User_Code": "C1001",
  "Token": "TXT",
  "pdf_base64": "<base64-encoded file>",
  "filename": "Fitness",
  "file_extension": ".pdf"
}
```

`POST /api/chat` asks a question about the indexed documents:

```json
{
  "User_Code": "C1001",
  "Token": "TXT",
  "User_Token": "01",
  "Question": "What does the document say?",
  "Condition": true
}
```

Set `Condition` to `true` to require context-grounded answers; set it to `false` to allow a general-knowledge fallback. With `Condition: false`, Tavily is searched automatically when no local document context is found and a key is configured. Add `"Web_Search": true` to request web results even when local documents are available. Web search is not allowed when `Condition` is true. Conversation history is isolated by user, token, and user token, and is held in memory for the lifetime of the process.

`DELETE /api/documents/<filename>?User_Code=C1001&Token=TXT` removes a stored file and its index. `GET` and `DELETE /api/conversations?User_Code=C1001&Token=TXT&User_Token=01` read or clear conversation history.

The legacy `POST /upload_pdf`, `POST /ask_question`, and `POST /delete_pdf` endpoints are retained for existing clients.

## Tests

```powershell
python -m pytest
```
