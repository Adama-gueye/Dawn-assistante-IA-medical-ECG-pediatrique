import React from 'react';
import { useAppActions } from '../../context/AppContext';
import { useConfirm } from '../../context/ConfirmContext';

export default function DoctorStatusCells({ doctor }) {
  const { toggleDoctorStatus } = useAppActions();
  const confirm = useConfirm();
  const isActive = doctor.est_actif;

  async function handleToggle() {
    const willActivate = !isActive;
    const ok = await confirm({
      title: willActivate ? 'Activer ce médecin ?' : 'Désactiver ce médecin ?',
      message: `Dr. ${doctor.prenom} ${doctor.nom} — ${willActivate ? 'pourra de nouveau se connecter à DAWN.' : 'ne pourra plus se connecter à DAWN tant que le compte est désactivé.'}`,
      okLabel: willActivate ? 'Activer' : 'Désactiver',
      tone: willActivate ? undefined : 'danger',
    });
    if (ok) toggleDoctorStatus(doctor.id, willActivate);
  }

  return (
    <>
      <td>{isActive ? <span className="status-chip active">✅ Actif</span> : <span className="status-chip inactive">❌ Inactif</span>}</td>
      <td>
        {isActive
          ? <button className="adm-btn-sm deactivate" onClick={handleToggle}>Désactiver</button>
          : <button className="adm-btn-sm activate" onClick={handleToggle}>Activer</button>}
      </td>
    </>
  );
}
