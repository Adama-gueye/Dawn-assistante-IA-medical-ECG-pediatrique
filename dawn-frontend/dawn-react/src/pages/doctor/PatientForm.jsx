import React, { useState, useEffect } from 'react';
import { useAppState, useAppDispatch, useAppActions } from '../../context/AppContext';

// Reconstruit une saisie "valeur + unité" naturelle à partir d'une date de
// naissance stockée, pour préremplir le formulaire en mode édition.
function dobToAgeInput(dateNaissance) {
  if (!dateNaissance) return { ageValeur: '', ageUnite: 'mois' };
  const jours = Math.round((Date.now() - new Date(dateNaissance + 'T00:00:00').getTime()) / 86400000);
  if (jours < 60) return { ageValeur: jours, ageUnite: 'jours' };
  if (jours < 2 * 365) return { ageValeur: Math.round(jours / 30.44), ageUnite: 'mois' };
  return { ageValeur: Math.round(jours / 365.25), ageUnite: 'annees' };
}

export default function PatientForm() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const { submitPatientForm } = useAppActions();
  const editing = state.editingPatientId ? state.dossiers.find((p) => p.id === state.editingPatientId) : null;

  const blank = { first: '', last: '', ageValeur: '', ageUnite: 'mois', sex: '', blood: '', history: '', allergies: '', vaccinations: '', notes: '' };
  const fromDossier = (d) => ({
    id: d.id,
    first: d.prenom_enfant, last: d.nom_enfant, sex: d.sexe || '',
    ...dobToAgeInput(d.date_naissance),
    blood: d.groupe_sanguin || '', history: d.antecedents || '', allergies: d.allergies || '',
    vaccinations: d.vaccinations || '', notes: d.notes_complementaires || '',
  });
  const [form, setForm] = useState(blank);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm(editing ? fromDossier(editing) : blank);
    setError('');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.editingPatientId]);

  function set(field, value) { setForm((f) => ({ ...f, [field]: value })); }

  async function submit() {
    if (!form.first.trim() || !form.last.trim() || form.ageValeur === '' || !form.sex) {
      setError("Merci de renseigner au minimum le prénom, le nom, l'âge et le sexe.");
      return;
    }
    setError('');
    setSaving(true);
    try {
      await submitPatientForm({ ...form, first: form.first.trim(), last: form.last.trim(), ageValeur: Number(form.ageValeur) });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="ca active">
      <div className="bc"><a onClick={() => dispatch({ type: 'DOC_NAV', view: 'patients' })}>Mes Patients</a><span className="sep">›</span><span>{editing ? 'Modifier' : 'Nouveau patient'}</span></div>
      <div className="phdr"><h1>{editing ? 'Modifier le Dossier Patient' : 'Nouveau Patient'}</h1><p>{editing ? `${editing.prenom_enfant} ${editing.nom_enfant}` : "Créez la fiche médicale de l'enfant."}</p></div>
      <div className="form-card form-card-accent doc">
        <div className="form-card-body">
          <div className="fg-row">
            <div className="fg"><label className="fg-label">Prénom <span className="req">*</span></label><input className="fi" placeholder="Ex: Aminata" value={form.first} onChange={(e) => set('first', e.target.value)} /></div>
            <div className="fg"><label className="fg-label">Nom <span className="req">*</span></label><input className="fi" placeholder="Ex: Diallo" value={form.last} onChange={(e) => set('last', e.target.value)} /></div>
          </div>
          <div className="fg-row-3">
            <div className="fg">
              <label className="fg-label">Âge <span className="req">*</span></label>
              <div style={{ display: 'flex', gap: 8 }}>
                <input className="fi" type="number" min="0" placeholder="Ex: 5" value={form.ageValeur} onChange={(e) => set('ageValeur', e.target.value)} style={{ flex: 1 }} />
                <select className="fi" value={form.ageUnite} onChange={(e) => set('ageUnite', e.target.value)} style={{ flex: 1 }}>
                  <option value="jours">Jours</option>
                  <option value="mois">Mois</option>
                  <option value="annees">Années</option>
                </select>
              </div>
              <div className="fg-help">Pédiatrique : 0–14 ans</div>
            </div>
            <div className="fg"><label className="fg-label">Sexe <span className="req">*</span></label><select className="fi" value={form.sex} onChange={(e) => set('sex', e.target.value)}><option value="">— Sélectionner —</option><option value="M">♂ Masculin</option><option value="F">♀ Féminin</option></select></div>
            <div className="fg"><label className="fg-label">Groupe sanguin</label><select className="fi" value={form.blood} onChange={(e) => set('blood', e.target.value)}><option value="">— Sélectionner —</option>{['A+','A−','B+','B−','AB+','AB−','O+','O−'].map((b) => <option key={b}>{b}</option>)}</select></div>
          </div>
          <div className="fg"><label className="fg-label">Antécédents médicaux</label><textarea placeholder="Prématurité, chirurgies, hospitalisations, suivi en cours..." value={form.history} onChange={(e) => set('history', e.target.value)} /></div>
          <div className="fg"><label className="fg-label">Allergies</label><input className="fi" placeholder="Ex: Pénicilline, Latex (séparées par une virgule)" value={form.allergies} onChange={(e) => set('allergies', e.target.value)} /></div>
          <div className="fg"><label className="fg-label">Vaccinations</label><textarea placeholder="Calendrier vaccinal, rappels..." value={form.vaccinations} onChange={(e) => set('vaccinations', e.target.value)} /></div>
          <div className="fg"><label className="fg-label">Notes complémentaires</label><textarea placeholder="Informations additionnelles, observations cliniques..." value={form.notes} onChange={(e) => set('notes', e.target.value)} /></div>
          {error && <div style={{ color: 'var(--red)', fontSize: 13, marginTop: 8 }}>{error}</div>}
          <div className="btn-row">
            <button className="btn btn-primary" onClick={submit} disabled={saving}>{saving ? '⏳ Enregistrement...' : (editing ? '💾 Sauvegarder' : '✅ Enregistrer le patient')}</button>
            <button className="btn btn-secondary" onClick={() => dispatch({ type: 'DOC_NAV', view: 'patients' })}>Annuler</button>
          </div>
        </div>
      </div>
    </div>
  );
}
