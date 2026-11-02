import React from 'react';

export default function MedicalIllustration({ title, subtitle }) {
  return (
    <div className="login-illustration">
      <div className="li-visual">
        <div className="li-ring r1" />
        <div className="li-ring r2" />
        <div className="li-ring r3" />
        <div className="li-heart-wrap">
          <svg viewBox="0 0 100 100" className="li-heart-svg">
            <path
              d="M50 88 C20 65,5 45,5 28 C5 12,18 2,32 2 C42 2,50 9,50 9 C50 9,58 2,68 2 C82 2,95 12,95 28 C95 45,80 65,50 88 Z"
              stroke="rgba(190,205,255,.55)" strokeWidth="2.5" fill="rgba(92,126,239,.08)"
            />
            <path
              className="li-ecg-path"
              d="M8,50 L30,50 L38,26 L47,74 L56,14 L63,50 L92,50"
              stroke="#8fa4ff" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round"
            />
          </svg>
        </div>
        <div className="li-badge b1" title="Suivi en temps réel">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
        </div>
        <div className="li-badge b2" title="Pour les médecins">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
        </div>
        <div className="li-badge b3" title="Assistant IA">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" /></svg>
        </div>
        <div className="li-badge b4" title="Données sécurisées">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
        </div>
      </div>
      <div className="li-caption">
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>
    </div>
  );
}
