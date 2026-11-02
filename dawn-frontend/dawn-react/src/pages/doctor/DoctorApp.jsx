import React, { useEffect } from 'react';
import { useAppState, useAppActions } from '../../context/AppContext';
import DoctorSidebar from './DoctorSidebar';
import Dashboard from './Dashboard';
import PatientsGrid from './PatientsGrid';
import PatientForm from './PatientForm';
import PatientRecord from './PatientRecord';
import PersonalSessions from './PersonalSessions';
import ProfilePage from './ProfilePage';

export default function DoctorApp() {
  const state = useAppState();
  const { loadDossiers, loadSessions, loadCurrentUser } = useAppActions();

  useEffect(() => {
    loadCurrentUser();
    loadDossiers();
    loadSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  let content;
  switch (state.doctorView) {
    case 'patients': content = <PatientsGrid />; break;
    case 'patient-form': content = <PatientForm />; break;
    case 'record': content = <PatientRecord />; break;
    case 'sessions': content = <PersonalSessions />; break;
    case 'profile': content = <ProfilePage />; break;
    default: content = <Dashboard />;
  }

  return (
    <div className="page active">
      <div className="app-shell">
        <DoctorSidebar />
        <div className="mw">
          <header className="tb">
            <div className="sr">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
              <input type="text" placeholder="Rechercher un patient..." />
            </div>
            <div className="tb-r">
              <button className="tb-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 01-3.46 0" /></svg><span className="ndot" /></button>
              <span className="tb-date">{new Date().toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
            </div>
          </header>
          <main className="ct">{content}</main>
        </div>
      </div>
    </div>
  );
}
