import React, { useState, useEffect } from 'react';
import { useAppState, useAppActions } from '../../context/AppContext';
import { initials } from '../../utils/helpers';

const SPECIALTIES = ['Cardiologie', 'Pédiatrie', 'Généraliste', 'Neurologie', 'Chirurgie', 'Autre'];

export default function ProfilePage() {
  const state = useAppState();
  const { saveProfile, changePassword } = useAppActions();
  const user = state.currentUser;

  const [info, setInfo] = useState({ prenom: '', nom: '', specialite: '' });
  const [savingInfo, setSavingInfo] = useState(false);

  const [pw, setPw] = useState({ ancien: '', nouveau: '', confirmation: '' });
  const [showPw, setShowPw] = useState(false);
  const [pwError, setPwError] = useState('');
  const [savingPw, setSavingPw] = useState(false);

  useEffect(() => {
    if (user) setInfo({ prenom: user.prenom || '', nom: user.nom || '', specialite: user.specialite || '' });
  }, [user]);

  if (!user) {
    return (
      <div className="ca active">
        <div className="empty-state"><div className="ico">⏳</div><div className="txt">Chargement du profil...</div></div>
      </div>
    );
  }

  const unchanged = info.prenom.trim() === user.prenom && info.nom.trim() === user.nom && info.specialite === (user.specialite || '');
  const specialties = info.specialite && !SPECIALTIES.includes(info.specialite) ? [info.specialite, ...SPECIALTIES] : SPECIALTIES;

  async function submitInfo() {
    if (!info.prenom.trim() || !info.nom.trim() || !info.specialite) return;
    setSavingInfo(true);
    try {
      await saveProfile({ prenom: info.prenom.trim(), nom: info.nom.trim(), specialite: info.specialite });
    } finally {
      setSavingInfo(false);
    }
  }

  async function submitPassword() {
    if (!pw.ancien || !pw.nouveau || !pw.confirmation) return setPwError('Merci de remplir les trois champs.');
    if (pw.nouveau.length < 8) return setPwError('Le nouveau mot de passe doit contenir au moins 8 caractères.');
    if (pw.nouveau !== pw.confirmation) return setPwError('La confirmation ne correspond pas au nouveau mot de passe.');
    if (pw.nouveau === pw.ancien) return setPwError("Le nouveau mot de passe doit être différent de l'ancien.");
    setPwError('');
    setSavingPw(true);
    try {
      const ok = await changePassword(pw.ancien, pw.nouveau);
      if (ok) setPw({ ancien: '', nouveau: '', confirmation: '' });
    } finally {
      setSavingPw(false);
    }
  }

  const memberSince = user.date_creation ? new Date(user.date_creation).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' }) : '—';

  return (
    <div className="ca active">
      <div className="phdr"><h1>Mon profil</h1><p>Consultez vos informations et sécurisez votre compte.</p></div>

      <div className="pt-hdr-card">
        <div className="pt-hdr-av">{initials(user.prenom, user.nom)}</div>
        <div>
          <div className="pt-hdr-nm">Dr. {user.prenom} {user.nom}</div>
          <div className="pt-hdr-meta"><span>{user.specialite || 'Médecin'}</span><span>✉️ {user.email}</span><span>Membre depuis le {memberSince}</span></div>
        </div>
      </div>

      <div className="two-col">
        <div className="form-card form-card-accent doc">
          <div className="form-card-body">
            <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>Informations personnelles</h2>
            <div className="fg-row">
              <div className="fg"><label className="fg-label">Prénom</label><input className="fi" value={info.prenom} onChange={(e) => setInfo({ ...info, prenom: e.target.value })} /></div>
              <div className="fg"><label className="fg-label">Nom</label><input className="fi" value={info.nom} onChange={(e) => setInfo({ ...info, nom: e.target.value })} /></div>
            </div>
            <div className="fg">
              <label className="fg-label">Spécialité</label>
              <select className="fi" value={info.specialite} onChange={(e) => setInfo({ ...info, specialite: e.target.value })}>
                <option value="">— Sélectionner —</option>
                {specialties.map((sp) => <option key={sp}>{sp}</option>)}
              </select>
            </div>
            <div className="fg-row">
              <div className="fg"><label className="fg-label">E-mail</label><input className="fi" value={user.email} disabled /><div className="fg-help">Identifiant de connexion, non modifiable ici.</div></div>
              <div className="fg"><label className="fg-label">Numéro d'ordre</label><input className="fi" value={user.numero_ordre || '—'} disabled /><div className="fg-help">Géré par l'administrateur.</div></div>
            </div>
            <div className="btn-row">
              <button className="btn btn-primary" onClick={submitInfo} disabled={savingInfo || unchanged || !info.prenom.trim() || !info.nom.trim() || !info.specialite}>{savingInfo ? '⏳ Enregistrement...' : '💾 Enregistrer'}</button>
            </div>
          </div>
        </div>

        <div className="form-card form-card-accent doc">
          <div className="form-card-body">
            <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 16 }}>Mot de passe</h2>
            <div className="fg"><label className="fg-label">Mot de passe actuel</label><input className="fi" type={showPw ? 'text' : 'password'} autoComplete="current-password" value={pw.ancien} onChange={(e) => setPw({ ...pw, ancien: e.target.value })} /></div>
            <div className="fg"><label className="fg-label">Nouveau mot de passe</label><input className="fi" type={showPw ? 'text' : 'password'} autoComplete="new-password" value={pw.nouveau} onChange={(e) => setPw({ ...pw, nouveau: e.target.value })} /><div className="fg-help">8 caractères minimum.</div></div>
            <div className="fg"><label className="fg-label">Confirmer le nouveau mot de passe</label><input className="fi" type={showPw ? 'text' : 'password'} autoComplete="new-password" value={pw.confirmation} onChange={(e) => setPw({ ...pw, confirmation: e.target.value })} onKeyDown={(e) => { if (e.key === 'Enter') submitPassword(); }} /></div>
            <div className="fg-check"><input type="checkbox" checked={showPw} onChange={(e) => setShowPw(e.target.checked)} /><span>Afficher les mots de passe</span></div>
            {pwError && <div style={{ color: 'var(--red)', fontSize: 13, marginTop: 8 }}>{pwError}</div>}
            <div className="btn-row">
              <button className="btn btn-primary" onClick={submitPassword} disabled={savingPw}>{savingPw ? '⏳ Modification...' : '🔒 Modifier le mot de passe'}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
