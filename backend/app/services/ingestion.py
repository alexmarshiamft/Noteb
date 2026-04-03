"""
Data Ingestion & Parsing Module.
Handles parsing of various file types and sources.
"""
import os
import io
import re
import logging
from typing import Tuple
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_txt(content: bytes) -> str:
    """Parse plain text file."""
    return content.decode("utf-8", errors="replace")


def parse_markdown(content: bytes) -> str:
    """Parse markdown file - strip markdown syntax to get plain text."""
    text = content.decode("utf-8", errors="replace")
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    text = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()


def parse_docx(content: bytes) -> str:
    """Parse .docx files."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(content))
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        return "\n\n".join(paragraphs)
    except ImportError:
        raise RuntimeError("python-docx is required to parse .docx files")


def parse_pdf(content: bytes) -> str:
    """Parse PDF files using PyMuPDF with OCR fallback via pytesseract."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=content, filetype="pdf")
        pages = []
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()
            if text.strip():
                pages.append(f"[Page {page_num}]\n{text.strip()}")
            else:
                try:
                    import pytesseract
                    from PIL import Image
                    pix = page.get_pixmap(dpi=200)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ocr_text = pytesseract.image_to_string(img)
                    if ocr_text.strip():
                        pages.append(f"[Page {page_num} (OCR)]\n{ocr_text.strip()}")
                except Exception as ocr_err:
                    logger.warning(f"OCR failed for page {page_num}: {ocr_err}")
        return "\n\n".join(pages)
    except ImportError:
        raise RuntimeError("PyMuPDF is required to parse PDF files")


def parse_url(url: str) -> str:
    """Scrape and extract main article text from a URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    main_content = (
        soup.find("article")
        or soup.find("main")
        or soup.find(id=re.compile(r"content|article|main", re.I))
        or soup.find(class_=re.compile(r"content|article|main|post", re.I))
        or soup.body
    )

    if main_content:
        text = main_content.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def parse_youtube(url: str) -> str:
    """Extract transcript and metadata from a YouTube video."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
        import re as _re

        patterns = [
            r"(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})",
        ]
        video_id = None
        for pattern in patterns:
            m = _re.search(pattern, url)
            if m:
                video_id = m.group(1)
                break

        if not video_id:
            raise ValueError(f"Could not extract YouTube video ID from URL: {url}")

        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_manually_created_transcript(["en"])
        except NoTranscriptFound:
            transcript = transcript_list.find_generated_transcript(["en"])

        entries = transcript.fetch()
        lines = [entry["text"] for entry in entries]
        full_transcript = " ".join(lines)

        return f"[YouTube Transcript - Video ID: {video_id}]\n\n{full_transcript}"
    except ImportError:
        raise RuntimeError("youtube-transcript-api is required to fetch YouTube transcripts")


def parse_audio(content: bytes, filename: str) -> str:
    """Transcribe audio file using OpenAI Whisper ASR."""
    try:
        import whisper
        import tempfile

        suffix = Path(filename).suffix or ".mp3"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            model = whisper.load_model("base")
            result = model.transcribe(tmp_path)
            return result["text"]
        finally:
            os.unlink(tmp_path)
    except ImportError:
        raise RuntimeError("openai-whisper is required to transcribe audio files")


def ingest_file(filename: str, content: bytes) -> Tuple[str, str]:
    """
    Ingest a file and return (parsed_text, source_type).
    """
    fname_lower = filename.lower()

    if fname_lower.endswith(".txt"):
        return parse_txt(content), "file"
    elif fname_lower.endswith(".md"):
        return parse_markdown(content), "file"
    elif fname_lower.endswith(".docx"):
        return parse_docx(content), "file"
    elif fname_lower.endswith(".pdf"):
        return parse_pdf(content), "file"
    elif fname_lower.endswith((".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm")):
        return parse_audio(content, filename), "audio"
    else:
        try:
            return content.decode("utf-8", errors="replace"), "file"
        except Exception:
            raise ValueError(f"Unsupported file type: {filename}")


def ingest_url(url: str) -> Tuple[str, str]:
    """
    Ingest a URL (web or YouTube) and return (parsed_text, source_type).
    """
    youtube_patterns = [
        "youtube.com/watch",
        "youtu.be/",
        "youtube.com/shorts/",
        "youtube.com/embed/",
    ]
    if any(p in url for p in youtube_patterns):
        return parse_youtube(url), "youtube"
    else:
        return parse_url(url), "url"
