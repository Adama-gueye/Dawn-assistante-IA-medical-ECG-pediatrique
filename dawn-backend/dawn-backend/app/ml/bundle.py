"""
Validation du fichier de modèle (dawn_ecg_model_final.pt) et sélection des modèles de l'ensemble.
Python pur : aucune dépendance à torch, pour pouvoir être testé sans lui.
"""
from typing import Dict, List

from app.ml import preprocessing as P

PRETRAITEMENT_ATTENDU = {
    "sample_rate": P.SAMPLE_RATE,
    "window_sec": P.WINDOW_SEC,
    "n_eval_windows": P.N_EVAL_WIN,
    "norm_mode": "record",
    "baseline_removal_1s_moving_average": True,
    "clip": 10.0,
    "age_scale_years": P.AGE_SCALE,
}


def etiquette(modele: dict) -> str:
    return f"{modele['loss']}:{modele['seed']}"


def verifier_bundle(bundle: dict, categories: List[str], seuils_bruts: Dict[str, float]) -> None:
    """Lève ValueError (message en français) si le .pt n'est pas celui que le prétraitement et la calibration attendent."""
    for cle in ("models", "thresholds", "categories", "architecture", "preprocessing"):
        if cle not in bundle:
            raise ValueError(f"Fichier de modèle invalide : clé « {cle} » absente (attendu : le .pt produit par la cellule de sauvegarde finale du notebook).")
    if bundle["architecture"] != "hubert":
        raise ValueError(f"Architecture « {bundle['architecture']} » non prise en charge (seule « hubert » est implémentée).")
    if list(bundle["categories"]) != list(categories):
        raise ValueError(f"Catégories du modèle {list(bundle['categories'])} différentes de celles de la calibration {list(categories)}.")
    if int(bundle.get("n_leads", 12)) != P.N_LEADS:
        raise ValueError(f"Le modèle attend {bundle.get('n_leads')} dérivations, le prétraitement en produit {P.N_LEADS}.")
    pre = bundle["preprocessing"]
    for cle, attendu in PRETRAITEMENT_ATTENDU.items():
        if cle in pre and pre[cle] != attendu:
            raise ValueError(f"Prétraitement incompatible : le modèle a été entraîné avec {cle}={pre[cle]!r}, ce code applique {attendu!r}.")
    ecarts = [c for c in categories if abs(float(bundle["thresholds"][c]) - float(seuils_bruts[c])) > 1e-9]
    if ecarts:
        raise ValueError(
            "Les artefacts de calibration ne correspondent pas à ce fichier de modèle (seuils différents pour : "
            f"{', '.join(ecarts)}). Régénère-les avec scripts/reproduire_calibration.py à partir des résultats du même entraînement."
        )
    if not bundle["models"]:
        raise ValueError("Le fichier de modèle ne contient aucun modèle.")


def choisir_modeles(modeles: List[dict], spec: str) -> List[dict]:
    """
    spec : « all » (ou vide) = tous ; un entier N = les N premiers ; « ASL:42,CB:1337 » = ces modèles précis.
    NB : la calibration fournie est établie pour l'ensemble complet des modèles du .pt ; un sous-ensemble donne
    des probabilités légèrement moins bien calibrées (le service le signale).
    """
    spec = (spec or "all").strip()
    if spec.lower() in ("all", "tous", "0"):
        return list(modeles)
    if spec.isdigit():
        n = int(spec)
        if n > len(modeles):
            raise ValueError(f"{n} modèles demandés mais le .pt n'en contient que {len(modeles)}.")
        return list(modeles[:n])
    voulus = [t.strip() for t in spec.split(",") if t.strip()]
    par_tag = {etiquette(m): m for m in modeles}
    inconnus = [t for t in voulus if t not in par_tag]
    if inconnus:
        raise ValueError(f"Modèle(s) inconnu(s) : {inconnus}. Disponibles : {list(par_tag)}.")
    return [par_tag[t] for t in voulus]
