# NotebookLM Clone

A full-stack NotebookLM-style application for closed-domain RAG (Retrieval-Augmented Generation). Upload documents, chat with an AI grounded exclusively in your sources, and generate a two-host podcast audio overview.

## Architecture

| Layer | Technology |
|---|---|
| Backend | Python FastAPI |
| Frontend | React 18 + TypeScript (Vite) |
| LLM | Google Gemini 1.5 Pro |
| TTS | Google Cloud TTS (or gTTS fallback) |

## Features

- **Multi-source ingestion**: PDF, DOCX, TXT, Markdown, web URLs, YouTube transcripts, audio files (Whisper ASR)
- **Grounded chat**: All answers cite exact quotes from your uploaded documents
- **Citation navigation**: Click a citation to jump to the highlighted passage in the source viewer
- **Audio Overview**: AI-generated two-host podcast (Alex & Jordan) summarizing your sources
- **Session persistence**: Session ID stored in localStorage across reloads

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── api/routes.py     # All API endpoints
│   │   ├── services/
│   │   │   ├── ingestion.py       # File/URL/YouTube/audio parsing
│   │   │   ├── gemini_service.py  # Gemini 1.5 Pro integration
│   │   │   └── audio_service.py   # TTS podcast generation
│   │   └── models/schemas.py # Pydantic models
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.tsx
    │   ├── components/
    │   │   ├── FileUpload.tsx
    │   │   ├── SourceViewer.tsx
    │   │   ├── ChatInterface.tsx
    │   │   ├── CitationPill.tsx
    │   │   └── AudioOverview.tsx
    │   ├── services/api.ts
    │   └── types/index.ts
    └── package.json
```

## Setup

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

## API Reference

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/sessions` | Create a new session |
| `POST` | `/api/v1/sessions/{id}/upload` | Upload a file |
| `POST` | `/api/v1/sessions/{id}/upload-url` | Ingest a URL or YouTube link |
| `GET` | `/api/v1/sessions/{id}/documents` | List session documents |
| `DELETE` | `/api/v1/sessions/{id}/documents/{doc_id}` | Remove a document |
| `POST` | `/api/v1/sessions/{id}/chat` | Chat (grounded in documents) |
| `POST` | `/api/v1/sessions/{id}/audio-overview` | Generate podcast MP3 |
| `GET` | `/api/v1/sessions/{id}/audio-overview/script` | Get podcast script only |
| `GET` | `/api/v1/health` | Health check |

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key (required) |
| `GOOGLE_TTS_API_KEY` | Google Cloud TTS API key (optional, falls back to gTTS) |