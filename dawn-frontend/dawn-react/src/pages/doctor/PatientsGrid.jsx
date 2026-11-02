import React from 'react';
import { useAppState, useAppDispatch } from '../../context/AppContext';
import { ageFromDob, avatarClass, initials, sexLabel, shortDate } from '../../utils/helpers';

function lastSessionLabel(dossierId, sessions) {
  const own = sessions.filter((s) => s.dossier_patient_id === dossierId);
  if (!own.length) return null;
  const latest = own.reduce((a, b) => (new Date(a.date_session) > new Date(b.date_session) ? a : b));
  return shortDate(latest.date_session);
}

export default function PatientsGrid() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  return (
    <div className="ca active">
      <div className="phdr"><h1>Mes Patients</h1><p>Gérez vos patients et accédez à leurs dossiers.</p></div>
      <div className="act-row">
        <button className="btn-p" onClick={() => { dispatch({ type: 'SET_EDITING_PATIENT', id: null }); dispatch({ type: 'DOC_NAV', view: 'patient-form' }); }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>Nouveau Patient
        </button>
      </div>
      {state.dossiers.length === 0 ? (
        <div className="empty-state"><div className="ico">👤</div><div className="txt">Aucun patient pour l'instant</div></div>
      ) : (
        <div className="patients-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(300px,1fr))', gap: 18 }}>
          {state.dossiers.map((p) => (
            <div key={p.id} className="scard" style={{ cursor: 'pointer' }} onClick={() => dispatch({ type: 'OPEN_RECORD', id: p.id })}>
              <div style={{ padding: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 14 }}>
                  <div className={'p-av ' + avatarClass(p.sexe)} style={{ width: 48, height: 48, borderRadius: 14, fontSize: 16 }}>{initials(p.prenom_enfant, p.nom_enfant)}</div>
                  <div><div style={{ fontSize: 16, fontWeight: 700 }}>{p.prenom_enfant} {p.nom_enfant}</div><div style={{ fontSize: 12, color: 'var(--g400)' }}>{ageFromDob(p.date_naissance)} · {sexLabel(p.sexe).slice(0, 1)} · {p.groupe_sanguin || '—'}</div></div>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--g100)', fontSize: 13 }}><span style={{ color: 'var(--g500)' }}>Antécédents</span><span style={{ fontWeight: 600 }}>{p.antecedents ? p.antecedents.slice(0, 24) + (p.antecedents.length > 24 ? '…' : '') : '—'}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--g100)', fontSize: 13 }}><span style={{ color: 'var(--g500)' }}>Dernière session</span><span style={{ fontWeight: 600 }}>{lastSessionLabel(p.id, state.sessions) || '—'}</span></div>
                <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                  <button className="ba" style={{ flex: 1, justifyContent: 'center' }} onClick={(e) => { e.stopPropagation(); dispatch({ type: 'GO_CHAT', dossierId: p.id }); }}>Session</button>
                  <button className="ba" style={{ flex: 1, justifyContent: 'center' }} onClick={(e) => { e.stopPropagation(); dispatch({ type: 'OPEN_RECORD', id: p.id }); }}>Dossier</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
