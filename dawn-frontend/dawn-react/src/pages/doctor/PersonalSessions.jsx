import React, { useState } from 'react';
import { useAppState, useAppDispatch } from '../../context/AppContext';
import { shortDateTime } from '../../utils/helpers';
import DeleteSessionButton from '../../components/DeleteSessionButton';

const COULEURS = ['blue', 'green', 'purple', 'orange'];

export default function PersonalSessions() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const [search, setSearch] = useState('');

  const sessions = state.sessions
    .filter((s) => s.dossier_patient_id == null)
    .filter((s) => s.titre.toLowerCase().includes(search.trim().toLowerCase()))
    .sort((a, b) => new Date(b.date_session) - new Date(a.date_session));

  // Une « nouvelle session » ouvre directement la conversation, prête à écrire :
  // elle sera créée et nommée automatiquement au premier message.
  const nouvelle = () => dispatch({ type: 'GO_CHAT', dossierId: null });

  return (
    <div className="ca active">
      <div className="phdr"><h1>Sessions personnelles</h1><p>Vos propres questions à l'assistant DAWN, sans lien avec un patient.</p></div>

      <div className="sessions-toolbar">
        <div className="sessions-search">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
          <input type="text" placeholder="Rechercher une session..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <button className="btn-p" onClick={nouvelle}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>Nouvelle session
        </button>
      </div>

      <div className="scard">
        <div className="shdr"><h2>Historique</h2></div>
        <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
          {sessions.length === 0 ? (
            <div className="empty-state">
              <div className="ico">💬</div>
              <div className="txt">{search.trim() ? 'Aucune session ne correspond à votre recherche' : 'Aucune session personnelle pour l\'instant'}</div>
            </div>
          ) : sessions.map((s, i) => (
            <div key={s.id} className={'sess-card ' + COULEURS[i % COULEURS.length] + '-border'} style={{ cursor: 'pointer' }} onClick={() => dispatch({ type: 'GO_CHAT', dossierId: null, sessionId: s.id })}>
              <div className={'sess-ico ' + COULEURS[i % COULEURS.length]}><span style={{ fontSize: 16 }}>💬</span></div>
              <div style={{ flex: 1 }}><div className="sess-title">{s.titre}</div></div>
              <div className="sess-date">{shortDateTime(s.date_session)}</div>
              <DeleteSessionButton session={s} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
