"""
Résume les temps de réponse enregistrés par l'API (logs/temps_reponses.csv) : nombre de mesures, minimum, médiane,
moyenne, 90e percentile et maximum, par type de requête, avec la configuration de la machine.

    python scripts/resume_temps.py
    python scripts/resume_temps.py --fichier chemin/vers/temps_reponses.csv --sans-premiere   # écarte la 1re mesure de chaque type

Seules les réponses réussies (HTTP 2xx) sont comptées. La 1re analyse après un démarrage peut être plus lente (chargement
du modèle si ECG_PRECHARGER=false) : à signaler dans le mémoire, ou à écarter avec --sans-premiere.
"""
import argparse
import csv
import os
import platform
import statistics
from collections import defaultdict
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
NOMS = {"ecg": "Analyse ECG (WFDB)", "ecg_csv": "Analyse ECG (test CSV)", "texte": "Question texte (RAG)"}


def centile(valeurs, q):
    v = sorted(valeurs)
    if len(v) == 1:
        return v[0]
    k = (len(v) - 1) * q
    i = int(k)
    return v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (k - i)


def memoire_gio():
    try:  # Linux
        with open("/proc/meminfo") as f:
            return round(int(f.readline().split()[1]) / 1024 / 1024, 1)
    except (OSError, ValueError):
        pass
    try:  # Windows
        import ctypes

        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong), ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong), ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
        st = MEMORYSTATUSEX()
        st.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
        return round(st.ullTotalPhys / 1024 ** 3, 1)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fichier", default=str(RACINE / "logs" / "temps_reponses.csv"))
    ap.add_argument("--sans-premiere", action="store_true", help="écarte la 1re mesure de chaque type")
    a = ap.parse_args()

    f = Path(a.fichier)
    if not f.is_file():
        raise SystemExit(f"Aucun fichier de mesures ({f}). Fais d'abord quelques analyses/questions avec l'API lancée.")
    par_type = defaultdict(list)
    with open(f, encoding="utf-8") as h:
        for ligne in csv.DictReader(h, delimiter=";"):
            if 200 <= int(ligne["statut_http"]) < 300:
                par_type[ligne["type"]].append(float(ligne["duree_s"]))

    ram = memoire_gio()
    print(f"Machine : {platform.system()} {platform.release()}, {os.cpu_count()} coeurs logiques"
          + (f", {ram} Gio de RAM" if ram else "") + f", Python {platform.python_version()}")
    print(f"Fichier : {f}\n")
    print(f"{'Type':<26}{'n':>4}{'min':>8}{'médiane':>9}{'moyenne':>9}{'p90':>8}{'max':>8}   (secondes)")
    for t, valeurs in sorted(par_type.items()):
        if a.sans_premiere and len(valeurs) > 1:
            valeurs = valeurs[1:]
        print(f"{NOMS.get(t, t):<26}{len(valeurs):>4}{min(valeurs):>8.2f}{statistics.median(valeurs):>9.2f}"
              f"{statistics.mean(valeurs):>9.2f}{centile(valeurs, 0.9):>8.2f}{max(valeurs):>8.2f}")
    print("\nDurée mesurée côté serveur : de la réception de la requête à l'envoi de la réponse (hors réseau et affichage).")
    print("Avec peu de mesures (n < 10), présente plutôt la fourchette min–max que le p90.")


if __name__ == "__main__":
    main()