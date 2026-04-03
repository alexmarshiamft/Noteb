"""
Audio Overview (Podcast) Generator.
Uses Google Cloud TTS to synthesize multi-speaker podcast audio.
"""
import io
import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


def parse_script_lines(script: str) -> List[Tuple[str, str]]:
    """
    Parse podcast script lines into [(speaker, text), ...].
    Handles [Alex]: and [Jordan]: prefixes.
    """
    lines = []
    pattern = re.compile(r"^\[(Alex|Jordan)\]:\s*(.+)$", re.IGNORECASE)
    for raw_line in script.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            speaker = m.group(1).capitalize()
            text = m.group(2).strip()
            # Remove stage directions like (laughs) from TTS text
            tts_text = re.sub(r"\([^)]+\)", "", text).strip()
            if tts_text:
                lines.append((speaker, tts_text))
    return lines


def synthesize_with_gtts(text: str, slow: bool = False) -> bytes:
    """Synthesize speech using gTTS (Google Text-to-Speech free API)."""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="en", slow=slow)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except ImportError:
        raise RuntimeError("gTTS is required. Install with: pip install gTTS")


def synthesize_with_google_cloud_tts(
    text: str, voice_name: str, api_key: str
) -> bytes:
    """Synthesize speech using Google Cloud TTS REST API."""
    import requests as _requests
    import base64

    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
    payload = {
        "input": {"text": text},
        "voice": {
            "languageCode": "en-US",
            "name": voice_name,
            "ssmlGender": "NEUTRAL",
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": 1.0,
            "pitch": 0.0,
        },
    }
    resp = _requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    audio_content = resp.json()["audioContent"]
    return base64.b64decode(audio_content)


def stitch_audio_segments(segments: List[bytes]) -> bytes:
    """Concatenate MP3 audio segments into a single MP3 file."""
    try:
        from pydub import AudioSegment

        combined = AudioSegment.empty()
        silence = AudioSegment.silent(duration=400)  # 400ms pause between lines

        for i, seg_bytes in enumerate(segments):
            buf = io.BytesIO(seg_bytes)
            try:
                audio_seg = AudioSegment.from_mp3(buf)
            except Exception:
                audio_seg = AudioSegment.from_file(buf)
            combined += audio_seg
            if i < len(segments) - 1:
                combined += silence

        out_buf = io.BytesIO()
        combined.export(out_buf, format="mp3")
        out_buf.seek(0)
        return out_buf.read()
    except ImportError:
        # Fallback: just concatenate raw bytes
        return b"".join(segments)


class AudioService:
    # Voice mapping for two hosts
    VOICE_MAP = {
        "Alex": "en-US-Neural2-D",   # Male voice
        "Jordan": "en-US-Neural2-F",  # Female voice
    }

    def __init__(self, tts_api_key: Optional[str] = None):
        self.tts_api_key = tts_api_key

    def generate_audio_overview(self, script: str) -> bytes:
        """
        Parse script, synthesize each line, stitch together, return MP3 bytes.
        """
        lines = parse_script_lines(script)
        if not lines:
            raise ValueError("No valid script lines found to synthesize.")

        segments = []
        for speaker, text in lines:
            try:
                if self.tts_api_key:
                    voice = self.VOICE_MAP.get(speaker, "en-US-Neural2-D")
                    audio_bytes = synthesize_with_google_cloud_tts(
                        text, voice, self.tts_api_key
                    )
                else:
                    audio_bytes = synthesize_with_gtts(text)
                segments.append(audio_bytes)
            except Exception as e:
                logger.warning(f"TTS failed for line [{speaker}]: {e}")
                continue

        if not segments:
            raise RuntimeError("All TTS synthesis attempts failed.")

        return stitch_audio_segments(segments)
