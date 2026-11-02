import React, { useState, useRef, useEffect } from 'react';
import { useAppState, useAppDispatch, useAppActions } from '../../context/AppContext';
import AiCard from '../../components/AiCard';
import DeleteSessionButton from '../../components/DeleteSessionButton';
import { toDisplayEntries } from '../../utils/messages';
import { shortDateTime } from '../../utils/helpers';

export default function ChatPage() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const {
    startSession, renameSession,
    sendDoctorText, sendDoctorAttachment, sendDoctorCsvAttachment,
    loadSessionMessages,
  } = useAppActions();

  const [search, setSearch] = useState('');
  const [input, setInput] = useState('');
  const [fileError, setFileError] = useState('');
  const [csvFs, setCsvFs] = useState(500);
  const [csvEntete, setCsvEntete] = useState(true);
  // Session SANS dossier patient : âge et sexe obligatoires pour l'analyse ECG (entrées du modèle).
  const [ageVal, setAgeVal] = useState('');
  const [ageUnite, setAgeUnite] = useState('annees');
  const [sexeCli, setSexeCli] = useState('');
  const [starting, setStarting] = useState(false);       // création de session / envoi en cours
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState('');
  const bodyRef = useRef(null);
  const cancelTitleRef = useRef(false);
  const prevSessionRef = useRef(null);

  const patient = state.dossiers.find((p) => p.id === state.chat.activeDossierId);
  const label = patient ? `${patient.prenom_enfant} ${patient.nom_enfant}` : 'personnelles';
  const sessions = state.sessions
    .filter((s) => (s.dossier_patient_id ?? null) === (state.chat.activeDossierId ?? null))
    .filter((s) => s.titre.toLowerCase().includes(search.trim().toLowerCase()))
    .sort((a, b) => new Date(b.date_session) - new Date(a.date_session));
  const activeSession = state.sessions.find((s) => s.id === state.chat.activeSessionId);
  const pending = state.pending && activeSession && state.pending.sessionId === activeSession.id ? state.pending : null;
  const busy = starting || !!state.pending;

  useEffect(() => {
    if (activeSession && activeSession.messages === null) {
      loadSessionMessages(activeSession.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSession?.id, activeSession?.messages]);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [activeSession?.messages?.length, state.pending]);

  useEffect(() => {
    setFileError('');
  }, [state.chat.inputType, state.chat.activeSessionId]);

  useEffect(() => {
    setEditingTitle(false);
    // On ne garde pas l'âge/le sexe d'un patient en passant à une autre session (risque de les réutiliser pour un autre patient).
    // La création automatique de la session au 1er envoi (null -> id) ne les efface pas.
    if (prevSessionRef.current !== null && prevSessionRef.current !== state.chat.activeSessionId) { setAgeVal(''); setSexeCli(''); }
    prevSessionRef.current = state.chat.activeSessionId;
  }, [state.chat.activeSessionId]);

  function setMode(mode) {
    dispatch({ type: 'SET_CHAT_INPUT_TYPE', inputType: mode });
  }

  // Pas de session ouverte = nouvelle conversation : on la crée au premier envoi.
  async function ensureSessionId() {
    if (activeSession) return activeSession.id;
    const created = await startSession(state.chat.activeDossierId);
    return created ? created.id : null;
  }

  async function handleSendText() {
    const text = input.trim();
    if (!text || busy) return;
    setStarting(true);
    setInput('');
    try {
      const sid = await ensureSessionId();
      if (sid === null) { setInput(text); return; }
      const ok = await sendDoctorText(sid, text);
      if (!ok) setInput(text);
    } finally {
      setStarting(false);
    }
  }

  // null = pas nécessaire (le serveur prend l'âge et le sexe du dossier) ; undefined = invalide (message affiché) ; sinon { ageAnnees, sexe }.
  function donneesCliniques() {
    if (patient) return null;
    const v = Number(ageVal);
    if (ageVal === '' || Number.isNaN(v) || v < 0 || !sexeCli) {
      setFileError("Session sans dossier patient : renseignez l'âge et le sexe du patient (obligatoires pour l'analyse ECG).");
      return undefined;
    }
    const ageAnnees = ageUnite === 'jours' ? v / 365.25 : ageUnite === 'mois' ? v / 12 : v;
    return { ageAnnees, sexe: sexeCli };
  }

  async function handleEcgFiles(e) {
    const files = Array.from(e.target.files || []);
    e.target.value = '';
    if (!files.length || busy) return;

    const hea = files.find((f) => f.name.toLowerCase().endsWith('.hea'));
    const dat = files.find((f) => f.name.toLowerCase().endsWith('.dat'));
    if (files.length !== 2 || !hea || !dat) {
      setFileError('Sélectionnez les deux fichiers WFDB ensemble : le .hea et le .dat du même enregistrement.');
      return;
    }
    if (hea.name.replace(/\.hea$/i, '') !== dat.name.replace(/\.dat$/i, '')) {
      setFileError('Le .hea et le .dat ne correspondent pas au même enregistrement (noms différents).');
      return;
    }
    const clinique = donneesCliniques();
    if (clinique === undefined) return;
    setFileError('');
    const question = input.trim();
    setStarting(true);
    setInput('');
    try {
      const sid = await ensureSessionId();
      if (sid === null) { setInput(question); return; }
      const ok = await sendDoctorAttachment(sid, hea, dat, question, clinique);
      if (!ok) setInput(question);
    } finally {
      setStarting(false);
    }
  }

  async function handleCsvFile(e) {
    const file = e.target.files && e.target.files[0];
    e.target.value = '';
    if (!file || busy) return;
    const clinique = donneesCliniques();
    if (clinique === undefined) return;
    setFileError('');
    const question = input.trim();
    setStarting(true);
    setInput('');
    try {
      const sid = await ensureSessionId();
      if (sid === null) { setInput(question); return; }
      const ok = await sendDoctorCsvAttachment(sid, file, csvFs, csvEntete, question, clinique);
      if (!ok) setInput(question);
    } finally {
      setStarting(false);
    }
  }

  function beginEditTitle() {
    if (!activeSession) return;
    cancelTitleRef.current = false;
    setTitleDraft(activeSession.titre);
    setEditingTitle(true);
  }

  async function commitTitle() {
    setEditingTitle(false);
    if (cancelTitleRef.current) { cancelTitleRef.current = false; return; }
    const titre = titleDraft.trim();
    if (!activeSession || !titre || titre === activeSession.titre) return;
    await renameSession(activeSession.id, titre);
  }

  const blocClinique = patient ? (
    <div className="chat-input-hint">Âge et sexe repris du dossier de {label}.</div>
  ) : (
    <div className="chat-clinique">
      <span className="chat-clinique-titre">Patient — obligatoire (entrées du modèle)</span>
      <label>Âge
        <input type="number" min="0" step="any" value={ageVal} onChange={(e) => setAgeVal(e.target.value)} disabled={busy} />
        <select value={ageUnite} onChange={(e) => setAgeUnite(e.target.value)} disabled={busy}>
          <option value="annees">ans</option><option value="mois">mois</option><option value="jours">jours</option>
        </select>
      </label>
      <label>Sexe
        <select value={sexeCli} onChange={(e) => setSexeCli(e.target.value)} disabled={busy}>
          <option value="">—</option><option value="M">Garçon</option><option value="F">Fille</option>
        </select>
      </label>
    </div>
  );

  const entries = activeSession && activeSession.messages ? activeSession.messages.flatMap((m) => toDisplayEntries(m)) : [];
  const doctorName = state.currentUser ? `Dr. ${state.currentUser.nom}` : 'Médecin';

  return (
    <div className="page active">
      <div className="chat-shell">
        <div className="chat-sb">
          <div className="chat-sb-hdr">
            <div className="chat-sb-title">Sessions — <span>{label}</span></div>
            <div className="chat-sb-search">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 14, height: 14, position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--g400)', pointerEvents: 'none' }}><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
              <input type="text" placeholder="Rechercher une session..." value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
            <button className="chat-new-btn" onClick={() => dispatch({ type: 'SELECT_SESSION', id: null })} disabled={busy}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 14, height: 14 }}><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg> Nouvelle session
            </button>
          </div>
          <div className="chat-sessions">
            {sessions.length === 0 ? (
              <div className="chat-s-item empty-hint">{search.trim() ? 'Aucune session trouvée' : 'Aucune session — écrivez pour en démarrer une'}</div>
            ) : sessions.map((s) => (
              <div key={s.id} onClick={() => !busy && dispatch({ type: 'SELECT_SESSION', id: s.id })} className={'chat-s-item' + (s.id === state.chat.activeSessionId ? ' active' : '')}>
                <span className="emoji">💬</span><span className="ttl">{s.titre}</span><span className="sess-time">{shortDateTime(s.date_session)}</span>
                <DeleteSessionButton session={s} />
              </div>
            ))}
          </div>
        </div>
        <div className="chat-main">
          <div className="chat-tb">
            {!activeSession ? (
              <div className="chat-tb-title">Nouvelle conversation</div>
            ) : editingTitle ? (
              <input
                className="chat-title-input"
                autoFocus
                value={titleDraft}
                maxLength={255}
                onChange={(e) => setTitleDraft(e.target.value)}
                onBlur={commitTitle}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') e.currentTarget.blur();
                  if (e.key === 'Escape') { cancelTitleRef.current = true; e.currentTarget.blur(); }
                }}
              />
            ) : (
              <div className="chat-tb-title editable" onClick={beginEditTitle} title="Cliquer pour renommer la session">
                <span className="chat-title-text">{activeSession.titre}</span>
                <svg className="edit-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9" /><path d="M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4 12.5-12.5z" /></svg>
              </div>
            )}
            {patient && <span className="chat-pt-badge">{patient.sexe === 'F' ? '👩' : '👦'} {patient.prenom_enfant} {patient.nom_enfant}</span>}
            <div className="chat-upload-btns">
              <button className={'chat-up-btn' + (state.chat.inputType === 'text' ? ' active' : '')} onClick={() => setMode('text')}>📝 Texte</button>
              <button className={'chat-up-btn' + (state.chat.inputType === 'ecg' ? ' active' : '')} onClick={() => setMode('ecg')}>📊 ECG</button>
              <button className={'chat-up-btn' + (state.chat.inputType === 'csv' ? ' active' : '')} onClick={() => setMode('csv')}>🧪 CSV (test)</button>
            </div>
            {activeSession && <DeleteSessionButton session={activeSession} />}
            <button className="tb-btn" title="Retour" style={{ marginLeft: 8 }} onClick={() => {
              if (patient) {
                dispatch({ type: 'OPEN_RECORD', id: patient.id });
              } else {
                dispatch({ type: 'DOC_NAV', view: 'sessions' });
                dispatch({ type: 'GO_PAGE', page: 'doctor' });
              }
            }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 12H5" /><polyline points="12 19 5 12 12 5" /></svg>
            </button>
          </div>

          <div className="chat-body" ref={bodyRef}>
            {!activeSession ? (
              <div className="empty-state">
                <div className="ico">💬</div>
                <div className="txt">Nouvelle conversation</div>
                <div className="sub">Posez votre question ci-dessous : la session sera créée et nommée automatiquement{patient ? ` pour ${label}` : ''}.</div>
              </div>
            ) : activeSession.messages === null ? (
              <div className="empty-state"><div className="ico">⏳</div><div className="txt">Chargement des messages...</div></div>
            ) : (
              <>
                {entries.map((m, i) => <ChatMessage key={i} m={m} doctorName={doctorName} />)}
                {pending && pending.entries.map((m, i) => <ChatMessage key={'p' + i} m={m} doctorName={doctorName} />)}
                {pending && <TypingIndicator />}
              </>
            )}
          </div>

          <div className="chat-input-area">
            {state.chat.inputType === 'text' && (
              <div className="chat-input-row">
                <input
                  className="chat-input"
                  placeholder={busy ? 'DAWN rédige sa réponse…' : 'Posez votre question...'}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSendText(); }}
                  disabled={busy}
                />
                <button className="chat-send" onClick={handleSendText} disabled={busy || !input.trim()}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" /></svg>
                </button>
              </div>
            )}

            {state.chat.inputType === 'ecg' && (
              <div className="chat-file-block">
                <input
                  className="chat-input"
                  placeholder="Question optionnelle pour DAWN (facultatif)"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={busy}
                />
                {blocClinique}
                <label className={'chat-file-drop' + (busy ? ' disabled' : '')}>
                  <input type="file" multiple accept=".hea,.dat" onChange={handleEcgFiles} disabled={busy} />
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
                  <span>📎 Cliquez ici pour choisir les 2 fichiers WFDB (.hea + .dat) du même enregistrement</span>
                </label>
              </div>
            )}

            {state.chat.inputType === 'csv' && (
              <div className="chat-file-block">
                <input
                  className="chat-input"
                  placeholder="Question optionnelle pour DAWN (facultatif)"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  disabled={busy}
                />
                <div className="chat-csv-opts">
                  <span className="chat-input-hint">🧪 Outil de test — convertit le CSV en WFDB côté serveur avant analyse.</span>
                  <label>Fréquence (Hz) <input type="number" min="1" value={csvFs} onChange={(e) => setCsvFs(Number(e.target.value) || 500)} /></label>
                  <label><input type="checkbox" checked={csvEntete} onChange={(e) => setCsvEntete(e.target.checked)} /> Le CSV a une ligne d'en-tête</label>
                </div>
                {blocClinique}
                <label className={'chat-file-drop' + (busy ? ' disabled' : '')}>
                  <input type="file" accept=".csv" onChange={handleCsvFile} disabled={busy} />
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" /></svg>
                  <span>📎 Cliquez ici pour choisir un fichier CSV</span>
                </label>
              </div>
            )}

            {fileError && <div className="chat-input-error">{fileError}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="msg ai" aria-live="polite">
      <div className="msg-label">🤖 DAWN AI</div>
      <div className="msg-bubble typing-bubble" aria-label="DAWN rédige sa réponse">
        <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
      </div>
    </div>
  );
}

function ChatMessage({ m, doctorName }) {
  if (m.from === 'ai' && m.card) {
    return (
      <div className="msg ai"><div className="msg-label">🤖 DAWN AI</div><AiCard card={m.card} /></div>
    );
  }
  if (m.from === 'ai') {
    return <div className="msg ai"><div className="msg-label">🤖 DAWN AI</div><div className="msg-bubble" dangerouslySetInnerHTML={{ __html: m.html }} /></div>;
  }
  return (
    <div className="msg dr">
      <div className="msg-label">{doctorName}</div>
      <div className="msg-bubble">
        {m.text}
        {m.attachment && (
          <div className="ecg-attach">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
            <div><div className="fn">{m.attachment.name}</div><div className="fs">{m.attachment.meta}</div></div>
          </div>
        )}
      </div>
    </div>
  );
}
