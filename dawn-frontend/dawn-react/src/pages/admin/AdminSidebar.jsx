import React from 'react';
import { useAppState, useAppDispatch, useAppActions } from '../../context/AppContext';

export default function AdminSidebar() {
  const state = useAppState();
  const dispatch = useAppDispatch();
  const { logout } = useAppActions();
  const nav = (view) => dispatch({ type: 'ADMIN_NAV', view });

  return (
    <aside className="sb sb-admin">
      <div className="sb-hdr">
        <div className="sb-logo">
          <svg viewBox="0 0 64 64" fill="none" style={{ width: 34, height: 34 }}><path d="M32 8C22 8 14 16 14 26C14 32 17 36 22 39C24 40.5 25 42.5 25 45L25 50L39 50L39 45C39 42.5 40 40.5 42 39C47 36 50 32 50 26C50 16 42 8 32 8Z" stroke="rgba(200,215,255,.8)" strokeWidth="2" fill="none" /><rect x="28" y="38" width="8" height="12" rx="1.5" fill="rgba(140,170,255,.85)" /><rect x="24" y="42" width="16" height="4" rx="1.5" fill="rgba(140,170,255,.85)" /></svg>
          <div><div className="brand">DAWN</div><div className="tag">Administration</div></div>
        </div>
      </div>
      <nav className="sb-nav">
        <a className={'ni' + (state.adminView === 'dashboard' ? ' active' : '')} onClick={() => nav('dashboard')}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></svg>Dashboard
        </a>
        <a className={'ni' + (['medecins', 'doctor-form'].includes(state.adminView) ? ' active' : '')} onClick={() => nav('medecins')}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 00-3-3.87" /><path d="M16 3.13a4 4 0 010 7.75" /></svg>Médecins
        </a>
        <a className={'ni' + (state.adminView === 'stats' ? ' active' : '')} onClick={() => nav('stats')}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 20V10" /><path d="M12 20V4" /><path d="M6 20v-6" /></svg>Statistiques
        </a>
        <a className="ni logout" onClick={logout}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>Déconnexion
        </a>
      </nav>
    </aside>
  );
}
