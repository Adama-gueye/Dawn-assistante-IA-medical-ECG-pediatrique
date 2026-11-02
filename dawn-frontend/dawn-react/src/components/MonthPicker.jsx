import React from 'react';

// mois : "YYYY-MM" | null (null => mois en cours, géré côté API)
export default function MonthPicker({ mois, onChange }) {
  const current = mois || new Date().toISOString().slice(0, 7);

  function shift(delta) {
    const [y, m] = current.split('-').map(Number);
    const d = new Date(y, m - 1 + delta, 1);
    onChange(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
  }

  const label = new Date(current + '-02').toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });

  return (
    <div className="month-picker">
      <button type="button" className="mp-arrow" onClick={() => shift(-1)} aria-label="Mois précédent">‹</button>
      <input
        type="month"
        className="mp-input"
        value={current}
        max={new Date().toISOString().slice(0, 7)}
        onChange={(e) => e.target.value && onChange(e.target.value)}
      />
      <span className="mp-label">{label}</span>
      <button type="button" className="mp-arrow" onClick={() => shift(1)} disabled={current >= new Date().toISOString().slice(0, 7)} aria-label="Mois suivant">›</button>
    </div>
  );
}
