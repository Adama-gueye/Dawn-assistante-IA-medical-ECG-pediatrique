// Transforme un MessageMedecinOut (tel que renvoyé par l'API) en une ou deux
// bulles de chat affichables : la question du médecin, puis la réponse IA.

// La réponse vient d'un modèle de langage : on échappe TOUT le HTML avant d'ajouter
// nos propres balises (gras, retours à la ligne), pour qu'aucune balise émise par le
// modèle ne soit interprétée par le navigateur.
function escapeHtml(texte) {
  return texte
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function formatReponse(texte = '') {
  return escapeHtml(texte)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^- /gm, '• ')
    .replace(/\n/g, '<br>');
}

// Liste de lignes « Titre du document (84 %) » (ou null s'il n'y a aucune source).
function formatSources(sourcesDocument = [], sourcesCas = []) {
  const lignes = [
    ...sourcesDocument.map((s) => `${s.document_titre || 'Document #' + s.document_id} (${Math.round(s.score_relevance * 100)} %)`),
    ...sourcesCas.map((s) => `Cas clinique #${s.cas_id} (${Math.round(s.score_relevance * 100)} %)`),
  ];
  return lignes.length ? lignes : null;
}

function basename(path) {
  if (!path) return '';
  return path.split(/[/\\]/).pop();
}

export function toDisplayEntries(message) {
  const sources = formatSources(message.sources_document, message.sources_cas);

  if (message.type === 'ecg') {
    const metaParts = [];
    if (message.nb_derivations) metaParts.push(`${message.nb_derivations} dérivations`);
    if (message.frequence_hz) metaParts.push(`${message.frequence_hz} Hz`);
    if (message.duree_secondes) metaParts.push(`${message.duree_secondes}s`);
    return [
      {
        from: 'dr',
        text: message.question || "Voici l'ECG à analyser",
        attachment: { name: basename(message.fichier_ecg).replace(/\.hea$/, ''), meta: metaParts.join(' · ') || 'WFDB' },
      },
      {
        from: 'ai',
        card: {
          title: '📊 Analyse ECG',
          bodyHtml: formatReponse(message.reponse || 'Analyse en cours...'),
          sources,
        },
      },
    ];
  }

  // type === 'texte'
  const entries = [{ from: 'dr', text: message.contenu }];
  if (sources) {
    entries.push({ from: 'ai', card: { title: '🤖 Réponse DAWN', bodyHtml: formatReponse(message.reponse || ''), sources } });
  } else {
    entries.push({ from: 'ai', html: formatReponse(message.reponse || '') });
  }
  return entries;
}
