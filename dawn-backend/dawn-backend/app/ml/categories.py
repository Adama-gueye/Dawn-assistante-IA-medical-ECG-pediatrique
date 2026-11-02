"""Libellés des 12 catégories AHA du modèle (déduits des codes AHA du jeu de données ZZU : ECGCode.csv)."""

LIBELLES = {
    "A": "ECG normal",
    "C": "Anomalie du rythme sinusal",
    "D": "Extrasystoles / échappements atriaux et jonctionnels",
    "E": "Tachyarythmie supraventriculaire",
    "F": "Extrasystoles ventriculaires",
    "G": "Tachycardie / fibrillation ventriculaire",
    "H": "Trouble de la conduction auriculo-ventriculaire",
    "I": "Trouble de la conduction intraventriculaire",
    "J": "Anomalie de l'axe ou du voltage",
    "K": "Hypertrophie / dilatation des cavités",
    "L": "Anomalie de repolarisation (ST-T, QT)",
    "M": "Signes d'ischémie / d'infarctus",
}


def libelle(code: str) -> str:
    return LIBELLES.get(code, code)
