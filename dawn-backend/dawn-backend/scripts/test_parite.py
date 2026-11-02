"""
Compare la chaîne d'inférence du BACKEND à celle du NOTEBOOK sur quelques ECG de test.

1) Dans Kaggle (session du notebook encore ouverte) : exécuter scripts/cellule_kaggle_export_parite.py
   -> télécharger parite_backend.zip (Output) et le décompresser dans un dossier.
2) Ici (racine du backend, venv activé) :
       python scripts/test_parite.py --dossier C:\\chemin\\parite_backend

Essai simple sur un enregistrement (sans comparaison) — affiche aussi le temps de calcul :
       python scripts/test_parite.py --hea C:\\chemin\\enregistrement_sans_extension --age-annees 7 --sexe F
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))

from app.ml import preprocessing as P  # noqa: E402
from app.ml.calibration import Calibration  # noqa: E402


def charger(args):
    from app.ml.hubert_ensemble import HuBERTEnsemble

    cal = Calibration.charger()
    t = time.perf_counter()
    ens = HuBERTEnsemble(RACINE / args.modele, RACINE / args.hubert, cal, selection=args.modeles,
                         weights_only=not args.sans_weights_only, n_threads=args.threads)
    print(f"Modèle chargé en {time.perf_counter() - t:.1f} s : {ens.etiquettes}")
    return ens, cal


def essai(args, ens, cal):
    fen, clin, infos = P.preparer_ecg(args.hea, args.age_annees, args.sexe)
    t = time.perf_counter()
    p = ens.predire(fen, clin)
    print(f"Inférence : {time.perf_counter() - t:.1f} s ({len(ens.modeles)} modèle(s) × {fen.shape[0]} fenêtres) — lecture : {infos}")
    for l in cal.analyser(p):
        marque = "  <-- détecté" if l["detecte"] else ""
        print(f"  {l['code']}  brute={l['p_brute']:.3f}  calibrée={l['p_calibree']:.3f}  seuil={l['seuil']:.2f}  {l['conforme']}{marque}")
    print("incertitude globale :", cal.niveau_incertitude(cal.calibrer(p)))


def parite(args, ens, cal):
    dossier = Path(args.dossier)
    attendu = json.loads((dossier / "parite_attendu.json").read_text(encoding="utf-8"))
    pire, n_ko = 0.0, 0
    for it in attendu:
        fen, clin, infos = P.preparer_ecg(str(dossier / it["fichier"]), it["age_annees"], it["sexe"])
        p_ens, par_modele = ens.predire(fen, clin, detail=True)
        ecarts = {}
        for tag, p in par_modele:
            if tag in it["probas_par_run"]:
                ecarts[tag] = float(np.abs(p - np.array(it["probas_par_run"][tag])).max())
        if ens.ensemble_complet:
            ecarts["ENSEMBLE"] = float(np.abs(p_ens - np.array(it["probas_ens"])).max())
        pire_ecg = max(ecarts.values()) if ecarts else float("nan")
        derivations_ok = infos["nb_derivations"] == it["n_real"]
        ko = (not derivations_ok) or not (pire_ecg <= args.tol)
        n_ko += ko
        pire = max(pire, pire_ecg if pire_ecg == pire_ecg else 0.0)
        print(f"{'ECHEC' if ko else 'OK   '} {it['ecg_id']:>12}  âge={it['age_annees']:.2f} ans  {it['n_real']:>2} dér.  "
              f"écart max = {pire_ecg:.4f}  (dérivations lues={infos['nb_derivations']}, attendues={it['n_real']})")
        if ko:
            detail = ", ".join(f"{k}={v:.3f}" for k, v in sorted(ecarts.items(), key=lambda kv: -kv[1])[:4])
            print(f"        plus gros écarts : {detail}")
    print(f"\nTolérance {args.tol} (le notebook calculait en demi-précision sur GPU, le backend en float32 sur CPU : ~0.001-0.005 est normal).")
    if n_ko == 0:
        print(f"PARITÉ VALIDÉE sur {len(attendu)} ECG (écart maximal observé : {pire:.4f}).")
    else:
        print(f"PARITÉ NON VALIDÉE : {n_ko}/{len(attendu)} ECG hors tolérance. Envoie-moi cette sortie complète.")
    sys.exit(1 if n_ko else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dossier", help="dossier décompressé de parite_backend.zip (contient parite_attendu.json et les .hea/.dat)")
    ap.add_argument("--hea", help="chemin d'un enregistrement WFDB SANS extension (mode essai)")
    ap.add_argument("--age-annees", type=float, default=None)
    ap.add_argument("--sexe", default=None, help="M ou F")
    ap.add_argument("--modele", default="models/dawn_ecg_model_final.pt")
    ap.add_argument("--hubert", default="models/hubert-ecg-small")
    ap.add_argument("--modeles", default="all", help="« all », un nombre N, ou « ASL:42,CB:1337 »")
    ap.add_argument("--tol", type=float, default=0.02)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--sans-weights-only", action="store_true", help="si torch refuse de lire le .pt (fichier produit par toi uniquement)")
    args = ap.parse_args()

    if not args.dossier and not args.hea:
        ap.error("indique --dossier (test de parité) ou --hea (essai simple)")
    ens, cal = charger(args)
    if args.hea:
        if args.age_annees is None or not args.sexe:
            ap.error("--age-annees et --sexe sont obligatoires avec --hea")
        essai(args, ens, cal)
    if args.dossier:
        parite(args, ens, cal)


if __name__ == "__main__":
    main()
