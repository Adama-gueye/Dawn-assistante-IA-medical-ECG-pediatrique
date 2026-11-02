import React, { useEffect } from 'react';
import { useAppState, useAppActions } from '../../context/AppContext';
import AdminSidebar from './AdminSidebar';
import AdminDashboard from './AdminDashboard';
import DoctorsTable from './DoctorsTable';
import DoctorForm from './DoctorForm';
import StatsPage from './StatsPage';

export default function AdminApp() {
  const state = useAppState();
  const { loadDoctors, loadCurrentUser } = useAppActions();

  useEffect(() => {
    loadCurrentUser();
    loadDoctors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  let content;
  switch (state.adminView) {
    case 'medecins': content = <DoctorsTable />; break;
    case 'doctor-form': content = <DoctorForm />; break;
    case 'stats': content = <StatsPage />; break;
    default: content = <AdminDashboard />;
  }

  return (
    <div className="page active">
      <div className="app-shell">
        <AdminSidebar />
        <div className="mw">
          <header className="tb">
            <div style={{ fontSize: 18, fontWeight: 700 }}>Administration DAWN</div>
            <div className="tb-r"><span className="tb-date">{new Date().toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })}</span></div>
          </header>
          <main className="ct">{content}</main>
        </div>
      </div>
    </div>
  );
}
