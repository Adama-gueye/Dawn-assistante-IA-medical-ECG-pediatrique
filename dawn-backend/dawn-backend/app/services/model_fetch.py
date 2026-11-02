"""
Récupération automatique du modèle DAWN-ECG depuis le dépôt Hugging Face PRIVÉ (plus de script manuel).

  - poids (~730 Mo)      : dépôt privé ECG_HF_REPO, fichier ECG_HF_FILENAME  -> ECG_MODEL_PATH   (jeton HF_TOKEN requis)
  - calibration + seuils : même dépôt privé, fichier ECG_HF_CALIBRATION_FILENAME -> ECG_CALIBRATION_PATH (quelques Ko)
  - code/config HuBERT   : dépôt public Edoardo-Coppola/hubert-ecg-small      -> ECG_HUBERT_DIR   (sans poids)

Le téléchargement se fait UNE fois (les fichiers sont ensuite réutilisés), en arrière-plan au démarrage de l'API
(si ECG_AUTO_DOWNLOAD=true) ou à la première analyse ECG. Une requête n'attend jamais 730 Mo : tant que le
téléchargement n'est pas fini, l'analyse répond 503 « téléchargement en cours ».
Le jeton n'est lu que dans .env (non versionné) ou dans la variable d'environnement HF_TOKEN ; il n'est jamais journalisé.
"""
import logging
import shutil
import threading
import time
from pathlib import Path
from typing import Optional

from app.config import settings

log = logging.getLogger("dawn.model_fetch")

RACINE = Path(__file__).resolve().parents[2]
DEPOT_HUBERT = "Edoardo-Coppola/hubert-ecg-small"

_verrou = threading.Lock()
_thread: Optional[threading.Thread] = None
_etat = {"statut": "inconnu", "message": ""}  # inconnu | pret | telechargement | erreur | desactive


def _chemin(valeur: str) -> Path:
    p = Path(valeur)
    return p if p.is_absolute() else RACINE / p


def chemin_modele() -> Path:
    return _chemin(settings.ECG_MODEL_PATH)


def dossier_hubert() -> Path:
    return _chemin(settings.ECG_HUBERT_DIR)


def fichiers_presents() -> bool:
    return chemin_modele().is_file() and (dossier_hubert() / "config.json").is_file()


def statut() -> dict:
    """Pour l'API / le front : {'statut': ..., 'message': ...}."""
    if fichiers_presents():
        return {"statut": "pret", "message": ""}
    if _etat["statut"] in ("telechargement", "erreur"):
        return dict(_etat)
    if not settings.ECG_AUTO_DOWNLOAD:
        return {"statut": "desactive", "message": "Téléchargement automatique désactivé (ECG_AUTO_DOWNLOAD=false)."}
    return {"statut": "absent", "message": "Modèle pas encore téléchargé."}


_verrou_calibration = threading.Lock()
_calibration_tentee = False
_source_calibration = "locale"  # « hugging_face » une fois le fichier du dépôt utilisé


def source_calibration() -> str:
    return _source_calibration


def chemin_calibration() -> Path:
    """
    Fichier de calibration à utiliser : celui du dépôt Hugging Face (téléchargé une fois, quelques Ko), sinon la copie
    livrée avec le backend (app/ml/artifacts/calibration_artifacts.json). Appel synchrone et rapide ; ne lève jamais :
    en cas d'échec réseau/jeton/fichier absent du dépôt, on retombe sur la copie locale (avec un avertissement).
    """
    global _calibration_tentee, _source_calibration
    from app.ml.calibration import ARTEFACTS_PAR_DEFAUT, Calibration
    import json

    local = _chemin(settings.ECG_CALIBRATION_PATH)
    with _verrou_calibration:
        if not local.is_file() and settings.ECG_AUTO_DOWNLOAD and not _calibration_tentee:
            _calibration_tentee = True
            try:
                from huggingface_hub import hf_hub_download

                local.parent.mkdir(parents=True, exist_ok=True)
                obtenu = Path(hf_hub_download(
                    repo_id=settings.ECG_HF_REPO, filename=settings.ECG_HF_CALIBRATION_FILENAME,
                    revision=settings.ECG_HF_REVISION or None, token=settings.HF_TOKEN or None, local_dir=str(local.parent),
                ))
                if obtenu.resolve() != local.resolve():
                    shutil.move(str(obtenu), str(local))
                log.info("Calibration récupérée depuis %s (%s).", settings.ECG_HF_REPO, settings.ECG_HF_CALIBRATION_FILENAME)
            except Exception as e:
                log.warning("Calibration absente du dépôt Hugging Face ou inaccessible (%s) : utilisation de la copie livrée avec le backend.", _nettoyer(e))
        if local.is_file():
            try:  # fichier du dépôt exploitable ? (structure attendue) sinon on l'ignore plutôt que de casser l'analyse
                with open(local, encoding="utf-8") as f:
                    Calibration(json.load(f))
                _source_calibration = "hugging_face"
                return local
            except Exception as e:
                log.warning("Fichier de calibration téléchargé inutilisable (%s) : copie livrée utilisée.", _nettoyer(e))
        _source_calibration = "locale"
        return ARTEFACTS_PAR_DEFAUT


def _nettoyer(e: Exception) -> str:
    texte = f"{type(e).__name__}: {str(e)[:300]}"
    jeton = settings.HF_TOKEN
    return texte.replace(jeton, "hf_***") if jeton else texte


def _telecharger():
    from huggingface_hub import HfApi, hf_hub_download, snapshot_download

    token = settings.HF_TOKEN or None  # None -> jeton éventuellement mis en cache par `huggingface-cli login`

    chemin_calibration()  # petit fichier : récupéré en premier (n'échoue jamais)

    # 1) code + config HuBERT (public, quelques Ko, révision figée dans REVISION.txt)
    dh = dossier_hubert()
    if not (dh / "config.json").is_file():
        sha = settings.ECG_HUBERT_REVISION or HfApi().model_info(DEPOT_HUBERT).sha
        log.info("Téléchargement de la config HuBERT-ECG (%s@%s)", DEPOT_HUBERT, sha[:8])
        snapshot_download(repo_id=DEPOT_HUBERT, revision=sha, local_dir=str(dh), allow_patterns=["*.json", "*.py", "*.txt", "*.md"])
        (dh / "REVISION.txt").write_text(f"{DEPOT_HUBERT}\nrevision {sha}\n", encoding="utf-8")

    # 2) poids DAWN-ECG (privé)
    cible = chemin_modele()
    if not cible.is_file():
        if not (settings.HF_TOKEN or token):
            log.warning("HF_TOKEN non défini : tentative avec le jeton mis en cache par huggingface-cli (si présent).")
        cible.parent.mkdir(parents=True, exist_ok=True)
        log.info("Téléchargement du modèle DAWN-ECG depuis %s (~730 Mo)…", settings.ECG_HF_REPO)
        obtenu = Path(hf_hub_download(
            repo_id=settings.ECG_HF_REPO, filename=settings.ECG_HF_FILENAME,
            revision=settings.ECG_HF_REVISION or None, token=token, local_dir=str(cible.parent),
        ))
        if obtenu.resolve() != cible.resolve():  # ECG_MODEL_PATH n'a pas le même nom que le fichier du dépôt
            shutil.move(str(obtenu), str(cible))
        log.info("Modèle DAWN-ECG prêt : %s (%.0f Mo)", cible, cible.stat().st_size / 1e6)


def _prechauffer():
    """Charge le modèle ECG et le modèle d'embeddings du RAG pour que la première requête de chaque type soit rapide."""
    from app.services import ecg_service, rag_service

    if fichiers_presents():
        try:
            t = time.perf_counter()
            ecg_service.prechauffer()
            log.info("Modèle ECG chargé en mémoire (%.1f s).", time.perf_counter() - t)
        except Exception as e:
            log.error("Préchauffage du modèle ECG impossible : %s", _nettoyer(e))
    try:
        t = time.perf_counter()
        rag_service.get_embeddings()
        log.info("Modèle d'embeddings chargé (%.1f s).", time.perf_counter() - t)
    except Exception as e:
        log.error("Préchauffage des embeddings impossible : %s", _nettoyer(e))


def demarrer_prechauffage():
    if settings.ECG_PRECHARGER:
        threading.Thread(target=_prechauffer, name="dawn-warmup", daemon=True).start()


def _travail():
    try:
        _telecharger()
        _etat.update(statut="pret", message="")
        demarrer_prechauffage()
    except Exception as e:  # message lisible pour le médecin / l'admin ; jeton masqué
        msg = _nettoyer(e)
        log.error("Échec du téléchargement du modèle ECG : %s", msg)
        _etat.update(
            statut="erreur",
            message=(f"Téléchargement du modèle ECG impossible ({msg}). Vérifie HF_TOKEN (lecture) et le nom du dépôt "
                     f"« {settings.ECG_HF_REPO} » dans .env."),
        )


def demarrer_telechargement() -> bool:
    """Lance le téléchargement en arrière-plan s'il est nécessaire et possible. Renvoie True si un téléchargement est en cours/lancé."""
    global _thread
    if fichiers_presents():
        return False
    if not settings.ECG_AUTO_DOWNLOAD:
        return False
    with _verrou:
        if _thread is not None and _thread.is_alive():
            return True
        _etat.update(statut="telechargement", message="Téléchargement du modèle ECG en cours (~730 Mo), réessaie dans quelques minutes.")
        _thread = threading.Thread(target=_travail, name="dawn-model-fetch", daemon=True)
        _thread.start()
        return True


def reessayer() -> bool:
    """Relance après une erreur (efface l'état d'erreur)."""
    if _etat["statut"] == "erreur":
        _etat.update(statut="inconnu", message="")
    return demarrer_telechargement()
