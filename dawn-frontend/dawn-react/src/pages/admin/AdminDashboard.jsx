import React, { useState, useEffect } from 'react';
import { useAppState, useAppDispatch, useAppActions } from '../../context/AppContext';
import DoctorStatusCells from './DoctorStatusCells';
import BarRow, { relativePct } from '../../components/BarRow';
import MonthPicker from '../../components/MonthPicker';

export default function AdminDashboard() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const { loadStatistiques } = useAppActions();
  const [mois, setMois] = useState(null);
  const s = state.stats;

  useEffect(() => { loadStatistiques(mois); }, [loadStatistiques, mois]);

  const active = state.doctors.filter((d) => d.est_actif).length;
  const inactive = state.doctors.length - active;
  const activityById = Object.fromEntries((s ? s.activite_medecins : []).map((a) => [a.id, a]));
  const kb = s ? s.base_connaissances : null;

  return (
    <div className="ca active">
      <div className="phdr"><h1>Tableau de bord — Administration</h1><p>Vue d'ensemble de la plateforme DAWN.</p></div>

      <div className="st-row c4">
        <div className="st-card green"><div className="si green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /></svg></div><div><div className="sv">{active}</div><div className="sl">Médecins actifs</div></div></div>
        <div className="st-card red"><div className="si red"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /></svg></div><div><div className="sv">{inactive}</div><div className="sl">Médecins inactifs</div></div></div>
        <div className="st-card blue"><div className="si blue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" /></svg></div><div><div className="sv">{state.doctors.length}</div><div className="sl">Comptes médecins</div></div></div>
        <div className="st-card purple"><div className="si blue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" /></svg></div><div><div className="sv">{s ? s.messages : '—'}</div><div className="sl">Messages ce mois</div></div></div>
      </div>

      <div className="act-row">
        <button className="btn-p" onClick={() => dispatch({ type: 'ADMIN_NAV', view: 'doctor-form' })}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>Créer un médecin
        </button>
        <button className="btn-o" onClick={() => dispatch({ type: 'ADMIN_NAV', view: 'stats' })}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 20V10" /><path d="M12 20V4" /><path d="M6 20v-6" /></svg>Voir les statistiques détaillées
        </button>
      </div>

      <div className="scard">
        <div className="shdr">
          <h2>Activité du mois — par médecin</h2>
          <MonthPicker mois={mois} onChange={setMois} />
        </div>
        <table className="ptbl">
          <thead><tr><th>Médecin</th><th>Spécialité</th><th>Nouveaux patients</th><th>Sessions</th><th>Messages</th><th>Statut</th><th>Actions</th></tr></thead>
          <tbody>
            {state.doctors.length === 0 ? (
              <tr><td colSpan={7}><div className="empty-state"><div className="ico">🩺</div><div className="txt">Aucun médecin pour l'instant</div></div></td></tr>
            ) : state.doctors.map((d) => {
              const a = activityById[d.id];
              return (
                <tr key={d.id}>
                  <td><div style={{ fontWeight: 600 }}>Dr. {d.prenom} {d.nom}</div><div style={{ fontSize: 12, color: 'var(--g500)' }}>{d.email}</div></td>
                  <td>{d.specialite}</td>
                  <td>{a ? a.dossiers : 0}</td>
                  <td>{a ? a.sessions : 0}</td>
                  <td>{a ? a.messages : 0}</td>
                  <DoctorStatusCells doctor={d} />
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {s && (
        <div className="two-col">
          <div className="scard">
            <div className="shdr"><h2>Messages par type — ce mois</h2></div>
            <div style={{ padding: 24 }}>
              {s.messages === 0 ? <div style={{ fontSize: 13, color: 'var(--g400)' }}>Aucun message ce mois-ci.</div> : (
                <div className="bar-chart">
                  {s.messages_par_type.map((m) => <BarRow key={m.label} label={m.label} value={m.valeur} pct={relativePct(m.valeur, s.messages_par_type)} color="orange" />)}
                </div>
              )}
            </div>
          </div>
          <div className="scard">
            <div className="shdr"><h2>Base de connaissances</h2></div>
            <div style={{ padding: 24 }}>
              <div className="bar-chart">
                <BarRow label="Documents" value={`${kb.documents_indexes}/${kb.documents_total}`} pct={kb.documents_total ? Math.round((kb.documents_indexes / kb.documents_total) * 100) : 0} color="blue" />
                <BarRow label="Cas cliniques" value={`${kb.cas_indexes}/${kb.cas_total}`} pct={kb.cas_total ? Math.round((kb.cas_indexes / kb.cas_total) * 100) : 0} color="green" />
              </div>
              <div style={{ fontSize: 12, color: 'var(--g400)', marginTop: 14 }}>Éléments indexés / total (population totale, pas bornée au mois)</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
