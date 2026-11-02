import React, { createContext, useContext, useState, useCallback, useRef } from 'react';

const ConfirmContext = createContext(null);

export function ConfirmProvider({ children }) {
  const [modal, setModal] = useState(null); // {title, message, okLabel, tone}
  const resolver = useRef(null);

  const confirm = useCallback(({ title, message, okLabel = 'Confirmer', tone }) => {
    setModal({ title, message, okLabel, tone });
    return new Promise((resolve) => {
      resolver.current = resolve;
    });
  }, []);

  const close = useCallback((result) => {
    setModal(null);
    if (resolver.current) {
      resolver.current(result);
      resolver.current = null;
    }
  }, []);

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {modal && (
        <div className="modal-ov open" onClick={(e) => { if (e.target === e.currentTarget) close(false); }}>
          <div className="modal" style={{ position: 'relative', maxWidth: 420 }}>
            <div className="modal-top">
              <div className="modal-av">⚠</div>
              <div><div className="modal-nm">{modal.title}</div></div>
              <button className="modal-cls" onClick={() => close(false)}>✕</button>
            </div>
            <div className="modal-body">
              <p style={{ fontSize: 14, color: 'var(--text2)', lineHeight: 1.6 }}>{modal.message}</p>
            </div>
            <div className="modal-acts">
              <button className={modal.tone === 'danger' ? 'btn-danger' : 'btn-p'} style={{ fontSize: 13, height: 40, padding: '0 20px' }} onClick={() => close(true)}>
                {modal.okLabel}
              </button>
              <button className="btn-o" style={{ fontSize: 13, height: 40, padding: '0 20px' }} onClick={() => close(false)}>Annuler</button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const ctx = useContext(ConfirmContext);
  if (!ctx) throw new Error('useConfirm must be used within ConfirmProvider');
  return ctx;
}
