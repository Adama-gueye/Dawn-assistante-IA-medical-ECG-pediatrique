import React, { useState, useEffect } from 'react';
import { useAppState, useAppActions } from '../../context/AppContext';
import BarRow, { relativePct } from '../../components/BarRow';
import MonthPicker from '../../components/MonthPicker';

function CountBars({ items, color }) {
  const total = items.reduce((n, i) => n + i.valeur, 0);
  if (!items.length || total === 0) {
    return <div style={{ fontSize: 13, color: 'var(--g400)' }}>Pas encore de données.</div>;
  }
  return (
    <div className="bar-chart">
      {items.map((i) => <BarRow key={i.label} label={i.label} value={i.valeur} pct={relativePct(i.valeur, items)} color={color} />)}
    </div>
  );
}

function Section({ title, left, right }) {
  return (
    <div className="stat-chart-section">
      <div className="shdr"><h2>{title}</h2></div>
      <div className="chart-grid">
        <div className="chart-panel"><h3>{left.title}</h3>{left.body}</div>
        <div className="chart-panel"><h3>{right.title}</h3>{right.body}</div>
      </div>
    </div>
  );
}

export default function StatsPage() {
  const state = useAppState();
  const { loadStatistiques } = useAppActions();
  const [mois, setMois] = useState(null);
  const s = state.stats;

  useEffect(() => { loadStatistiques(mois); }, [loadStatistiques, mois]);

  if (!s) {
    return (
      <div className="ca active">
        <div className="phdr"><h1>Statistiques</h1><p>Analyse de l'utilisation de la plateforme DAWN.</p></div>
        <div className="empty-state"><div className="ico">⏳</div><div className="txt">Chargement des statistiques...</div></div>
      </div>
    );
  }

  const liees = s.sessions - s.sessions_personnelles;
  const sessionsItems = [
    { label: 'Liées à un patient', valeur: liees },
    { label: 'Personnelles', valeur: s.sessions_personnelles },
  ];
  const evoDossiers = s.evolution.map((m) => ({ label: m.label, valeur: m.nouveaux_dossiers }));
  const evoSessions = s.evolution.map((m) => ({ label: m.label, valeur: m.nouvelles_sessions }));
  const kb = s.base_connaissances;
  const kbItems = [
    { label: 'Documents', valeur: kb.documents_indexes, total: kb.documents_total },
    { label: 'Cas cliniques', valeur: kb.cas_indexes, total: kb.cas_total },
  ];
  const hasPertinence = s.evolution.some((m) => m.pertinence_moyenne != null);

  return (
    <div className="ca active">
      <div className="phdr"><h1>Statistiques</h1><p>Analyse de l'utilisation de la plateforme DAWN, calculée sur les données réelles.</p></div>

      <div className="stats-toolbar">
        <span className="stats-toolbar-label">Activité, patients et sessions ci-dessous pour :</span>
        <MonthPicker mois={mois} onChange={setMois} />
      </div>

      <div className="st-row c4">
        <div className="st-card blue"><div><div className="sv">{s.dossiers}</div><div className="sl">Nouveaux patients</div></div></div>
        <div className="st-card green"><div><div className="sv">{s.sessions}</div><div className="sl">Sessions</div></div></div>
        <div className="st-card orange"><div><div className="sv">{s.messages}</div><div className="sl">Messages</div></div></div>
        <div className="st-card purple"><div><div className="sv">{s.medecins_actifs}</div><div className="sl">Médecins actifs (total)</div></div></div>
      </div>

      <Section
        title="Activité"
        left={{ title: 'Messages par type', body: <CountBars items={s.messages_par_type} color="orange" /> }}
        right={{ title: 'Sessions par contexte', body: <CountBars items={sessionsItems} color="blue" /> }}
      />
      <Section
        title="Patients (population totale suivie, tous mois confondus)"
        left={{ title: 'Répartition par sexe', body: <CountBars items={s.dossiers_par_sexe} color="purple" /> }}
        right={{ title: "Répartition par tranche d'âge", body: <CountBars items={s.dossiers_par_tranche_age} color="green" /> }}
      />
      <Section
        title="Évolution trimestrielle (indépendante du mois sélectionné ci-dessus)"
        left={{ title: 'Nouveaux patients', body: <CountBars items={evoDossiers} color="blue" /> }}
        right={{ title: 'Nouvelles sessions', body: <CountBars items={evoSessions} color="green" /> }}
      />
      <Section
        title="Qualité du RAG"
        left={{
          title: 'Pertinence moyenne des sources citées',
          body: hasPertinence ? (
            <div className="bar-chart">
              {s.evolution.map((m) => (
                <BarRow key={m.mois} label={m.label} value={m.pertinence_moyenne == null ? '—' : m.pertinence_moyenne + '%'} pct={m.pertinence_moyenne || 0} color="green" showPct={m.pertinence_moyenne != null} />
              ))}
            </div>
          ) : <div style={{ fontSize: 13, color: 'var(--g400)' }}>Aucune source citée pour l'instant.</div>,
        }}
        right={{
          title: 'Base de connaissances indexée',
          body: (
            <div className="bar-chart">
              {kbItems.map((k) => (
                <BarRow key={k.label} label={k.label} value={`${k.valeur}/${k.total}`} pct={k.total ? Math.round((k.valeur / k.total) * 100) : 0} color="orange" showPct={k.total > 0} />
              ))}
            </div>
          ),
        }}
      />
    </div>
  );
}
