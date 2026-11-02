---
titre: Autres anomalies ECG fréquentes non-arythmiques en pédiatrie (catégories AHA J, K, L)
type_doc: Référence clinique — ECG non-arythmique
usage_dawn: Documentation de complétude — ces catégories ne sont pas des classes du modèle de classification d'arythmies, mais figurent parmi les diagnostics les plus fréquents du dataset ZZU pECG et seront couramment évoquées par les médecins interrogeant le RAG
---

# Autres anomalies ECG fréquentes non-arythmiques

**Pourquoi ce document existe** : les catégories J (axe/voltage/alternance), K (hypertrophie des cavités) et L (repolarisation, ST-T, QT, onde U) ne sont **pas des arythmies** — le modèle de classification de DAWN ne les prédit pas comme telles. Mais L est à elle seule la catégorie la plus fréquente de tout le dataset (plus fréquente encore que les troubles du rythme sinusal), et K/J restent très présentes. Un médecin qui voit ces mentions sur un tracé réel doit pouvoir interroger le RAG à leur sujet — ce document sert cette complétude, sans prétendre remplacer les 5 documents d'arythmies qui restent le cœur du système.

## Catégorie J — Axe, voltage, alternance électrique

Regroupe des anomalies de l'amplitude ou de l'orientation électrique globale du cœur, sans trouble du rythme associé : déviation axiale (droite ou gauche), anomalies de voltage global, alternance électrique (variation battement à battement de l'amplitude du QRS, évocatrice d'un épanchement péricardique volumineux dans les formes marquées).

**Point pédiatrique clé** : l'axe QRS normal évolue fortement avec l'âge — un axe très droit est physiologique chez le nouveau-né (dominance ventriculaire droite) et deviendrait suspect de la même façon chez un adolescent. Toute mention d'un axe "anormal" doit être immédiatement recontextualisée par l'âge du patient (voir document 1).

## Catégorie K — Hypertrophie des cavités

**Définition ECG** : critères de voltage (amplitude anormalement élevée des ondes R ou S dans certaines dérivations) suggérant un épaississement ou une dilatation d'une cavité cardiaque — hypertrophie ventriculaire droite, gauche, ou hypertrophie/dilatation atriale.

**Signification clinique** : les critères de voltage corrèlent mieux avec la taille réelle des cavités chez l'enfant que chez l'adulte, mais leur valeur prédictive reste limitée (de l'ordre de 70% au mieux dans la littérature) — un signe ECG d'hypertrophie doit toujours être corrélé à la clinique et, idéalement, à une échocardiographie, jamais interprété seul comme un diagnostic. Chez le nouveau-né, une onde T positive en V1 peut évoquer une hypertrophie ventriculaire droite alors que c'est physiologique à cet âge précis — encore un exemple où l'âge change l'interprétation.

## Catégorie L — Repolarisation (ST-T, QT, onde U)

**Sous-catégories principales** :
- **Anomalies de l'onde T** : chez le nourrisson et le jeune enfant, une onde T **inversée** en V1-V3 (parfois jusqu'en V4) est **normale** et persiste souvent jusqu'à l'adolescence — l'inverse (onde T positive dans ces dérivations chez le tout-petit) est ce qui doit attirer l'attention (hypertrophie ventriculaire droite). Après la première semaine de vie, une onde T inversée dans les dérivations inférieures (II, III, aVF) ou latérales (I, V5, V6) est en revanche toujours anormale.
- **Sus/sous-décalage du segment ST** : pathologique quand associé à des anomalies de l'onde T, évocateur de péricardite, ischémie/infarctus (rare en pédiatrie, voir document 7), hypertrophie ventriculaire sévère avec surcharge ("strain pattern"), ou effet digitalique.
- **QT/QTc prolongé, onde U proéminente** : voir le traitement détaillé du QTc dans le document 1 — à ne jamais interpréter sur un seuil rigide isolé. Repère utile : QTc normal < 450 ms avant 6 mois, < 440 ms après 6 mois (à nuancer selon la méthode de correction et le contexte, cf. document 1).

## Utilisation par DAWN

Pour ces trois catégories, le RAG doit **explicitement rappeler qu'il ne s'agit pas d'un trouble du rythme** si la question du médecin semble confondre les deux, et systématiquement renvoyer à la nécessité de recontextualiser par l'âge (renvoi au document 1). Contrairement aux documents d'arythmies, l'enjeu ici n'est pas la gravité immédiate mais la **fréquence des faux positifs d'interprétation** liés à la méconnaissance des variantes normales pédiatriques.

## Sources indicatives

- Pediatric ECGs: A Primary Care Primer, Contemporary Pediatrics / Consultant360.
- Clinical Practice Guidelines: Basic paediatric ECG interpretation, Royal Children's Hospital Melbourne.
- Pediatric ECGs and Rhythm Disturbances, Clinician.com.
- Electrocardiographic Manifestations: Pediatric ECG, ScienceDirect.

*(Document académique compilé à partir de la littérature ouverte pour les besoins du prototype DAWN — à faire valider par un cardiologue pédiatre avant tout usage clinique réel.)*
