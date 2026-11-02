---
titre: Signes ECG d'ischémie/infarctus en pédiatrie — rare mais grave (catégorie AHA M)
type_doc: Référence clinique — ECG non-arythmique
usage_dawn: Documentation de complétude pour la catégorie M, la plus rare du dataset ZZU pECG (46 occurrences) mais cliniquement critique en cas de survenue
---

# Signes ECG d'ischémie/infarctus en pédiatrie

**Pourquoi ce document existe** : la catégorie M (ondes Q pathologiques, signes évocateurs d'ischémie ou d'infarctus du myocarde) est la plus rare de tout le dataset ZZU pECG. Mais rareté ne veut pas dire absence de gravité — c'est justement le type de constat qu'un système d'aide à la décision ne doit pas laisser sans réponse documentée, même pour de très petits effectifs d'entraînement.

## Définition ECG

Ondes Q pathologiques (larges et/ou profondes, dans un territoire correspondant à une paroi myocardique donnée), parfois associées à des anomalies du segment ST et de l'onde T (voir document 6, catégorie L) évocatrices d'ischémie ou de nécrose myocardique.

## Signification clinique — une différence majeure avec l'adulte

Chez l'adulte, un infarctus du myocarde est presque toujours d'origine athéromateuse (occlusion coronaire par une plaque). **Chez l'enfant, cette cause est exceptionnelle** — les causes d'ischémie/infarctus pédiatrique sont d'une nature complètement différente et doivent orienter la réflexion clinique vers :

- **Anomalie congénitale des artères coronaires** (par exemple naissance anormale d'une coronaire depuis l'artère pulmonaire) — cause classique d'ischémie myocardique du nourrisson.
- **Maladie de Kawasaki** avec atteinte coronaire (anévrysmes coronaires) — c'est la cause acquise la plus caractéristique en pédiatrie ; le lien avec la maladie de Kawasaki déjà présente dans `DiseaseCode.csv` de votre dataset est directement pertinent ici.
- **Myocardite** sévère, pouvant s'accompagner de troubles de la repolarisation voire de véritables images de nécrose dans les formes graves.
- **Origine post-chirurgicale**, après certaines interventions de cardiopathie congénitale complexe impliquant une réimplantation coronaire.

## Point de vigilance pour DAWN

Une prédiction dans cette catégorie, même avec un score de confiance modeste (effectif d'entraînement très limité, 46 cas), doit être traitée comme un signal à ne jamais ignorer ni relativiser automatiquement — la rareté statistique de la classe dans les données d'entraînement ne doit pas se traduire par une minimisation clinique dans la réponse du RAG. C'est un cas où l'estimation d'incertitude (MC Dropout) est particulièrement utile pour signaler explicitement au médecin que la prédiction repose sur peu d'exemples, sans pour autant sous-entendre que le signal ECG lui-même est moins préoccupant.

## Utilisation par DAWN

Le RAG doit systématiquement associer toute mention de cette catégorie à une invitation claire à une évaluation cardiologique pédiatrique en lien avec le contexte clinique (antécédent de Kawasaki, chirurgie cardiaque, signes de myocardite) plutôt que de se limiter à décrire le signe ECG isolément.

## Sources indicatives

- DiseaseCode.csv (dataset ZZU pECG) — lien direct avec Kawasaki disease et Congenital heart disease.
- Electrocardiographic Manifestations: Pediatric ECG, ScienceDirect.
- Littérature générale sur les causes pédiatriques d'ischémie myocardique (anomalies coronaires congénitales, Kawasaki).

*(Document académique compilé à partir de la littérature ouverte pour les besoins du prototype DAWN — à faire valider par un cardiologue pédiatre avant tout usage clinique réel. Catégorie à effectif très limité dans les données d'entraînement — la prudence clinique doit primer sur la confiance statistique du modèle.)*
