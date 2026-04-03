import React, { useRef, useState } from 'react';
import { uploadFile, uploadUrl } from '../services/api';
import type { DocumentSource } from '../types';

interface FileUploadProps {
  sessionId: string;
  onDocumentAdded: (doc: DocumentSource) => void;
  onDocumentRemoved: (docId: string) => void;
  documents: DocumentSource[];
}

const SUPPORTED_EXTENSIONS = ['.txt', '.md', '.docx', '.pdf', '.mp3', '.wav', '.m4a'];

const FileUpload: React.FC<FileUploadProps> = ({
  sessionId,
  onDocumentAdded,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [urlInput, setUrlInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFiles = async (files: FileList | File[]) => {
    setError(null);
    setLoading(true);
    try {
      for (const file of Array.from(files)) {
        const result = await uploadFile(sessionId, file);
        onDocumentAdded({
          doc_id: result.doc_id,
          filename: result.filename,
          content: '',
          source_type: result.source_type as DocumentSource['source_type'],
        });
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Upload failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const result = await uploadUrl(sessionId, urlInput.trim());
      onDocumentAdded({
        doc_id: result.doc_id,
        filename: result.filename,
        content: '',
        source_type: result.source_type as DocumentSource['source_type'],
      });
      setUrlInput('');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'URL ingestion failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  };

  return (
    <div className="file-upload">
      <div
        className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <div className="drop-zone-icon">📂</div>
        <p>Drop files here or click to browse</p>
        <p className="drop-zone-hint">Supports: {SUPPORTED_EXTENSIONS.join(', ')}</p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={SUPPORTED_EXTENSIONS.join(',')}
          style={{ display: 'none' }}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
      </div>

      <form className="url-form" onSubmit={handleUrlSubmit}>
        <input
          type="url"
          placeholder="Paste a URL or YouTube link..."
          value={urlInput}
          onChange={(e) => setUrlInput(e.target.value)}
          className="url-input"
        />
        <button
          type="submit"
          disabled={loading || !urlInput.trim()}
          className="url-submit-btn"
        >
          Add
        </button>
      </form>

      {error && <div className="upload-error">{error}</div>}
      {loading && <div className="upload-loading">Processing...</div>}
    </div>
  );
};

export default FileUpload;
