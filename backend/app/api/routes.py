"""
API routes for the NotebookLM clone backend.
"""
import logging
import os
import uuid
from typing import Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    SessionDocuments,
    UploadResponse,
)
from app.services.audio_service import AudioService
from app.services.gemini_service import GeminiService
from app.services.ingestion import ingest_file, ingest_url

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session store: session_id -> list of documents
# In production, replace with a persistent store (Redis, DB, etc.)
_sessions: Dict[str, List[dict]] = {}


def get_gemini_service() -> GeminiService:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
    return GeminiService(api_key=api_key)


def get_audio_service() -> AudioService:
    tts_key = os.environ.get("GOOGLE_TTS_API_KEY")
    return AudioService(tts_api_key=tts_key)


@router.post("/sessions", response_model=dict)
async def create_session():
    """Create a new session and return its ID."""
    session_id = str(uuid.uuid4())
    _sessions[session_id] = []
    return {"session_id": session_id}


@router.post("/sessions/{session_id}/upload", response_model=UploadResponse)
async def upload_document(
    session_id: str,
    file: UploadFile = File(...),
):
    """Upload and parse a document file into the session."""
    if session_id not in _sessions:
        _sessions[session_id] = []

    content = await file.read()
    filename = file.filename or "unknown"

    try:
        parsed_text, source_type = ingest_file(filename, content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse file: {e}")

    doc_id = str(uuid.uuid4())[:8]
    _sessions[session_id].append(
        {
            "doc_id": doc_id,
            "filename": filename,
            "content": parsed_text,
            "source_type": source_type,
        }
    )

    return UploadResponse(
        doc_id=doc_id,
        filename=filename,
        source_type=source_type,
        char_count=len(parsed_text),
        message=f"Successfully ingested '{filename}'",
    )


@router.post("/sessions/{session_id}/upload-url", response_model=UploadResponse)
async def upload_url(session_id: str, url: str = Form(...)):
    """Ingest a URL (web page or YouTube) into the session."""
    if session_id not in _sessions:
        _sessions[session_id] = []

    try:
        parsed_text, source_type = ingest_url(url)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to ingest URL: {e}")

    doc_id = str(uuid.uuid4())[:8]
    filename = url[:80]
    _sessions[session_id].append(
        {
            "doc_id": doc_id,
            "filename": filename,
            "content": parsed_text,
            "source_type": source_type,
        }
    )

    return UploadResponse(
        doc_id=doc_id,
        filename=filename,
        source_type=source_type,
        char_count=len(parsed_text),
        message="Successfully ingested URL",
    )


@router.get("/sessions/{session_id}/documents", response_model=SessionDocuments)
async def get_session_documents(session_id: str):
    """Get all documents in the current session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDocuments(
        session_id=session_id,
        documents=_sessions[session_id],
    )


@router.delete("/sessions/{session_id}/documents/{doc_id}")
async def delete_document(session_id: str, doc_id: str):
    """Remove a document from the session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    _sessions[session_id] = [
        d for d in _sessions[session_id] if d["doc_id"] != doc_id
    ]
    return {"message": f"Document {doc_id} removed"}


@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat(
    session_id: str,
    request: ChatRequest,
    gemini: GeminiService = Depends(get_gemini_service),
):
    """Send a chat message grounded in the session documents."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    docs = _sessions[session_id]
    if not docs:
        raise HTTPException(
            status_code=400,
            detail="No documents in session. Please upload at least one document first.",
        )

    try:
        result = gemini.query(
            user_query=request.query,
            documents=docs,
            session_id=session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM query failed: {e}")

    return ChatResponse(
        message=result["message"],
        citations=result["citations"],
        raw_response=result["raw_response"],
    )


@router.post("/sessions/{session_id}/audio-overview")
async def generate_audio_overview(
    session_id: str,
    gemini: GeminiService = Depends(get_gemini_service),
    audio_svc: AudioService = Depends(get_audio_service),
):
    """Generate a two-host podcast audio overview of the session documents."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    docs = _sessions[session_id]
    if not docs:
        raise HTTPException(
            status_code=400,
            detail="No documents in session. Please upload at least one document first.",
        )

    try:
        script = gemini.generate_podcast_script(docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {e}")

    try:
        audio_bytes = audio_svc.generate_audio_overview(script)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio synthesis failed: {e}")

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "attachment; filename=audio_overview.mp3",
            "X-Podcast-Script": script[:500],
        },
    )


@router.get("/sessions/{session_id}/audio-overview/script")
async def get_podcast_script(
    session_id: str,
    gemini: GeminiService = Depends(get_gemini_service),
):
    """Get only the podcast script without synthesizing audio."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    docs = _sessions[session_id]
    if not docs:
        raise HTTPException(status_code=400, detail="No documents in session.")

    try:
        script = gemini.generate_podcast_script(docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {e}")

    return {"script": script, "session_id": session_id}


@router.get("/health")
async def health_check():
    return {"status": "ok"}
