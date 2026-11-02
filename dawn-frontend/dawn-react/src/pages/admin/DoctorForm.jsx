import React, { useState } from 'react';
import { useAppDispatch, useAppActions } from '../../context/AppContext';

export default function DoctorForm() {
  const dispatch = useAppDispatch();
  const { submitDoctorForm } = useAppActions();
  const [form, setForm] = useState({ first: '', last: '', email: '', password: '', specialty: '', numeroOrdre: '' });
  const [status, setStatus] = useState('active');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  function set(field, value) { setForm((f) => ({ ...f, [field]: value })); }

  async function submit() {
    if (!form.first.trim() || !form.last.trim() || !form.email.trim() || !form.password.trim() || !form.specialty || !form.numeroOrdre.trim()) {
      setError('Merci de renseigner tous les champs obligatoires.');
      return;
    }
    setError('');
    setSaving(true);
    try {
      await submitDoctorForm(
        { ...form, first: form.first.trim(), last: form.last.trim(), email: form.email.trim(), numeroOrdre: form.numeroOrdre.trim() },
        status
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="ca active">
      <div className="bc"><a onClick={() => dispatch({ type: 'ADMIN_NAV', view: 'medecins' })}>Médecins</a><span className="sep">›</span><span>Nouveau médecin</span></div>
      <div className="phdr"><h1>Créer un Médecin</h1><p>Le médecin pourra se connecter avec cet e-mail et ce mot de passe.</p></div>
      <div className="form-card form-card-accent adm">
        <div className="form-card-body">
          <div className="fg-row">
            <div className="fg"><label className="fg-label">Prénom <span className="req">*</span></label><input className="fi" placeholder="Ex: Ibrahima" value={form.first} onChange={(e) => set('first', e.target.value)} /></div>
            <div className="fg"><label className="fg-label">Nom <span className="req">*</span></label><input className="fi" placeholder="Ex: Sy" value={form.last} onChange={(e) => set('last', e.target.value)} /></div>
          </div>
          <div className="fg-row">
            <div className="fg"><label className="fg-label">E-mail professionnel <span className="req">*</span></label><input className="fi" type="email" placeholder="nom@hopital.sn" value={form.email} onChange={(e) => set('email', e.target.value)} /></div>
            <div className="fg"><label className="fg-label">Mot de passe temporaire <span className="req">*</span></label><input className="fi" type="text" placeholder="Ex: Dawn2026!" value={form.password} onChange={(e) => set('password', e.target.value)} /></div>
          </div>
          <div className="fg-row">
            <div className="fg"><label className="fg-label">Spécialité <span className="req">*</span></label>
              <select className="fi" value={form.specialty} onChange={(e) => set('specialty', e.target.value)}>
                <option value="">— Sélectionner —</option><option>Cardiologie</option><option>Pédiatrie</option><option>Généraliste</option><option>Neurologie</option><option>Chirurgie</option><option>Autre</option>
              </select>
            </div>
            <div className="fg"><label className="fg-label">Numéro d'ordre <span className="req">*</span></label><input className="fi" placeholder="Ex: SN-CARD-2024-018" value={form.numeroOrdre} onChange={(e) => set('numeroOrdre', e.target.value)} /></div>
          </div>
          <div className="fg">
            <label className="fg-label">Statut initial</label>
            <div className="fg-check"><input type="radio" name="dfStatus" checked={status === 'active'} onChange={() => setStatus('active')} /><span>✅ Actif — le médecin peut se connecter immédiatement</span></div>
            <div className="fg-check"><input type="radio" name="dfStatus" checked={status === 'pending'} onChange={() => setStatus('pending')} /><span>⏳ En attente — activation manuelle par l'admin</span></div>
          </div>
          {error && <div style={{ color: 'var(--red)', fontSize: 13, marginTop: 8 }}>{error}</div>}
          <div className="btn-row">
            <button className="btn btn-primary" onClick={submit} disabled={saving}>{saving ? '⏳ Création...' : '🩺 Créer le médecin'}</button>
            <button className="btn btn-secondary" onClick={() => dispatch({ type: 'ADMIN_NAV', view: 'medecins' })}>Annuler</button>
          </div>
        </div>
      </div>
    </div>
  );
}
