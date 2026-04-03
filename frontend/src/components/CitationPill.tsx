import React from 'react';
import type { Citation } from '../types';

interface CitationPillProps {
  citation: Citation;
  index: number;
  onClick: (citation: Citation) => void;
}

const CitationPill: React.FC<CitationPillProps> = ({ citation, index, onClick }) => {
  return (
    <button
      className="citation-pill"
      onClick={() => onClick(citation)}
      title={`"${citation.quote}"`}
    >
      [{index + 1}]
    </button>
  );
};

export default CitationPill;
