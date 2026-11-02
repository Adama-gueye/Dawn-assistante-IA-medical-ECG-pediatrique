"""
Mesure du temps de réponse côté serveur, enregistré dans un fichier CSV (une ligne par requête mesurée) :

    horodatage ; type ; statut_http ; duree_s

type : « ecg » (analyse d'un enregistrement WFDB), « ecg_csv » (test à partir d'un CSV) ou « texte » (question au RAG).
La durée va de la réception de la requête par l'API à l'envoi de la réponse : elle inclut la lecture du fichier, le calcul
(modèle ECG, ou recherche documentaire + génération par Ollama pour le texte) et l'écriture en base ; elle n'inclut ni le
réseau ni l'affichage dans le navigateur. Résumé des mesures : python scripts/resume_temps.py
"""
import csv
import threading
from datetime import datetime
from pathlib import Path

from app.config import settings

RACINE = Path(__file__).resolve().parents[2]
_verrou = threading.Lock()
ENTETE = ["horodatage", "type", "statut_http", "duree_s"]


def type_de_requete(methode: str, chemin: str):
    if methode != "POST":
        return None
    if chemin.endswith("/messages/ecg-csv"):
        return "ecg_csv"
    if chemin.endswith("/messages/ecg"):
        return "ecg"
    if chemin.endswith("/messages/texte"):
        return "texte"
    return None


def chemin_fichier() -> Path:
    p = Path(settings.TEMPS_LOG_PATH)
    return p if p.is_absolute() else RACINE / p


def enregistrer(type_requete: str, statut: int, duree_s: float) -> None:
    try:
        f = chemin_fichier()
        with _verrou:
            f.parent.mkdir(parents=True, exist_ok=True)
            nouveau = not f.is_file()
            with open(f, "a", newline="", encoding="utf-8") as h:
                w = csv.writer(h, delimiter=";")
                if nouveau:
                    w.writerow(ENTETE)
                w.writerow([datetime.now().isoformat(timespec="seconds"), type_requete, statut, f"{duree_s:.2f}"])
    except OSError:
        pass  # la mesure ne doit jamais faire échouer une requête
