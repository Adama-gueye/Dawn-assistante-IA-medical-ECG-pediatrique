import React from 'react';

export default function AiCard({ card }) {
  return (
    <div className="ai-card">
      <div className="ai-card-hdr">{card.title}</div>
      <div className="ai-card-body" dangerouslySetInnerHTML={{ __html: card.bodyHtml }} />
      {card.confidence != null && (
        <div className="conf-row">
          <span>Confiance :</span>
          <div className="conf-bar"><div className="conf-fill" style={{ width: card.confidence + '%' }} /></div>
          <span className="conf-label">{card.confidence}%</span>
        </div>
      )}
      {card.sources && card.sources.length > 0 && (
        <div className="ai-sources">
          <div className="ai-sources-label">📚 Sources utilisées</div>
          <ul>{card.sources.map((ligne, i) => <li key={i}>{ligne}</li>)}</ul>
        </div>
      )}
    </div>
  );
}
