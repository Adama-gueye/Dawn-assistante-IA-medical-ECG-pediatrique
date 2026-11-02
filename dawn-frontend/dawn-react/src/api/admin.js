import { apiRequest } from './client';

// creerCompteMedecin()
export function creerMedecin(payload) {
  return apiRequest('/admin/medecins', { method: 'POST', json: payload });
}

// gererUtilisateurs()
export function listerUtilisateurs() {
  return apiRequest('/admin/utilisateurs');
}

export function listerMedecins() {
  return apiRequest('/admin/medecins');
}

export function changerStatutUtilisateur(id, estActif) {
  return apiRequest(`/admin/utilisateurs/${id}/statut?est_actif=${estActif}`, { method: 'PATCH' });
}

export function obtenirStatistiques(mois) {
  const q = mois ? `?mois=${mois}` : '';
  return apiRequest(`/admin/statistiques${q}`);
}
