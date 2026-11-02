"""
Service ECG — analyse d'un enregistrement WFDB par le modèle DAWN-ECG (ensemble de 6 HuBERT-ECG fine-tunés,
12 catégories AHA en multi-label) puis mise en forme du résultat pour le médecin.

Chaîne : WFDB -> prétraitement identique au notebook -> ensemble de modèles -> calibration de Platt -> seuils
-> prédiction conforme (certain / à confirmer / indéterminé) -> texte français + résultat structuré (JSON).

Tant que le fichier de modèle n'est pas installé (models/dawn_ecg_model_final.pt + models/hubert-ecg-small/),
le service renvoie la réponse simulée d'origine, clairement signalée comme telle.
"""
import json
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from app.config import settings
from app.ml import preprocessing as P
from app.ml.calibration import Calibration
from app.ml.categories import libelle
from app.services import model_fetch

RACINE = Path(__file__).resolve().parents[2]  # racine du backend (dawn-backend/)

# Une catégorie détectée est signalée « fiabilité limitée » si sa précision mesurée sur le jeu de test est inférieure à ce seuil,
# et « évaluation peu fiable » si elle compte moins de SUPPORT_RARE cas positifs dans ce jeu de test.
SEUIL_PRECISION_FAIBLE = 0.40
SUPPORT_RARE = 30
# Au-delà de ce taux, la prédiction conforme est « ambiguë » quasi tout le temps pour la catégorie : inutile de la lister comme indéterminée.
SEUIL_AMBIGU_INUTILE = 80.0


class ModeleIndisponible(RuntimeError):
    """Le modèle est installé mais n'a pas pu être chargé (le message dit pourquoi)."""


class EntreeInvalide(ValueError):
    """Données d'entrée inutilisables par le modèle (âge/sexe manquants, âge hors du domaine d'entraînement...)."""


@dataclass
class EcgAnalysisResult:
    reponse: str
    classe_predite: str
    confiance: float
    incertitude: str
    details: Optional[dict] = None  # résultat structuré, stocké en JSON dans MessageECG.resultat_json


_verrou_chargement = threading.RLock()
_verrou_inference = threading.Lock()
_ensemble = None
_calibration: Optional[Calibration] = None


def _chemin(valeur: str) -> Path:
    p = Path(valeur)
    return p if p.is_absolute() else RACINE / p


def modele_installe() -> bool:
    return _chemin(settings.ECG_MODEL_PATH).is_file() and (_chemin(settings.ECG_HUBERT_DIR) / "config.json").is_file()


def _charger():
    global _ensemble, _calibration
    with _verrou_chargement:
        if _ensemble is None:
            try:
                from app.ml.hubert_ensemble import HuBERTEnsemble  # import tardif : torch + transformers
                calibration = Calibration.charger(model_fetch.chemin_calibration())  # dépôt Hugging Face, sinon copie locale
                _ensemble = HuBERTEnsemble(
                    _chemin(settings.ECG_MODEL_PATH), _chemin(settings.ECG_HUBERT_DIR), calibration,
                    selection=settings.ECG_MODELES, weights_only=settings.ECG_TORCH_WEIGHTS_ONLY,
                    n_threads=settings.ECG_THREADS or max(1, (os.cpu_count() or 2) - 1),  # laisse un coeur libre : l'API reste fluide pendant l'analyse
                    device=settings.ECG_DEVICE,
                )
                _calibration = calibration
            except (ValueError, RuntimeError, OSError, ImportError) as e:
                raise ModeleIndisponible(f"Le modèle ECG n'a pas pu être chargé : {e}") from e
        return _ensemble, _calibration


def _resultat_simule() -> EcgAnalysisResult:
    return EcgAnalysisResult(
        reponse=(
            "[Analyse simulée — modèle DAWN-ECG non installé] Placez models/dawn_ecg_model_final.pt et "
            "models/hubert-ecg-small/ (voir le README) pour obtenir une vraie analyse."
        ),
        classe_predite="Normal", confiance=0.0, incertitude="inconnue",
    )


def _pct(p: float) -> str:
    return f"{round(100 * p)} %"


def _avertissements(age_annees: float, infos: dict, ensemble) -> List[str]:
    a = []
    if age_annees > 15:
        a.append(f"Patient de {age_annees:.0f} ans : au-delà de la tranche d'âge d'entraînement (0–15 ans), à interpréter avec une extrême prudence.")
    if age_annees < 1:
        a.append("Nourrisson de moins d'un an : le modèle est nettement moins performant dans cette tranche d'âge lors de l'évaluation.")
    if infos["nb_derivations"] < 12:
        a.append(f"ECG à {infos['nb_derivations']} dérivations : performances plus faibles qu'à 12 dérivations lors de l'évaluation.")
    if infos["reechantillonne"]:
        a.append(f"Signal rééchantillonné de {infos['frequence_hz']:g} Hz à 500 Hz (le modèle a été entraîné à 500 Hz).")
    if infos["duree_s"] < P.WINDOW_SEC:
        a.append(f"Enregistrement de {infos['duree_s']:g} s (< {P.WINDOW_SEC} s) : complété par des zéros.")
    if not ensemble.ensemble_complet:
        a.append(f"Sous-ensemble de {len(ensemble.modeles)} modèle(s) sur {ensemble.n_modeles_total} : la calibration est établie pour l'ensemble complet.")
    return a


def formater_reponse(lignes: List[dict], cal: Calibration, incertitude: str, avertissements: List[str]) -> str:
    detectees = sorted((l for l in lignes if l["detecte"]), key=lambda l: -l["p_calibree"])
    sortie = ["**Analyse automatique DAWN-ECG** — aide à la décision, à confirmer par le médecin.", ""]

    if detectees:
        sortie.append("**Catégories détectées**")
        for l in detectees:
            # « nette » = la prédiction conforme (90 %) ne laisse qu'une étiquette ; ce n'est PAS une garantie de justesse pour cet ECG
            statut = "détection nette" if l["conforme"] == "present" else "détection à confirmer"
            sortie.append(f"- **{l['code']} — {libelle(l['code'])}** : {_pct(l['p_calibree'])} ({statut})")
        for l in detectees:
            m = cal.metriques[l["code"]]
            if m["support_test"] < SUPPORT_RARE:
                sortie.append(f"- ⚠ {l['code']} : catégorie très rare dans les données ({m['support_test']} cas en test) — évaluation peu fiable, précision mesurée {_pct(m['precision'])}.")
            elif m["precision"] < SEUIL_PRECISION_FAIBLE:
                sortie.append(f"- ⚠ {l['code']} : fiabilité limitée — sur le jeu de test, {_pct(m['precision'])} des détections étaient justes.")
    else:
        sortie.append("**Aucune catégorie n'atteint son seuil de détection.** Cela ne prouve pas que l'ECG est normal.")

    indetermines = [l["code"] for l in lignes
                    if not l["detecte"] and l["conforme"] == "indetermine" and cal.metriques[l["code"]]["pct_ambigu_conforme"] < SEUIL_AMBIGU_INUTILE]
    if indetermines:
        sortie += ["", f"**Indéterminé** (le modèle ne peut pas trancher) : {', '.join(indetermines)}"]

    sortie += ["", f"**Incertitude globale** : {incertitude}"]
    if avertissements:
        sortie += ["", "**Points d'attention**"] + [f"- {a}" for a in avertissements]
    sortie += ["", "Les catégories très rares (ischémie/infarctus M, arythmies ventriculaires graves G) ne sont pas fiables : l'absence de détection ne les exclut pas."]
    return "\n".join(sortie)


def analyser_ecg(
    chemin_base_sans_extension: str,
    question: Optional[str] = None,
    age_jours: Optional[int] = None,
    sexe: Optional[str] = None,
    nb_derivations: Optional[int] = None,
    age_annees: Optional[float] = None,
) -> EcgAnalysisResult:
    """
    `chemin_base_sans_extension` : record WFDB sans extension (.hea et .dat à côté).
    `age_annees` ou `age_jours`, et `sexe` (« M »/« F ») sont OBLIGATOIRES dès que le modèle est installé : ils font partie
    des entrées du modèle (le notebook substituerait silencieusement l'âge médian et « féminin » — on refuse plutôt).
    Lève EntreeInvalide (-> 422) ou ModeleIndisponible (-> 503).
    """
    if not modele_installe():
        if not settings.ECG_AUTO_DOWNLOAD:
            return _resultat_simule()
        model_fetch.demarrer_telechargement()  # no-op s'il est déjà en cours
        st = model_fetch.statut()
        if st["statut"] == "erreur":
            raise ModeleIndisponible(st["message"])
        raise ModeleIndisponible("Le modèle ECG est en cours de téléchargement depuis Hugging Face (~730 Mo) : réessaie dans quelques minutes.")

    if age_annees is None and age_jours is not None:
        age_annees = P.age_annees_depuis_jours(age_jours)
    if age_annees is None or not sexe or str(sexe).strip().upper()[:1] not in ("M", "F"):
        raise EntreeInvalide("L'âge et le sexe (M ou F) du patient sont obligatoires pour l'analyse ECG.")
    if age_annees < 0:
        raise EntreeInvalide("Âge négatif impossible.")
    if age_annees > settings.ECG_AGE_MAX_ANS:
        raise EntreeInvalide(
            f"Patient de {age_annees:.0f} ans : le modèle a été entraîné sur des enfants de 0 à 15 ans, "
            f"analyse refusée au-delà de {settings.ECG_AGE_MAX_ANS:g} ans."
        )

    ensemble, cal = _charger()
    debut = time.perf_counter()
    fenetres, clinique, infos = P.preparer_ecg(chemin_base_sans_extension, age_annees, sexe)
    with _verrou_inference:
        p_brute = ensemble.predire(fenetres, clinique)
    duree = time.perf_counter() - debut

    lignes = cal.analyser(p_brute)
    p_cal = [l["p_calibree"] for l in lignes]
    incertitude = cal.niveau_incertitude(p_cal)
    avertissements = _avertissements(age_annees, infos, ensemble)
    detectees = sorted((l for l in lignes if l["detecte"]), key=lambda l: -l["p_calibree"])

    details = {
        "version_calibration": cal.version,
        "source_calibration": model_fetch.source_calibration(),
        "modeles": ensemble.etiquettes,
        "age_annees": round(float(age_annees), 3),
        "sexe": str(sexe).strip().upper()[:1],
        "lecture": infos,
        "duree_calcul_s": round(duree, 2),
        "incertitude": incertitude,
        "avertissements": avertissements,
        "categories": [{**l, "libelle": libelle(l["code"])} for l in lignes],
    }
    return EcgAnalysisResult(
        reponse=formater_reponse(lignes, cal, incertitude, avertissements),
        classe_predite=(f"{detectees[0]['code']} — {libelle(detectees[0]['code'])}" if detectees else "Aucune catégorie détectée"),
        confiance=float(detectees[0]["p_calibree"]) if detectees else 0.0,
        incertitude=incertitude,
        details=details,
    )


def serialiser_details(resultat: EcgAnalysisResult) -> Optional[str]:
    return json.dumps(resultat.details, ensure_ascii=False) if resultat.details else None


def prechauffer():
    """Charge l'ensemble en mémoire (lecture du .pt + construction des 6 modèles) sans attendre la première analyse."""
    if modele_installe():
        _charger()
