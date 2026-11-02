import React from 'react';
import { useAppState, useAppDispatch } from '../../context/AppContext';
import DoctorStatusCells from './DoctorStatusCells';

export default function DoctorsTable() {
  const state = useAppState();
  const dispatch = useAppDispatch();

  return (
    <div className="ca active">
      <div className="phdr"><h1>Gestion des Médecins</h1><p>Créez, modifiez et gérez les comptes médecins.</p></div>
      <div className="act-row">
        <button className="btn-p" style={{ height: 40, padding: '0 20px', fontSize: 13 }} onClick={() => dispatch({ type: 'ADMIN_NAV', view: 'doctor-form' })}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: 16, height: 16 }}><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>Créer un médecin
        </button>
      </div>
      <div className="scard">
        <table className="ptbl">
          <thead><tr><th>Nom</th><th>Spécialité</th><th>Email</th><th>N° d'ordre</th><th>Statut</th><th>Actions</th></tr></thead>
          <tbody>
            {state.doctors.length === 0 ? (
              <tr><td colSpan={6}><div className="empty-state"><div className="ico">🩺</div><div className="txt">Aucun médecin pour l'instant</div></div></td></tr>
            ) : state.doctors.map((d) => (
              <tr key={d.id}>
                <td style={{ fontWeight: 600 }}>Dr. {d.prenom} {d.nom}</td>
                <td>{d.specialite}</td>
                <td style={{ color: 'var(--g500)' }}>{d.email}</td>
                <td>{d.numero_ordre}</td>
                <DoctorStatusCells doctor={d} />
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
