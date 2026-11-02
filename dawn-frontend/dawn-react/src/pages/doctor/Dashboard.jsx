import React, { useState, useEffect } from 'react';
import { useAppState, useAppDispatch, useAppActions } from '../../context/AppContext';
import { ageFromDob, avatarClass, initials, sexShort, shortDate } from '../../utils/helpers';
import BarRow, { relativePct } from '../../components/BarRow';
import MonthPicker from '../../components/MonthPicker';

function lastSessionLabel(dossierId, sessions) {
  const own = sessions.filter((s) => s.dossier_patient_id === dossierId);
  if (!own.length) return null;
  const latest = own.reduce((a, b) => (new Date(a.date_session) > new Date(b.date_session) ? a : b));
  return shortDate(latest.date_session);
}

export default function Dashboard() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const { loadMedecinStatistiques } = useAppActions();
  const [mois, setMois] = useState(null);
  const ms = state.medecinStats;

  useEffect(() => { loadMedecinStatistiques(mois); }, [loadMedecinStatistiques, mois]);

  const doctorLabel = state.currentUser ? `Dr. ${state.currentUser.nom}` : '';

  return (
    <div className="ca active">
      <div className="phdr"><h1>Bonjour, {doctorLabel} 👋</h1><p>Voici un aperçu de votre activité.</p></div>
      <div className="st-row">
        <div className="st-card blue"><div className="si blue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /></svg></div><div><div className="sv">{state.dossiers.length}</div><div className="sl">Patients (total)</div></div></div>
        <div className="st-card green"><div className="si green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" /></svg></div><div><div className="sv">{state.sessions.length}</div><div className="sl">Sessions (total)</div></div></div>
        <div className="st-card orange"><div className="si orange"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 015.83 1c0 2-3 2.5-3 4.5" /><circle cx="12" cy="17" r=".5" /></svg></div><div><div className="sv">{ms ? ms.messages_mois : '—'}</div><div className="sl">Messages ce mois</div></div></div>
      </div>
      <div className="act-row">
        <button className="btn-p" onClick={() => { dispatch({ type: 'SET_EDITING_PATIENT', id: null }); dispatch({ type: 'DOC_NAV', view: 'patient-form' }); }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>Nouveau Patient
        </button>
        <button className="btn-o" onClick={() => dispatch({ type: 'GO_CHAT', dossierId: null })}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 015.83 1c0 2-3 2.5-3 4.5" /><circle cx="12" cy="17" r=".5" /></svg>Session personnelle<span className="sub">Posez vos propres questions</span>
        </button>
      </div>

      <div className="scard">
        <div className="shdr"><h2>Activité mensuelle</h2><MonthPicker mois={mois} onChange={setMois} /></div>
        {!ms ? (
          <div style={{ padding: 24, fontSize: 13, color: 'var(--g400)' }}>Chargement...</div>
        ) : (
          <div className="chart-grid">
            <div className="chart-panel">
              <h3>Sessions du mois</h3>
              <div className="bar-chart">
                <BarRow label="Avec patient" value={ms.sessions_mois - ms.sessions_personnelles_mois} pct={relativePct(ms.sessions_mois - ms.sessions_personnelles_mois, [{ valeur: ms.sessions_mois - ms.sessions_personnelles_mois }, { valeur: ms.sessions_personnelles_mois }])} color="blue" />
                <BarRow label="Personnelles" value={ms.sessions_personnelles_mois} pct={relativePct(ms.sessions_personnelles_mois, [{ valeur: ms.sessions_mois - ms.sessions_personnelles_mois }, { valeur: ms.sessions_personnelles_mois }])} color="orange" />
              </div>
            </div>
            <div className="chart-panel">
              <h3>Messages du mois par type</h3>
              {ms.messages_mois === 0 ? <div style={{ fontSize: 13, color: 'var(--g400)' }}>Aucun message ce mois-ci.</div> : (
                <div className="bar-chart">
                  {ms.messages_par_type_mois.map((m) => <BarRow key={m.label} label={m.label} value={m.valeur} pct={relativePct(m.valeur, ms.messages_par_type_mois)} color="green" />)}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="scard">
        <div className="shdr"><h2>Mes Patients</h2><a className="va" onClick={() => dispatch({ type: 'DOC_NAV', view: 'patients' })}>Voir tout →</a></div>
        <table className="ptbl">
          <thead><tr><th>Patient</th><th>Âge</th><th>Sexe</th><th>Dernière session</th><th>Action</th></tr></thead>
          <tbody>
            {state.dossiers.slice(0, 6).map((p) => (
              <tr key={p.id}>
                <td><div className="pn-cell"><div className={'p-av ' + avatarClass(p.sexe)}>{initials(p.prenom_enfant, p.nom_enfant)}</div><div><div className="p-nm">{p.prenom_enfant} {p.nom_enfant}</div><div className="p-id">#{p.id}</div></div></div></td>
                <td className="p-date">{ageFromDob(p.date_naissance)}</td>
                <td><span className={'p-sex ' + avatarClass(p.sexe)}>{sexShort(p.sexe)}</span></td>
                <td className="p-date">{lastSessionLabel(p.id, state.sessions) || '—'}</td>
                <td><button className="ba" onClick={() => dispatch({ type: 'OPEN_RECORD', id: p.id })}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg> Voir</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
