import React from 'react';
import { useAppState } from '../context/AppContext';

export default function ToastHost() {
  const state = useAppState();
  return (
    <div className="toast-wrap">
      {state.toasts.map((t) => (
        <div key={t.id} className={'toast' + (t.tone ? ' ' + t.tone : '')}>{t.message}</div>
      ))}
    </div>
  );
}
