import { apiRequest } from './client';

// creerDossierPatient()
export function creerDossier(payload) {
  return apiRequest('/medecin/dossiers', { method: 'POST', json: payload });
}

export function listerDossiers() {
  return apiRequest('/medecin/dossiers');
}

export function obtenirDossier(id) {
  return apiRequest(`/medecin/dossiers/${id}`);
}

export function modifierDossier(id, payload) {
  return apiRequest(`/medecin/dossiers/${id}`, { method: 'PATCH', json: payload });
}

export function obtenirStatistiquesMedecin(mois) {
  const q = mois ? `?mois=${mois}` : '';
  return apiRequest(`/medecin/statistiques${q}`);
}

export function supprimerDossier(dossierId) {
  return apiRequest(`/medecin/dossiers/${dossierId}`, { method: 'DELETE' });
}
