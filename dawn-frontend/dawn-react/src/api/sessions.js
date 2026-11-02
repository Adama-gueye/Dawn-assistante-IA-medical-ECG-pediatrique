import { apiRequest } from './client';

export function creerSession(payload) {
  return apiRequest('/medecin/sessions', { method: 'POST', json: payload });
}

export function listerSessions(dossierPatientId) {
  const q = dossierPatientId != null ? `?dossier_patient_id=${dossierPatientId}` : '';
  return apiRequest(`/medecin/sessions${q}`);
}

export function listerMessages(sessionId) {
  return apiRequest(`/medecin/sessions/${sessionId}/messages`);
}

export function envoyerMessageTexte(sessionId, contenu) {
  return apiRequest(`/medecin/sessions/${sessionId}/messages/texte`, {
    method: 'POST',
    json: { contenu },
  });
}

// fichierHea / fichierDat : paire WFDB (.hea + .dat), meme enregistrement.
// clinique = { ageAnnees, sexe } : obligatoire pour une session SANS dossier patient (sinon le serveur utilise le dossier).
export function envoyerMessageEcg(sessionId, fichierHea, fichierDat, question, clinique) {
  const formData = new FormData();
  formData.append('fichier_hea', fichierHea);
  formData.append('fichier_dat', fichierDat);
  if (question) formData.append('question', question);
  if (clinique) { formData.append('age_annees', String(clinique.ageAnnees)); formData.append('sexe', clinique.sexe); }
  return apiRequest(`/medecin/sessions/${sessionId}/messages/ecg`, {
    method: 'POST',
    formData,
  });
}

// OUTIL DE TEST — convertit un CSV en WFDB côté serveur puis lance la même
// analyse (utile avant d'avoir de vrais fichiers WFDB ou le modèle final).
export function envoyerMessageEcgCsv(sessionId, fichierCsv, frequenceHz, aEntete, question, clinique) {
  const formData = new FormData();
  formData.append('fichier', fichierCsv);
  formData.append('frequence_hz', String(frequenceHz));
  formData.append('a_entete', String(aEntete));
  if (question) formData.append('question', question);
  if (clinique) { formData.append('age_annees', String(clinique.ageAnnees)); formData.append('sexe', clinique.sexe); }
  return apiRequest(`/medecin/sessions/${sessionId}/messages/ecg-csv`, {
    method: 'POST',
    formData,
  });
}

export function renommerSession(sessionId, titre) {
  return apiRequest(`/medecin/sessions/${sessionId}`, { method: 'PATCH', json: { titre } });
}

export function supprimerSession(sessionId) {
  return apiRequest(`/medecin/sessions/${sessionId}`, { method: 'DELETE' });
}
