import React from 'react';
import { useAppState, useAppActions } from '../context/AppContext';
import { useConfirm } from '../context/ConfirmContext';

// Bouton « corbeille » réutilisé dans le chat, la liste des sessions personnelles et le dossier patient.
export default function DeleteSessionButton({ session }) {
  const state = useAppState();
  const { deleteSession } = useAppActions();
  const confirm = useConfirm();
  // pas de suppression pendant qu'une réponse est en cours pour cette session
  const enCours = !!state.pending && state.pending.sessionId === session.id;

  async function onClick(e) {
    e.stopPropagation();
    const ok = await confirm({
      title: 'Supprimer cette session ?',
      message: `« ${session.titre} » et tous ses messages seront supprimés définitivement, ainsi que les fichiers ECG associés.`,
      okLabel: 'Supprimer',
      tone: 'danger',
    });
    if (ok) await deleteSession(session.id);
  }

  return (
    <button
      type="button"
      className="icon-del"
      title={enCours ? 'Réponse en cours…' : 'Supprimer la session'}
      aria-label="Supprimer la session"
      disabled={enCours}
      onClick={onClick}
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" /><path d="M10 11v6" /><path d="M14 11v6" /><path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2" /></svg>
    </button>
  );
}
