from pydantic import BaseModel
from typing import Optional, List


class DocumentSource(BaseModel):
    doc_id: str
    filename: str
    content: str
    source_type: str  # "file", "url", "youtube", "audio"


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    source_type: str
    char_count: int
    message: str


class ChatRequest(BaseModel):
    query: str
    session_id: str


class Citation(BaseModel):
    doc_id: str
    quote: str
    position: Optional[int] = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    citations: Optional[List[Citation]] = None


class ChatResponse(BaseModel):
    message: str
    citations: List[Citation]
    raw_response: str


class AudioOverviewRequest(BaseModel):
    session_id: str


class AudioOverviewResponse(BaseModel):
    audio_url: str
    script: str
    message: str


class SessionDocuments(BaseModel):
    session_id: str
    documents: List[DocumentSource]
