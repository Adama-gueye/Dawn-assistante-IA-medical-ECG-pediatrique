---
titre: Repères ECG normaux en pédiatrie, par tranche d'âge
type_doc: Référence clinique — physiologie et normes
usage_dawn: Document fondation du RAG ECG — sert de base de comparaison pour toute interprétation d'un tracé
---

# Repères ECG normaux en pédiatrie, par tranche d'âge

## Pourquoi l'âge change tout en ECG pédiatrique

Contrairement à l'adulte, il n'existe pas de valeur "normale" unique en ECG pédiatrique : la fréquence cardiaque et les intervalles évoluent fortement de la naissance à l'adolescence, en lien avec la maturation du système de conduction et le remodelage progressif des cavités cardiaques. Un rythme à 130 bpm est une tachycardie franche chez un adolescent, mais parfaitement physiologique chez un nourrisson de 3 mois. Toute interprétation automatisée d'un tracé (par DAWN ou par un cardiologue) doit donc systématiquement replacer les valeurs mesurées dans le contexte de l'âge exact du patient, et idéalement de son sexe.

Deux phénomènes de fond expliquent cette évolution, liés à la croissance cardiaque et à la maturation électrophysiologique progressive de l'enfant :
- **Dominance ventriculaire droite à la naissance**, qui s'inverse progressivement vers une dominance gauche typique de l'adulte, généralement acquise vers 3-4 ans.
- **Maturation du tissu de conduction et croissance des cavités cardiaques**, qui accompagne l'allongement progressif des intervalles PR et QRS observé avec l'âge.

## Table de référence indicative

| Tranche d'âge | Fréquence cardiaque (bpm) | Intervalle PR (ms) | Durée QRS (ms) | QTc (ms) |
|---|---|---|---|---|
| Nouveau-né (0-1 mois) | 95-160 | 80-120 | 45-85 | jusqu'à ~450 |
| Nourrisson (1-12 mois) | 90-150 | 80-135 | 45-90 | jusqu'à ~450 |
| 1-3 ans | 80-130 | 90-140 | 50-90 | jusqu'à ~450 |
| 3-6 ans | 70-120 | 90-150 | 50-90 | jusqu'à ~450 |
| 6-8 ans | 65-115 | 100-160 | 50-100 | jusqu'à ~450 |
| 8-12 ans | 55-110 | 100-170 | 55-105 | jusqu'à ~450 |
| 12-16 ans | 50-105 | 110-180 | 60-115 | jusqu'à ~460 |
| > 16 ans (proche adulte) | 50-100 | 120-200 | 70-120 | ~440-460 (♂ un peu < ♀) |

*Valeurs indicatives compilées à partir de plusieurs séries pédiatriques publiées (bornes 1er-99e percentile approximatives). Les seuils exacts varient légèrement selon les études et les méthodes de mesure ; en usage clinique réel, ces repères doivent être confrontés à une référence pédiatrique validée (ex. les normes par z-score de Rijnbeek et al.) plutôt qu'utilisés comme seuils rigides.*

## Points de vigilance particuliers

- **QTc** : l'interprétation d'un QTc ne doit jamais reposer sur un seuil universel unique. Elle dépend de l'âge, de la méthode de correction utilisée (Bazett, Fridericia...), de la population de référence et du contexte clinique (fièvre, électrolytes, médicaments). Un allongement franc au-delà des repères par âge doit faire évoquer un syndrome du QT long, une cause médicamenteuse ou un trouble électrolytique — c'est un facteur de risque de torsades de pointes, pas une arythmie en soi. DAWN doit comparer une valeur mesurée à une référence adaptée à l'âge plutôt qu'à un seuil fixe.
- **PR court** associé à un empâtement du QRS (onde delta) évoque une préexcitation (syndrome de Wolff-Parkinson-White), à ne pas confondre avec un simple PR court isolé.
- **QRS large** pour l'âge oriente vers un bloc de branche ou une origine ventriculaire du rythme plutôt que supraventriculaire.
- La période néonatale est la phase de changement la plus rapide de tous les paramètres ECG : les 35 premiers jours de vie concentrent déjà une variabilité importante, justifiant une prudence particulière dans l'interprétation automatisée chez le tout jeune nourrisson.

## Utilisation par DAWN

Ce document sert de **référence de contexte** au module RAG lorsqu'un médecin interroge l'assistant sur un tracé donné : avant de qualifier une fréquence ou un intervalle mesuré d'anormal, le système doit recouper la valeur avec la tranche d'âge du patient (déjà disponible dans `DossierPatient`/`AttributesDictionary`) en s'appuyant sur cette table plutôt que sur des seuils fixes universels.

## Sources indicatives

**Références normatives principales (Z-scores, larges populations pédiatriques) :**
- Rijnbeek et al., *Electrocardiogram Standards for Children and Young Adults Using Z-Scores*, Circulation: Arrhythmia and Electrophysiology.
- *Normal ECG standards and percentile charts for infants, children and adolescents*, Pediatrics & Neonatology / ScienceDirect.

**Sources complémentaires (synthèse pédagogique) :**
- LITFL — *Normal Paediatric ECG*, ECG Library.
- O'Connor M., McDaniel N., Brady W.J., *The pediatric electrocardiogram. Part I: Age-related interpretation*, Am J Emerg Med.

*(Document académique compilé à partir de la littérature ouverte pour les besoins du prototype DAWN — à faire valider par un cardiologue pédiatre avant tout usage clinique réel.)*
