// Client HTTP minimal pour l'API DAWN (FastAPI).
// Centralise l'URL de base, le token JWT (localStorage) et le parsing d'erreurs.

export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const TOKEN_KEY = 'dawn_token';
const ROLE_KEY = 'dawn_role';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setSession(token, role) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ROLE_KEY, role);
}
export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
}
export function getRole() {
  return localStorage.getItem(ROLE_KEY);
}

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function parseError(response) {
  try {
    const data = await response.json();
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail)) return data.detail.map((d) => d.msg).join(', ');
  } catch (_) { /* pas de corps JSON */ }
  return `Erreur ${response.status}`;
}

/**
 * @param {string} path chemin de l'API, ex: "/medecin/dossiers"
 * @param {object} opts { method, json, form, formData, auth }
 */
export async function apiRequest(path, opts = {}) {
  const { method = 'GET', json, form, formData, auth = true } = opts;
  const headers = {};
  let body;

  if (json !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(json);
  } else if (form !== undefined) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded';
    body = new URLSearchParams(form).toString();
  } else if (formData !== undefined) {
    body = formData; // le navigateur fixe le Content-Type multipart lui-même
  }

  if (auth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { method, headers, body });

  if (!response.ok) {
    if (response.status === 401 && auth) {
      clearSession();
    }
    throw new ApiError(await parseError(response), response.status);
  }
  if (response.status === 204) return null;
  return response.json();
}
