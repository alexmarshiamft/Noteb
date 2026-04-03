import { useEffect, useState } from 'react';
import './App.css';
import AudioOverview from './components/AudioOverview';
import ChatInterface from './components/ChatInterface';
import FileUpload from './components/FileUpload';
import SourceViewer from './components/SourceViewer';
import { createSession, deleteDocument, getSessionDocuments } from './services/api';
import type { Citation, DocumentSource } from './types';

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [documents, setDocuments] = useState<DocumentSource[]>([]);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const savedSessionId = localStorage.getItem('notebooklm_session_id');
    if (savedSessionId) {
      setSessionId(savedSessionId);
      getSessionDocuments(savedSessionId)
        .then((docs) => {
          setDocuments(docs);
          setLoading(false);
        })
        .catch(() => {
          initSession();
        });
    } else {
      initSession();
    }
  }, []);

  const initSession = async () => {
    try {
      const newSessionId = await createSession();
      localStorage.setItem('notebooklm_session_id', newSessionId);
      setSessionId(newSessionId);
    } catch {
      setError('Failed to connect to the backend. Make sure the server is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentAdded = (doc: DocumentSource) => {
    setDocuments((prev) => {
      if (prev.find((d) => d.doc_id === doc.doc_id)) return prev;
      return [...prev, doc];
    });
    if (sessionId) {
      getSessionDocuments(sessionId).then(setDocuments).catch(console.error);
    }
  };

  const handleDocumentRemoved = async (docId: string) => {
    if (sessionId) {
      try {
        await deleteDocument(sessionId, docId);
      } catch {
        // Optimistic removal even on error
      }
    }
    setDocuments((prev) => prev.filter((d) => d.doc_id !== docId));
  };

  const handleCitationClick = (citation: Citation) => {
    setActiveCitation(citation);
  };

  if (loading) {
    return (
      <div className="app-loading">
        <div className="spinner"></div>
        <p>Initializing session...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-error">
        <h2>⚠️ Connection Error</h2>
        <p>{error}</p>
        <button
          onClick={() => {
            setError(null);
            setLoading(true);
            initSession();
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-logo">
          <span className="logo-icon">📓</span>
          <span className="logo-text">NotebookLM</span>
        </div>
        <div className="header-actions">
          <AudioOverview sessionId={sessionId!} hasDocuments={documents.length > 0} />
        </div>
      </header>

      <main className="app-main">
        <aside className="sources-panel">
          <FileUpload
            sessionId={sessionId!}
            onDocumentAdded={handleDocumentAdded}
            onDocumentRemoved={handleDocumentRemoved}
            documents={documents}
          />
          <SourceViewer
            documents={documents}
            activeCitation={activeCitation}
            onDeleteDocument={handleDocumentRemoved}
          />
        </aside>

        <section className="chat-panel">
          <ChatInterface
            sessionId={sessionId!}
            hasDocuments={documents.length > 0}
            onCitationClick={handleCitationClick}
          />
        </section>
      </main>
    </div>
  );
}

export default App;
