import { apiRequest, setSession, clearSession } from './client';

// seConnecter() — POST /auth/login attend un form OAuth2 (username/password),
// pas du JSON.
export async function login(email, password) {
  const data = await apiRequest('/auth/login', {
    method: 'POST',
    form: { username: email, password },
    auth: false,
  });
  setSession(data.access_token, data.role);
  return data;
}

export function logout() {
  clearSession();
}

// whoami() — GET /auth/me
export function me() {
  return apiRequest('/auth/me');
}

// Modifie nom / prénom (et spécialité pour un médecin) — PATCH /auth/me
export function modifierProfil(payload) {
  return apiRequest('/auth/me', { method: 'PATCH', json: payload });
}

// POST /auth/changer-mot-de-passe (400 si l'ancien mot de passe est incorrect)
export function changerMotDePasse(ancien, nouveau) {
  return apiRequest('/auth/changer-mot-de-passe', {
    method: 'POST',
    json: { ancien_mot_de_passe: ancien, nouveau_mot_de_passe: nouveau },
  });
}
