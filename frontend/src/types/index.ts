export interface DocumentSource {
  doc_id: string;
  filename: string;
  content: string;
  source_type: 'file' | 'url' | 'youtube' | 'audio';
}

export interface Citation {
  doc_id: string;
  quote: string;
  index?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

export interface UploadResponse {
  doc_id: string;
  filename: string;
  source_type: string;
  char_count: number;
  message: string;
}

export interface ChatResponse {
  message: string;
  citations: Citation[];
  raw_response: string;
}
