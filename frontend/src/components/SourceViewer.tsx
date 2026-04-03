import React, { useEffect, useRef, useState } from 'react';
import type { Citation, DocumentSource } from '../types';

interface SourceViewerProps {
  documents: DocumentSource[];
  activeCitation: Citation | null;
  onDeleteDocument: (docId: string) => void;
}

const SourceViewer: React.FC<SourceViewerProps> = ({
  documents,
  activeCitation,
  onDeleteDocument,
}) => {
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const [highlightedQuote, setHighlightedQuote] = useState<string | null>(null);

  useEffect(() => {
    if (documents.length > 0 && !selectedDocId) {
      setSelectedDocId(documents[0].doc_id);
    }
    if (documents.length === 0) {
      setSelectedDocId(null);
    }
  }, [documents, selectedDocId]);

  useEffect(() => {
    if (!activeCitation) {
      setHighlightedQuote(null);
      return;
    }
    setSelectedDocId(activeCitation.doc_id);
    setHighlightedQuote(activeCitation.quote);
  }, [activeCitation]);

  useEffect(() => {
    if (!highlightedQuote || !contentRef.current) return;
    const el = contentRef.current.querySelector('.highlight') as HTMLElement | null;
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [highlightedQuote, selectedDocId]);

  const selectedDoc = documents.find((d) => d.doc_id === selectedDocId);

  const renderContent = (content: string) => {
    if (!highlightedQuote || !selectedDoc || selectedDoc.doc_id !== selectedDocId) {
      return <pre className="doc-content">{content}</pre>;
    }
    const idx = content.indexOf(highlightedQuote);
    if (idx === -1) {
      return <pre className="doc-content">{content}</pre>;
    }
    return (
      <pre className="doc-content">
        {content.slice(0, idx)}
        <mark className="highlight">{content.slice(idx, idx + highlightedQuote.length)}</mark>
        {content.slice(idx + highlightedQuote.length)}
      </pre>
    );
  };

  return (
    <div className="source-viewer">
      <div className="source-viewer-header">
        <h2>Sources</h2>
        <span className="doc-count">
          {documents.length} document{documents.length !== 1 ? 's' : ''}
        </span>
      </div>

      {documents.length === 0 ? (
        <div className="empty-sources">
          <p>No sources added yet.</p>
          <p className="hint">Upload documents, URLs, or audio to get started.</p>
        </div>
      ) : (
        <>
          <div className="doc-tabs">
            {documents.map((doc) => (
              <button
                key={doc.doc_id}
                className={`doc-tab ${doc.doc_id === selectedDocId ? 'active' : ''}`}
                onClick={() => setSelectedDocId(doc.doc_id)}
                title={doc.filename}
              >
                <span className="doc-tab-icon">
                  {doc.source_type === 'youtube'
                    ? '▶'
                    : doc.source_type === 'url'
                    ? '🌐'
                    : doc.source_type === 'audio'
                    ? '🎵'
                    : '📄'}
                </span>
                <span className="doc-tab-name">
                  {doc.filename.slice(0, 20)}
                  {doc.filename.length > 20 ? '…' : ''}
                </span>
                <button
                  className="doc-delete-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteDocument(doc.doc_id);
                  }}
                  title="Remove source"
                >
                  ×
                </button>
              </button>
            ))}
          </div>

          {selectedDoc && (
            <div className="doc-content-area" ref={contentRef}>
              <div className="doc-meta">
                <strong>{selectedDoc.filename}</strong>
                <span className="doc-type-badge">{selectedDoc.source_type}</span>
              </div>
              {renderContent(selectedDoc.content)}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default SourceViewer;
