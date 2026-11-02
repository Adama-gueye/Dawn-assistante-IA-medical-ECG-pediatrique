export function initials(first, last) {
  return ((first || ' ')[0] + (last || ' ')[0]).toUpperCase();
}

export function ageFromDob(dob) {
  if (!dob) return '—';
  const d = new Date(dob + 'T00:00:00');
  if (isNaN(d.getTime())) return '—';
  const today = new Date();
  let age = today.getFullYear() - d.getFullYear();
  const m = today.getMonth() - d.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < d.getDate())) age--;
  return age + ' ans';
}

export function sexLabel(sex) {
  return sex === 'F' ? '♀ Féminin' : '♂ Masculin';
}
export function sexShort(sex) {
  return sex === 'F' ? '♀ F' : '♂ M';
}
export function avatarClass(sex) {
  return sex === 'F' ? 'f' : 'm';
}

// Formate une date ISO (ou un objet Date) en libellé court fr-FR, ex: "05 sept."
export function shortDate(value) {
  if (!value) return '—';
  const d = value instanceof Date ? value : new Date(value);
  if (isNaN(d.getTime())) return '—';
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
}

// Formate une date+heure ISO en libellé fr-FR, ex: "05 sept. 14h30"
export function shortDateTime(value) {
  if (!value) return '—';
  const d = value instanceof Date ? value : new Date(value);
  if (isNaN(d.getTime())) return '—';
  const date = d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' });
  const time = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }).replace(':', 'h');
  return `${date} ${time}`;
}

// Sépare une liste d'allergies stockée comme texte libre ("Pénicilline, Latex")
// en tableau pour l'affichage sous forme de puces.
export function allergiesToList(text) {
  if (!text) return [];
  return text.split(',').map((a) => a.trim()).filter(Boolean);
}
