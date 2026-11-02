import React from 'react';
import { AppProvider, useAppState } from './context/AppContext';
import { ConfirmProvider } from './context/ConfirmContext';
import ToastHost from './components/ToastHost';
import LoginPage from './pages/login/LoginPage';
import DoctorApp from './pages/doctor/DoctorApp';
import ChatPage from './pages/chat/ChatPage';
import AdminApp from './pages/admin/AdminApp';

function Router() {
  const state = useAppState();
  switch (state.page) {
    case 'doctor': return <DoctorApp />;
    case 'chat': return <ChatPage />;
    case 'admin': return <AdminApp />;
    default: return <LoginPage />;
  }
}

export default function App() {
  return (
    <AppProvider>
      <ConfirmProvider>
        <Router />
        <ToastHost />
      </ConfirmProvider>
    </AppProvider>
  );
}
