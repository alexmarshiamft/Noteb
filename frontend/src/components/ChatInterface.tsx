import React, { useEffect, useRef, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { sendChatMessage } from '../services/api';
import type { ChatMessage, Citation } from '../types';
import CitationPill from './CitationPill';

interface ChatInterfaceProps {
  sessionId: string;
  hasDocuments: boolean;
  onCitationClick: (citation: Citation) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  sessionId,
  hasDocuments,
  onCitationClick,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    setError(null);

    const userMessage: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content: input.trim(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendChatMessage(sessionId, userMessage.content);
      const assistantMessage: ChatMessage = {
        id: uuidv4(),
        role: 'assistant',
        content: response.message,
        citations: response.citations,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Chat failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const renderMessageContent = (msg: ChatMessage) => {
    if (msg.role === 'user' || !msg.citations || msg.citations.length === 0) {
      return <p className="message-text">{msg.content}</p>;
    }

    const parts = msg.content.split(/(\[\d+\])/g);
    const elements: React.ReactNode[] = [];

    parts.forEach((part, i) => {
      const match = part.match(/^\[(\d+)\]$/);
      if (match) {
        const citationIndex = parseInt(match[1], 10) - 1;
        const citation = msg.citations![citationIndex];
        if (citation) {
          elements.push(
            <CitationPill
              key={`cite-${i}`}
              citation={citation}
              index={citationIndex}
              onClick={onCitationClick}
            />
          );
        } else {
          elements.push(<span key={i}>{part}</span>);
        }
      } else {
        elements.push(<span key={i}>{part}</span>);
      }
    });

    return <p className="message-text">{elements}</p>;
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>Chat</h2>
        {!hasDocuments && (
          <span className="chat-hint">Add sources to start chatting</span>
        )}
      </div>

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="empty-chat">
            <div className="empty-chat-icon">💬</div>
            <p>Ask a question about your uploaded documents.</p>
            <p className="hint">All answers are grounded in your sources.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`message message-${msg.role}`}>
            <div className="message-avatar">{msg.role === 'user' ? '👤' : '🤖'}</div>
            <div className="message-bubble">
              {renderMessageContent(msg)}
              {msg.citations && msg.citations.length > 0 && (
                <div className="message-citations">
                  <span className="citations-label">Sources: </span>
                  {msg.citations.map((c, i) => (
                    <CitationPill
                      key={i}
                      citation={c}
                      index={i}
                      onClick={onCitationClick}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message message-assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-bubble loading-bubble">
              <span className="dot-pulse"></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {error && <div className="chat-error">{error}</div>}

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          className="chat-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={hasDocuments ? 'Ask a question...' : 'Add sources first...'}
          disabled={!hasDocuments || loading}
        />
        <button
          type="submit"
          className="chat-send-btn"
          disabled={!hasDocuments || loading || !input.trim()}
        >
          {loading ? '...' : '→'}
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;
