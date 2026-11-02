import React from 'react';
import { useAppState, useAppDispatch, useAppActions } from '../../context/AppContext';
import { useConfirm } from '../../context/ConfirmContext';
import DeleteSessionButton from '../../components/DeleteSessionButton';
import { ageFromDob, sexLabel, initials, allergiesToList, shortDate } from '../../utils/helpers';

const BORDER_CLASSES = ['blue-border', 'green-border', 'orange-border'];
const ICON_CLASSES = ['blue', 'green', 'orange'];
const ALLERGY_COLORS = ['red', 'orange', 'blue'];

export default function PatientRecord() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const { deleteDossier } = useAppActions();
  const confirm = useConfirm();
  const p = state.dossiers.find((x) => x.id === state.currentRecordId);

  if (!p) {
    return (
      <div className="ca active">
        <div className="empty-state"><div className="ico">👤</div><div className="txt">Patient introuvable</div></div>
      </div>
    );
  }

  const sessions = state.sessions.filter((s) => s.dossier_patient_id === p.id);

  async function supprimerDossier() {
    const n = sessions.length;
    const ok = await confirm({
      title: `Supprimer le dossier de ${p.prenom_enfant} ${p.nom_enfant} ?`,
      message: n > 0
        ? `Ses ${n} session${n > 1 ? 's' : ''}, tous les messages et les fichiers ECG associés seront aussi supprimés définitivement. Cette action est irréversible.`
        : 'Le dossier sera supprimé définitivement. Cette action est irréversible.',
      okLabel: 'Supprimer le dossier',
      tone: 'danger',
    });
    if (ok) await deleteDossier(p.id);
  }
  const allergies = allergiesToList(p.allergies);

  return (
    <div className="ca active">
      <div className="bc">
        <a onClick={() => dispatch({ type: 'DOC_NAV', view: 'dashboard' })}>Dashboard</a><span className="sep">›</span>
        <a onClick={() => dispatch({ type: 'DOC_NAV', view: 'patients' })}>Mes Patients</a><span className="sep">›</span>
        <span>{p.prenom_enfant} {p.nom_enfant}</span>
      </div>
      <div className="pt-hdr-card">
        <div className="pt-hdr-av">{initials(p.prenom_enfant, p.nom_enfant)}</div>
        <div><div className="pt-hdr-nm">{p.prenom_enfant} {p.nom_enfant}</div><div className="pt-hdr-meta"><span>{ageFromDob(p.date_naissance)}</span><span>{sexLabel(p.sexe)}</span><span>🩸 {p.groupe_sanguin || '—'}</span></div></div>
        <div className="pt-hdr-right">
          <button className="btn-edit" onClick={() => { dispatch({ type: 'SET_EDITING_PATIENT', id: p.id }); dispatch({ type: 'DOC_NAV', view: 'patient-form' }); }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 14, height: 14 }}><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" /><path d="M18.5 2.5a2.12 2.12 0 013 3L12 15l-4 1 1-4 9.5-9.5z" /></svg> Modifier
          </button>
          <button className="btn-del-outline" onClick={supprimerDossier}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ width: 14, height: 14 }}><polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" /></svg> Supprimer
          </button>
        </div>
      </div>
      <div className="two-col">
        <div className="clinic-card">
          <div className="clinic-hdr">🏥 Informations cliniques</div>
          <div className="clinic-body">
            <div className="clinic-row"><div className="lbl">Antécédents médicaux</div><div className="val">{p.antecedents || 'Aucun antécédent renseigné.'}</div></div>
            <div className="clinic-row">
              <div className="lbl">Allergies</div>
              <div className="allergy-chips">
                {allergies.length
                  ? allergies.map((a, i) => <span key={a} className={'chip ' + ALLERGY_COLORS[i % 3]}>{a}</span>)
                  : <span style={{ fontSize: 13, color: 'var(--g400)' }}>Aucune allergie connue</span>}
              </div>
            </div>
            <div className="clinic-row"><div className="lbl">Vaccinations</div><div className="val">{p.vaccinations || '—'}</div></div>
            <div className="clinic-row"><div className="lbl">Notes complémentaires</div><div className="val">{p.notes_complementaires || 'Aucune note.'}</div></div>
          </div>
        </div>
        <div>
          <div className="scard">
            <div className="shdr">
              <h2>Sessions</h2>
              <button className="btn-p" style={{ height: 36, padding: '0 18px', fontSize: 12 }} onClick={() => dispatch({ type: 'GO_CHAT', dossierId: p.id })}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ width: 14, height: 14 }}><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>Nouvelle Session
              </button>
            </div>
            <div style={{ padding: '18px 22px' }}>
              {sessions.length === 0 ? (
                <div className="empty-state"><div className="ico">💬</div><div className="txt">Aucune session pour ce patient</div></div>
              ) : sessions.map((s, i) => (
                <div key={s.id} className={'sess-card ' + BORDER_CLASSES[i % 3]} onClick={() => dispatch({ type: 'GO_CHAT', dossierId: p.id, sessionId: s.id })}>
                  <div className={'sess-ico ' + ICON_CLASSES[i % 3]}><span style={{ fontSize: 16 }}>💬</span></div>
                  <div><div className="sess-title">{s.titre}</div><div className="sess-meta">Consultation</div></div>
                  <div className="sess-date">{shortDate(s.date_session)}</div>
                  <DeleteSessionButton session={s} />
                  <div className="sess-arrow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6" /></svg></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
