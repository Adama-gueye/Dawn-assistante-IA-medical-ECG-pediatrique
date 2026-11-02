"""
Suppression d'une session et de TOUT ce qui en depend : messages, sources citees
(cascade ORM deja declaree sur les modeles) et fichiers ECG stockes sur disque.

Les fichiers .hea/.dat sont des donnees patient : les laisser traîner apres la
suppression du message qui les reference serait une fuite de donnees silencieuse.
"""
import os
from typing import List

from sqlalchemy.orm import Session

from app import models

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads"))


def supprimer_session(db: Session, session: "models.SessionRAG") -> List[str]:
    """
    Marque la session (et, par cascade, ses messages et leurs sources) pour suppression.
    Renvoie les chemins de fichiers ECG a effacer APRES le commit (si le commit echoue,
    on ne doit surtout pas avoir deja detruit les fichiers).
    """
    fichiers: List[str] = []
    for message in list(session.messages):
        if message.type == "ecg":
            fichiers.extend([message.fichier_ecg, message.fichier_ecg_dat])
    db.delete(session)
    return [f for f in fichiers if f]


def effacer_fichiers(chemins: List[str]) -> None:
    """Efface les fichiers, uniquement s'ils sont bien dans le dossier d'uploads."""
    for chemin in chemins:
        try:
            chemin_abs = os.path.abspath(chemin)
            if os.path.commonpath([chemin_abs, UPLOAD_DIR]) == UPLOAD_DIR and os.path.isfile(chemin_abs):
                os.remove(chemin_abs)
        except (OSError, ValueError):
            pass  # fichier deja absent, droits, ou autre disque (Windows) : ne doit pas faire echouer la suppression
