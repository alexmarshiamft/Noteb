import React, { useRef, useState } from 'react';
import { generateAudioOverview, getPodcastScript } from '../services/api';

interface AudioOverviewProps {
  sessionId: string;
  hasDocuments: boolean;
}

const AudioOverview: React.FC<AudioOverviewProps> = ({ sessionId, hasDocuments }) => {
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [script, setScript] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showScript, setShowScript] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  const handleGenerateAudio = async () => {
    setError(null);
    setLoading(true);
    try {
      // Generate audio and full script in parallel
      const [{ audioBlob }, fullScript] = await Promise.all([
        generateAudioOverview(sessionId),
        getPodcastScript(sessionId),
      ]);
      const url = URL.createObjectURL(audioBlob);
      setAudioUrl(url);
      setScript(fullScript);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Audio generation failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleGetScriptOnly = async () => {
    setError(null);
    setLoading(true);
    try {
      const fullScript = await getPodcastScript(sessionId);
      setScript(fullScript);
      setShowScript(true);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Script generation failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="audio-overview">
      <div className="audio-overview-header">
        <h3>🎙️ Audio Overview</h3>
        <p className="audio-overview-desc">
          Generate a two-host podcast summary of your sources
        </p>
      </div>

      <div className="audio-overview-actions">
        <button
          className="btn btn-primary"
          onClick={handleGenerateAudio}
          disabled={!hasDocuments || loading}
        >
          {loading ? 'Generating...' : '▶ Generate Podcast'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={handleGetScriptOnly}
          disabled={!hasDocuments || loading}
        >
          📝 Script Only
        </button>
      </div>

      {error && <div className="audio-error">{error}</div>}

      {audioUrl && (
        <div className="audio-player-container">
          <audio ref={audioRef} controls src={audioUrl} className="audio-player">
            Your browser does not support the audio element.
          </audio>
          <a href={audioUrl} download="audio_overview.mp3" className="btn btn-small">
            ⬇ Download MP3
          </a>
        </div>
      )}

      {script && (
        <div className="script-container">
          <button
            className="script-toggle-btn"
            onClick={() => setShowScript(!showScript)}
          >
            {showScript ? '▲ Hide Script' : '▼ Show Script'}
          </button>
          {showScript && <pre className="podcast-script">{script}</pre>}
        </div>
      )}
    </div>
  );
};

export default AudioOverview;
