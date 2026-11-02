import React, { createContext, useContext, useReducer, useCallback, useRef } from 'react';
import * as authApi from '../api/auth';
import * as dossiersApi from '../api/dossiers';
import * as sessionsApi from '../api/sessions';
import * as adminApi from '../api/admin';
import { getToken, getRole } from '../api/client';

const StateContext = createContext(null);
const DispatchContext = createContext(null);
const ActionsContext = createContext(null);

const initialState = {
  page: getToken() ? (getRole() === 'administrateur' ? 'admin' : 'doctor') : 'login',
  authRole: getToken() ? getRole() : null,
  currentUser: null, // rempli après /auth/me

  doctorView: 'dashboard',
  adminView: 'dashboard',

  dossiers: [],      // DossierPatientOut[]
  sessions: [],       // { ...SessionRAGOut, messages: null | MessageMedecinOut[] }
  doctors: [],         // MedecinOut[] (vue admin)
  stats: null,          // StatistiquesOut (vue admin)
  medecinStats: null,    // StatistiquesMedecinOut (vue medecin)

  editingPatientId: null,
  currentRecordId: null,

  chat: { activeDossierId: null, activeSessionId: null, inputType: 'text' },
  pending: null, // { sessionId, entries } : message envoyé, réponse du serveur attendue

  toasts: [],
};

function reducer(state, action) {
  switch (action.type) {
    case 'GO_PAGE':
      return { ...state, page: action.page };

    case 'LOGIN_SUCCESS':
      return {
        ...state,
        authRole: action.role,
        page: action.role === 'administrateur' ? 'admin' : 'doctor',
        doctorView: 'dashboard',
        adminView: 'dashboard',
      };
    case 'SET_CURRENT_USER':
      return { ...state, currentUser: action.user };
    case 'LOGOUT':
      return { ...initialState, page: 'login', authRole: null };

    case 'DOC_NAV':
      return { ...state, doctorView: action.view };
    case 'ADMIN_NAV':
      return { ...state, adminView: action.view };

    case 'SET_EDITING_PATIENT':
      return { ...state, editingPatientId: action.id };
    case 'SET_DOSSIERS':
      return { ...state, dossiers: action.dossiers };
    case 'ADD_DOSSIER':
      return { ...state, dossiers: [...state.dossiers, action.dossier] };
    case 'UPDATE_DOSSIER':
      return { ...state, dossiers: state.dossiers.map((d) => (d.id === action.dossier.id ? action.dossier : d)) };
    case 'OPEN_RECORD':
      return { ...state, currentRecordId: action.id, page: 'doctor', doctorView: 'record' };

    case 'SET_SESSIONS':
      return { ...state, sessions: action.sessions };
    case 'REFRESH_SESSION_TITLES': {
      const parId = Object.fromEntries(action.sessions.map((x) => [x.id, x]));
      return {
        ...state,
        sessions: state.sessions.map((x) => (parId[x.id] ? { ...x, titre: parId[x.id].titre } : x)),
      };
    }
    case 'REMOVE_SESSION':
      return {
        ...state,
        sessions: state.sessions.filter((x) => x.id !== action.sessionId),
        // session ouverte supprimée : retour à l'écran « nouvelle conversation »
        chat: state.chat.activeSessionId === action.sessionId ? { ...state.chat, activeSessionId: null } : state.chat,
      };
    case 'REMOVE_DOSSIER':
      return {
        ...state,
        dossiers: state.dossiers.filter((d) => d.id !== action.dossierId),
        sessions: state.sessions.filter((x) => x.dossier_patient_id !== action.dossierId),
        currentRecordId: state.currentRecordId === action.dossierId ? null : state.currentRecordId,
      };
    case 'UPDATE_SESSION':
      return {
        ...state,
        sessions: state.sessions.map((x) => (x.id === action.session.id ? { ...x, ...action.session } : x)),
      };
    case 'PENDING_START':
      return { ...state, pending: { sessionId: action.sessionId, entries: action.entries } };
    case 'PENDING_END':
      return { ...state, pending: null };
    case 'MESSAGE_RECEIVED': // ajoute la réponse ET efface l'envoi en cours en une seule mise à jour (pas de doublon à l'écran)
      return {
        ...state,
        pending: null,
        sessions: state.sessions.map((x) =>
          x.id === action.sessionId ? { ...x, messages: [...(x.messages || []), action.message] } : x
        ),
      };
    case 'ADD_SESSION':
      return { ...state, sessions: [...state.sessions, { ...action.session, messages: [] }] };
    case 'SET_SESSION_MESSAGES':
      return {
        ...state,
        sessions: state.sessions.map((s) => (s.id === action.sessionId ? { ...s, messages: action.messages } : s)),
      };
    case 'APPEND_SESSION_MESSAGE':
      return {
        ...state,
        sessions: state.sessions.map((s) =>
          s.id === action.sessionId ? { ...s, messages: [...(s.messages || []), action.message] } : s
        ),
      };

    case 'GO_CHAT':
      return {
        ...state,
        page: 'chat',
        chat: { activeDossierId: action.dossierId ?? null, activeSessionId: action.sessionId ?? null, inputType: 'text' },
      };
    case 'SELECT_SESSION':
      return { ...state, chat: { ...state.chat, activeSessionId: action.id } };
    case 'SET_CHAT_INPUT_TYPE':
      return { ...state, chat: { ...state.chat, inputType: action.inputType } };

    case 'SET_DOCTORS':
      return { ...state, doctors: action.doctors };
    case 'ADD_DOCTOR':
      return { ...state, doctors: [...state.doctors, action.doctor] };
    case 'UPDATE_DOCTOR':
      return { ...state, doctors: state.doctors.map((d) => (d.id === action.doctor.id ? { ...d, ...action.doctor } : d)) };
    case 'SET_STATS':
      return { ...state, stats: action.stats };
    case 'SET_MEDECIN_STATS':
      return { ...state, medecinStats: action.stats };

    case 'ADD_TOAST':
      return { ...state, toasts: [...state.toasts, action.toast] };
    case 'REMOVE_TOAST':
      return { ...state, toasts: state.toasts.filter((t) => t.id !== action.id) };

    default:
      return state;
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  const toastId = useRef(1);

  const toast = useCallback((message, tone = 'info') => {
    const id = toastId.current++;
    dispatch({ type: 'ADD_TOAST', toast: { id, message, tone } });
    setTimeout(() => dispatch({ type: 'REMOVE_TOAST', id }), 4000);
  }, []);

  const errorToast = useCallback((err, fallback) => {
    toast((err && err.message) || fallback, 'error');
  }, [toast]);

  // ---------------- AUTH ----------------
  const doLogin = useCallback(async (email, password) => {
    const data = await authApi.login(email, password);
    dispatch({ type: 'LOGIN_SUCCESS', role: data.role });
    try {
      const user = await authApi.me();
      dispatch({ type: 'SET_CURRENT_USER', user });
    } catch (_) { /* pas bloquant */ }
    return data;
  }, []);

  const logout = useCallback(() => {
    authApi.logout();
    dispatch({ type: 'LOGOUT' });
  }, []);

  const loadCurrentUser = useCallback(async () => {
    try {
      const user = await authApi.me();
      dispatch({ type: 'SET_CURRENT_USER', user });
    } catch (err) {
      // token invalide/expiré
      authApi.logout();
      dispatch({ type: 'LOGOUT' });
    }
  }, []);

  // ---------------- PROFIL ----------------
  const saveProfile = useCallback(async (payload) => {
    try {
      const user = await authApi.modifierProfil(payload);
      dispatch({ type: 'SET_CURRENT_USER', user });
      toast('Profil mis à jour.', 'success');
      return true;
    } catch (err) {
      errorToast(err, 'Impossible de mettre à jour le profil.');
      return false;
    }
  }, [toast, errorToast]);

  const changePassword = useCallback(async (ancien, nouveau) => {
    try {
      await authApi.changerMotDePasse(ancien, nouveau);
      toast('Mot de passe modifié.', 'success');
      return true;
    } catch (err) {
      errorToast(err, 'Impossible de modifier le mot de passe.');
      return false;
    }
  }, [toast, errorToast]);

  // ---------------- DOSSIERS (médecin) ----------------
  const loadDossiers = useCallback(async () => {
    try {
      const dossiers = await dossiersApi.listerDossiers();
      dispatch({ type: 'SET_DOSSIERS', dossiers });
    } catch (err) {
      errorToast(err, 'Impossible de charger les dossiers patients.');
    }
  }, [errorToast]);

  const submitPatientForm = useCallback(async (form) => {
    const payload = {
      prenom_enfant: form.first,
      nom_enfant: form.last,
      age_valeur: form.ageValeur,
      age_unite: form.ageUnite,
      sexe: form.sex || null,
      groupe_sanguin: form.blood || null,
      antecedents: form.history || null,
      allergies: form.allergies || null,
      notes_complementaires: form.notes || null,
    };
    try {
      if (form.id) {
        const updated = await dossiersApi.modifierDossier(form.id, payload);
        dispatch({ type: 'UPDATE_DOSSIER', dossier: updated });
        toast('Dossier mis à jour.', 'success');
        dispatch({ type: 'OPEN_RECORD', id: updated.id });
      } else {
        const created = await dossiersApi.creerDossier(payload);
        dispatch({ type: 'ADD_DOSSIER', dossier: created });
        toast('Patient enregistré.', 'success');
        dispatch({ type: 'OPEN_RECORD', id: created.id });
      }
    } catch (err) {
      errorToast(err, "Impossible d'enregistrer le dossier.");
    }
  }, [toast, errorToast]);

  // ---------------- SESSIONS + MESSAGES ----------------
  const loadSessions = useCallback(async () => {
    try {
      const sessions = await sessionsApi.listerSessions();
      dispatch({ type: 'SET_SESSIONS', sessions: sessions.map((s) => ({ ...s, messages: null })) });
    } catch (err) {
      errorToast(err, 'Impossible de charger les sessions.');
    }
  }, [errorToast]);

  // Le backend renomme la session au 1er message (titre adapte au sujet) :
  // on relit la liste et on ne fusionne que les titres, sans toucher aux messages.
  const refreshSessionTitles = useCallback(async () => {
    try {
      const sessions = await sessionsApi.listerSessions();
      dispatch({ type: 'REFRESH_SESSION_TITLES', sessions });
    } catch (_) { /* silencieux : le titre sera à jour au prochain chargement */ }
  }, []);

  const loadSessionMessages = useCallback(async (sessionId) => {
    try {
      const messages = await sessionsApi.listerMessages(sessionId);
      dispatch({ type: 'SET_SESSION_MESSAGES', sessionId, messages });
    } catch (err) {
      errorToast(err, "Impossible de charger les messages de la session.");
    }
  }, [errorToast]);

  const newSessionFor = useCallback(async (dossierPatientId, titre) => {
    try {
      const session = await sessionsApi.creerSession({ titre, dossier_patient_id: dossierPatientId ?? null });
      dispatch({ type: 'ADD_SESSION', session });
      return session;
    } catch (err) {
      errorToast(err, 'Impossible de créer la session.');
      return null;
    }
  }, [errorToast]);

  // Une session n'est créée qu'au premier message (comme une conversation Claude) :
  // le serveur la nomme ensuite d'après le sujet, et le médecin peut la renommer.
  const startSession = useCallback(async (dossierPatientId) => {
    const session = await newSessionFor(dossierPatientId, 'Nouvelle session');
    if (session) dispatch({ type: 'SELECT_SESSION', id: session.id });
    return session;
  }, [newSessionFor]);

  const renameSession = useCallback(async (sessionId, titre) => {
    try {
      const session = await sessionsApi.renommerSession(sessionId, titre);
      dispatch({ type: 'UPDATE_SESSION', session });
      return true;
    } catch (err) {
      errorToast(err, 'Impossible de renommer la session.');
      return false;
    }
  }, [errorToast]);

  const deleteSession = useCallback(async (sessionId) => {
    try {
      await sessionsApi.supprimerSession(sessionId);
      dispatch({ type: 'REMOVE_SESSION', sessionId });
      toast('Session supprimée.', 'success');
      return true;
    } catch (err) {
      errorToast(err, 'Impossible de supprimer la session.');
      return false;
    }
  }, [toast, errorToast]);

  const deleteDossier = useCallback(async (dossierId) => {
    try {
      await dossiersApi.supprimerDossier(dossierId);
      dispatch({ type: 'REMOVE_DOSSIER', dossierId });
      dispatch({ type: 'DOC_NAV', view: 'patients' });
      toast('Dossier supprimé.', 'success');
      return true;
    } catch (err) {
      errorToast(err, 'Impossible de supprimer le dossier.');
      return false;
    }
  }, [toast, errorToast]);

  // Envoi optimiste : la question s'affiche tout de suite (state.pending) avec l'indicateur
  // « DAWN rédige... » pendant que le serveur travaille. Renvoie true/false pour que l'écran
  // puisse remettre le texte dans la zone de saisie en cas d'échec.
  const runSend = useCallback(async (sessionId, entries, call, messageErreur) => {
    dispatch({ type: 'PENDING_START', sessionId, entries });
    try {
      const message = await call();
      dispatch({ type: 'MESSAGE_RECEIVED', sessionId, message });
      refreshSessionTitles();
      return true;
    } catch (err) {
      dispatch({ type: 'PENDING_END' });
      errorToast(err, messageErreur);
      return false;
    }
  }, [errorToast, refreshSessionTitles]);

  const sendDoctorText = useCallback((sessionId, text) =>
    runSend(
      sessionId,
      [{ from: 'dr', text }],
      () => sessionsApi.envoyerMessageTexte(sessionId, text),
      "Impossible d'envoyer le message."
    ), [runSend]);

  const sendDoctorAttachment = useCallback((sessionId, fichierHea, fichierDat, question, clinique) =>
    runSend(
      sessionId,
      [{ from: 'dr', text: question || "Voici l'ECG à analyser", attachment: { name: fichierHea.name.replace(/\.hea$/i, ''), meta: 'Envoi et analyse en cours…' } }],
      () => sessionsApi.envoyerMessageEcg(sessionId, fichierHea, fichierDat, question, clinique),
      "Impossible d'analyser ce fichier ECG."
    ), [runSend]);

  // OUTIL DE TEST — CSV converti en WFDB côté serveur.
  const sendDoctorCsvAttachment = useCallback((sessionId, fichierCsv, frequenceHz, aEntete, question, clinique) =>
    runSend(
      sessionId,
      [{ from: 'dr', text: question || "Voici l'ECG (CSV) à analyser", attachment: { name: fichierCsv.name, meta: 'Conversion CSV → WFDB et analyse en cours…' } }],
      () => sessionsApi.envoyerMessageEcgCsv(sessionId, fichierCsv, frequenceHz, aEntete, question, clinique),
      "Impossible de convertir/analyser ce CSV."
    ), [runSend]);

  // ---------------- ADMIN ----------------
  const loadDoctors = useCallback(async () => {
    try {
      const doctors = await adminApi.listerMedecins();
      dispatch({ type: 'SET_DOCTORS', doctors });
    } catch (err) {
      errorToast(err, 'Impossible de charger la liste des médecins.');
    }
  }, [errorToast]);

  const loadStatistiques = useCallback(async (mois) => {
    try {
      const stats = await adminApi.obtenirStatistiques(mois);
      dispatch({ type: 'SET_STATS', stats });
    } catch (err) {
      errorToast(err, 'Impossible de charger les statistiques.');
    }
  }, [errorToast]);

  const loadMedecinStatistiques = useCallback(async (mois) => {
    try {
      const stats = await dossiersApi.obtenirStatistiquesMedecin(mois);
      dispatch({ type: 'SET_MEDECIN_STATS', stats });
    } catch (err) {
      errorToast(err, 'Impossible de charger votre activité du mois.');
    }
  }, [errorToast]);

  const submitDoctorForm = useCallback(async (form, estActif) => {
    const payload = {
      nom: form.last,
      prenom: form.first,
      email: form.email,
      mot_de_passe: form.password,
      specialite: form.specialty,
      numero_ordre: form.numeroOrdre,
      est_actif: estActif === 'active',
    };
    try {
      const created = await adminApi.creerMedecin(payload);
      dispatch({ type: 'ADD_DOCTOR', doctor: created });
      toast('Compte médecin créé.', 'success');
      dispatch({ type: 'ADMIN_NAV', view: 'medecins' });
    } catch (err) {
      errorToast(err, 'Impossible de créer ce compte médecin.');
    }
  }, [toast, errorToast]);

  const toggleDoctorStatus = useCallback(async (id, estActif) => {
    try {
      const updated = await adminApi.changerStatutUtilisateur(id, estActif);
      dispatch({ type: 'UPDATE_DOCTOR', doctor: updated });
      toast(estActif ? 'Médecin activé.' : 'Médecin désactivé.', 'success');
    } catch (err) {
      errorToast(err, 'Impossible de changer le statut de ce médecin.');
    }
  }, [toast, errorToast]);

  const actions = {
    toast,
    doLogin,
    logout,
    loadCurrentUser,
    saveProfile,
    changePassword,
    loadDossiers,
    submitPatientForm,
    loadSessions,
    loadSessionMessages,
    startSession,
    renameSession,
    deleteSession,
    deleteDossier,
    sendDoctorText,
    sendDoctorAttachment,
    sendDoctorCsvAttachment,
    loadDoctors,
    loadStatistiques,
    loadMedecinStatistiques,
    submitDoctorForm,
    toggleDoctorStatus,
  };

  return (
    <StateContext.Provider value={state}>
      <DispatchContext.Provider value={dispatch}>
        <ActionsContext.Provider value={actions}>{children}</ActionsContext.Provider>
      </DispatchContext.Provider>
    </StateContext.Provider>
  );
}

export function useAppState() {
  const ctx = useContext(StateContext);
  if (!ctx) throw new Error('useAppState must be used within AppProvider');
  return ctx;
}
export function useAppDispatch() {
  const ctx = useContext(DispatchContext);
  if (!ctx) throw new Error('useAppDispatch must be used within AppProvider');
  return ctx;
}
export function useAppActions() {
  const ctx = useContext(ActionsContext);
  if (!ctx) throw new Error('useAppActions must be used within AppProvider');
  return ctx;
}
