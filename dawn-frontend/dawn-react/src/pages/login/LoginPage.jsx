import React, { useState } from 'react';
import Particles from '../../components/Particles';
import MedicalIllustration from '../../components/MedicalIllustration';
import { useAppActions } from '../../context/AppContext';

export default function LoginPage() {
  const { doLogin } = useAppActions();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError('Merci de renseigner votre e-mail et votre mot de passe.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await doLogin(email.trim(), password);
    } catch (err) {
      setError(err.message || 'Identifiants incorrects.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page active">
      <div className="login-bg" />
      <div className="login-grid" />
      <Particles />
      <div className="login-layout">
      <div className="login-card">
        <div className="logo-ctr">
          <svg viewBox="0 0 64 64" fill="none">
            <path d="M32 8C22 8 14 16 14 26C14 32 17 36 22 39C24 40.5 25 42.5 25 45L25 50L39 50L39 45C39 42.5 40 40.5 42 39C47 36 50 32 50 26C50 16 42 8 32 8Z" stroke="rgba(130,160,255,.7)" strokeWidth="2" fill="none" />
            <path d="M22 26C24 22 28 20 32 20" stroke="rgba(130,160,255,.4)" strokeWidth="1.5" strokeLinecap="round" fill="none" />
            <path d="M32 20C36 20 40 22 42 26" stroke="rgba(130,160,255,.4)" strokeWidth="1.5" strokeLinecap="round" fill="none" />
            <rect x="28" y="38" width="8" height="12" rx="1.5" fill="rgba(92,126,239,.8)" />
            <rect x="24" y="42" width="16" height="4" rx="1.5" fill="rgba(92,126,239,.8)" />
            <circle cx="32" cy="20" r="2" fill="rgba(100,150,255,.3)" />
            <circle cx="32" cy="44" r="10" stroke="rgba(92,126,239,.2)" strokeWidth=".8" fill="none">
              <animate attributeName="r" values="10;13;10" dur="3s" repeatCount="indefinite" />
              <animate attributeName="opacity" values=".2;.05;.2" dur="3s" repeatCount="indefinite" />
            </circle>
          </svg>
        </div>
        <h1 className="l-title">DAWN</h1>
        <p className="l-sub">Assistant Médical Intelligent</p>

        <form onSubmit={handleSubmit} autoComplete="off">
          <div className="inp-grp">
            <label>Adresse e-mail</label>
            <div className="inp-w">
              <input type="email" placeholder="nom@hopital.sn" value={email} onChange={(e) => setEmail(e.target.value)} required />
              <svg className="ii" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="3" /><path d="M22 7L13.5 13.5C12.8 14 11.2 14 10.5 13.5L2 7" /></svg>
            </div>
          </div>
          <div className="inp-grp">
            <label>Mot de passe</label>
            <div className="inp-w">
              <input type={showPw ? 'text' : 'password'} placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required />
              <svg className="ii" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0110 0v4" /></svg>
              <button type="button" className="tog-pw" onClick={() => setShowPw((s) => !s)}>
                {!showPw ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" /><path d="M14.12 14.12a3 3 0 01-4.24-4.24" /><line x1="1" y1="1" x2="23" y2="23" /></svg>
                )}
              </button>
            </div>
          </div>
          {error && <div style={{ color: '#ff8a80', fontSize: 12, marginTop: -10, marginBottom: 16, textAlign: 'center' }}>{error}</div>}
          <button type="submit" className="btn-lgn" disabled={loading}>{loading ? 'Connexion...' : 'Se connecter'}</button>
        </form>
        <div className="first-link">Pas encore de compte ? Contactez votre administrateur DAWN.</div>
        <div className="sec-badge"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>Connexion sécurisée · Données chiffrées</div>
      </div>
      <MedicalIllustration
        title="Un assistant IA pensé pour la cardiologie pédiatrique"
        subtitle="Analyse ECG et aide à la décision clinique pour les médecins."
      />
      </div>
    </div>
  );
}
