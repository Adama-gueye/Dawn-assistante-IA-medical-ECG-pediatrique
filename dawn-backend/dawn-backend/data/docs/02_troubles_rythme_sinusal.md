---
titre: Troubles du rythme sinusal en pédiatrie (catégorie AHA C)
type_doc: Référence clinique — arythmies
usage_dawn: Documentation associée à la classe AHA "C" du modèle de classification ECG de DAWN (catégorie la plus fréquente du dataset ZZU pECG)
---

# Troubles du rythme sinusal en pédiatrie

Regroupe les anomalies où le nœud sinusal reste le générateur du rythme, mais à une fréquence ou une régularité anormale pour l'âge : tachycardie sinusale, bradycardie sinusale, arythmie sinusale, bloc sino-atrial et pause sinusale.

## Tachycardie sinusale

**Définition ECG** : rythme sinusal normal (onde P de morphologie normale précédant chaque QRS) mais à une fréquence supérieure à la norme pour l'âge (voir document des repères normaux). Chez le nourrisson fébrile, la fréquence peut atteindre 220-240 bpm sans que cela soit pathologique en soi.

**Signification clinique** : c'est l'arythmie la plus fréquemment rapportée chez l'enfant. Dans l'immense majorité des cas, elle est **secondaire** à une cause extracardiaque (fièvre, douleur, anxiété, déshydratation, anémie, hyperthyroïdie) plutôt qu'un trouble primitif du cœur. Le repère clinique clé : une tachycardie sinusale garde une variabilité battement à battement (elle s'accélère et ralentit progressivement avec l'activité/le repos), contrairement à une tachycardie supraventriculaire qui débute et se termine brutalement.

**Point de vigilance pour DAWN** : une fréquence élevée chez un enfant "par ailleurs calme ou endormi" doit faire suspecter une tachycardie supraventriculaire plutôt qu'une simple tachycardie sinusale, même en présence d'une onde P.

## Bradycardie sinusale

**Définition ECG** : rythme sinusal à une fréquence inférieure à la norme pour l'âge.

**Signification clinique** : très souvent physiologique — fréquente pendant le sommeil chez l'enfant sain, et chez les enfants sportifs entraînés (tonus vagal élevé). Une bradycardie sinusale isolée chez un enfant par ailleurs en bonne santé n'est généralement pas préoccupante, à condition que la fréquence remonte de façon appropriée à l'effort ou à la fièvre. Des causes pathologiques existent (hypertension intracrânienne, hypothyroïdie, hypothermie, hypokaliémie, dysfonction du nœud sinusal après chirurgie cardiaque) mais restent minoritaires.

## Arythmie sinusale

**Définition ECG** : variation cyclique de la fréquence cardiaque, le plus souvent synchronisée avec la respiration (accélération à l'inspiration, ralentissement à l'expiration). Onde P et morphologie du complexe normales.

**Signification clinique** : trouvée systématiquement chez l'enfant sain, ambulatoire ou hospitalisé, dans les études de monitoring continu — c'est une **variante normale**, pas une arythmie pathologique, et ne doit jamais être signalée comme une anomalie inquiétante.

## Bloc sino-atrial et pause sinusale

**Définition ECG** : absence intermittente d'une ou plusieurs ondes P attendues (le nœud sinusal "manque" un battement), créant une pause dans le rythme.

**Signification clinique** : peut relever d'une dysfonction sinusale (souvent liée à une lésion directe du nœud sinusal après chirurgie cardiaque chez l'enfant) ou d'un tonus vagal élevé sans caractère pathologique. Une association fréquente à surveiller : le "syndrome brady-tachy", où des pauses sinusales alternent avec des épisodes de tachycardie atriale de réentrée.

## Utilisation par DAWN

Cette catégorie regroupe la majorité des enregistrements classés comme anormaux dans le dataset ZZU pECG. Le RAG doit systématiquement rappeler que **la plupart de ces troubles sinusaux sont bénins et fréquents chez l'enfant sain** — le rôle de DAWN est d'attirer l'attention du médecin sur le trouble détecté et son contexte normatif par âge, pas de le présenter comme une urgence par défaut.

## Sources indicatives

- Emergency diagnosis and management of pediatric arrhythmias, PMC.
- Pediatric arrhythmias — sinus node dysfunction, ScienceDirect.
- Sinus Arrhythmia — ScienceDirect Topics.
- Neonatal and Pediatric Guidelines for Arrhythmia Management, PCICS.

*(Document académique compilé à partir de la littérature ouverte pour les besoins du prototype DAWN — à faire valider par un cardiologue pédiatre avant tout usage clinique réel.)*
