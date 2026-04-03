import axios from 'axios';
import type { ChatResponse, DocumentSource, UploadResponse } from '../types';

const BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: BASE_URL,
});

export async function createSession(): Promise<string> {
  const res = await api.post<{ session_id: string }>('/sessions');
  return res.data.session_id;
}

export async function uploadFile(
  sessionId: string,
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post<UploadResponse>(
    `/sessions/${sessionId}/upload`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return res.data;
}

export async function uploadUrl(
  sessionId: string,
  url: string
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('url', url);
  const res = await api.post<UploadResponse>(
    `/sessions/${sessionId}/upload-url`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return res.data;
}

export async function getSessionDocuments(
  sessionId: string
): Promise<DocumentSource[]> {
  const res = await api.get<{ session_id: string; documents: DocumentSource[] }>(
    `/sessions/${sessionId}/documents`
  );
  return res.data.documents;
}

export async function deleteDocument(
  sessionId: string,
  docId: string
): Promise<void> {
  await api.delete(`/sessions/${sessionId}/documents/${docId}`);
}

export async function sendChatMessage(
  sessionId: string,
  query: string
): Promise<ChatResponse> {
  const res = await api.post<ChatResponse>(`/sessions/${sessionId}/chat`, {
    query,
    session_id: sessionId,
  });
  return res.data;
}

export async function generateAudioOverview(
  sessionId: string
): Promise<{ audioBlob: Blob; script: string }> {
  const res = await api.post(
    `/sessions/${sessionId}/audio-overview`,
    {},
    { responseType: 'blob' }
  );
  const script = (res.headers['x-podcast-script'] as string) || '';
  return { audioBlob: res.data as Blob, script };
}

export async function getPodcastScript(sessionId: string): Promise<string> {
  const res = await api.get<{ script: string }>(
    `/sessions/${sessionId}/audio-overview/script`
  );
  return res.data.script;
}
