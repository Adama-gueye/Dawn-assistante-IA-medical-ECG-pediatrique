import React from 'react';

// Ligne de graphique en barres horizontale, partagée par le dashboard et la page Statistiques.
export default function BarRow({ label, value, pct, color = 'blue', showPct = false }) {
  const width = Math.max(0, Math.min(100, pct || 0));
  return (
    <div className="bar-row">
      <div className="bar-label" style={{ width: 110 }}>{label}</div>
      <div className="bar-track">
        <div className={'bar-fill ' + color} style={{ width: width + '%' }}>{showPct && width > 8 ? width + '%' : ''}</div>
      </div>
      <div className="bar-val" style={{ minWidth: 34, textAlign: 'right' }}>{value}</div>
    </div>
  );
}

// Largeur relative (0-100) d'une valeur par rapport au maximum du groupe.
export function relativePct(value, items) {
  const max = Math.max(1, ...items.map((i) => i.valeur));
  return Math.round((value / max) * 100);
}
