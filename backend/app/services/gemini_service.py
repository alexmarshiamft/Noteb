"""
Gemini 1.5 Pro integration with Context Caching.
Handles LLM queries and citation extraction.
"""
import re
import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert research assistant. You must answer the user's question using ONLY the provided documents. If the answer is not in the documents, explicitly state that you do not know. Do not use outside knowledge. For every factual claim you make, append a citation marker in the format <cite doc_id="X" quote="exact text snippet from document X">. Use the exact text from the documents in your citation quotes."""

PODCAST_SCRIPT_PROMPT = """You are writing a podcast script for two hosts: "Alex" and "Jordan". Based on the provided documents, create an engaging, educational, and conversational dialogue that covers the key ideas, findings, and insights from the material.

Requirements:
- Write 15-20 exchanges between the two hosts
- Use the format [Alex]: and [Jordan]: to label each speaker
- Include natural speech patterns: (laughs), (pause), (sighs), hmm, you know, etc.
- Make the conversation feel natural, not like a lecture
- Cover main themes and interesting details from the documents
- End with a brief summary and sign-off

Output only the dialogue script, no additional text."""


def parse_citations(raw_response: str) -> Tuple[str, list]:
    """
    Parse <cite doc_id="X" quote="..."> tags from LLM response.
    Returns (clean_message, citations_list).
    """
    citations = []
    cite_pattern = re.compile(
        r'<cite\s+doc_id=["\']([^"\']+)["\']\s+quote=["\']([^"\']+)["\'](?:\s*/)?>'
        r'(?:</cite>)?',
        re.IGNORECASE | re.DOTALL,
    )

    for i, match in enumerate(cite_pattern.finditer(raw_response)):
        citations.append({
            "doc_id": match.group(1),
            "quote": match.group(2),
            "index": i,
        })

    counter = [0]

    def replace_cite(m: re.Match) -> str:
        counter[0] += 1
        return f"[{counter[0]}]"

    clean_message = cite_pattern.sub(replace_cite, raw_response)
    return clean_message.strip(), citations


class GeminiService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._genai = None
        self._model_name = "gemini-1.5-pro"
        self._init_client()

    def _init_client(self) -> None:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._genai = genai
            logger.info("Gemini client initialized.")
        except ImportError:
            logger.error("google-generativeai package not installed.")
            raise

    def _build_document_context(self, documents: List[Dict]) -> str:
        """Build a combined document context string."""
        parts = []
        for doc in documents:
            parts.append(
                f"=== Document ID: {doc['doc_id']} | Source: {doc['filename']} ===\n"
                f"{doc['content']}\n"
                f"=== End of Document {doc['doc_id']} ==="
            )
        return "\n\n".join(parts)

    def query(
        self,
        user_query: str,
        documents: List[Dict],
        session_id: str,
    ) -> Dict:
        """
        Send a query to Gemini grounded in the provided documents.
        """
        doc_context = self._build_document_context(documents)

        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"--- DOCUMENTS ---\n{doc_context}\n--- END DOCUMENTS ---\n\n"
            f"User Question: {user_query}"
        )

        try:
            model = self._genai.GenerativeModel(
                model_name=self._model_name,
                generation_config={
                    "temperature": 0.0,
                    "top_p": 1.0,
                    "max_output_tokens": 8192,
                },
            )
            response = model.generate_content(full_prompt)
            raw_text = response.text
            clean_message, citations = parse_citations(raw_text)

            return {
                "message": clean_message,
                "citations": citations,
                "raw_response": raw_text,
            }
        except Exception as e:
            logger.error(f"Gemini query failed: {e}")
            raise

    def generate_podcast_script(self, documents: List[Dict]) -> str:
        """Generate a two-host podcast script from the documents."""
        doc_context = self._build_document_context(documents)

        full_prompt = (
            f"{PODCAST_SCRIPT_PROMPT}\n\n"
            f"--- DOCUMENTS ---\n{doc_context}\n--- END DOCUMENTS ---"
        )

        try:
            model = self._genai.GenerativeModel(
                model_name=self._model_name,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_output_tokens": 8192,
                },
            )
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Podcast script generation failed: {e}")
            raise
