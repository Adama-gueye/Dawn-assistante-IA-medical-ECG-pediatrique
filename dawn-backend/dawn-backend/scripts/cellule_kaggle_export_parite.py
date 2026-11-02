# ======================================================================================
# CELLULE À AJOUTER À LA FIN DU NOTEBOOK KAGGLE (session encore ouverte, variables en mémoire)
# Exporte quelques ECG de TEST (.hea/.dat) avec les probabilités EXACTES calculées par le notebook,
# pour vérifier que le backend reproduit les mêmes sorties (scripts/test_parite.py).
# Résultat : /kaggle/working/parite_backend.zip  (à télécharger depuis l'onglet Output)
# ======================================================================================
import json, shutil
from pathlib import Path
import numpy as np

ENS_TEST = np.asarray(CANDS["ENS"]["test"])
assert len(test_df) == len(ENS_TEST) == len(test_labels), "test_df, CANDS et test_labels ne sont pas alignés"

# probabilités de chaque run du modèle final (clé (perte, graine) -> étiquette « ASL:42 »)
runs_test = {}
for cle, v in RUNS.items():
    if isinstance(cle, tuple) and len(cle) == 2 and isinstance(v, dict) and "test_probs" in v:
        runs_test[f"{cle[0]}:{cle[1]}"] = np.asarray(v["test_probs"])
print("runs exportés :", list(runs_test))

rng = np.random.default_rng(7)
ages, nr = test_df["age_years"], test_df["n_real"]
choix = []
for masque, k in (((nr == 12) & (ages < 1), 1), ((nr == 12) & ages.between(4, 9), 1), ((nr == 12) & (ages >= 12), 1), ((nr == 9), 2)):
    candidats = np.where(masque.values)[0]
    choix += [int(i) for i in rng.choice(candidats, size=min(k, len(candidats)), replace=False)]

sortie = Path("/kaggle/working/parite_backend"); sortie.mkdir(exist_ok=True)
items = []
for i in choix:
    ligne = test_df.iloc[i]
    ecg_id = str(ligne["ECG_ID"])
    hea = Path(SIGNAL_INDEX[ecg_id][".hea"])
    for ext in (".hea", ".dat"):
        shutil.copy(hea.with_suffix(ext), sortie / (hea.stem + ext))
    items.append({
        "ecg_id": ecg_id, "fichier": hea.stem,
        "age_annees": float(ligne["age_years"]), "sexe": "M" if float(ligne["sex_m"]) == 1.0 else "F", "n_real": int(ligne["n_real"]),
        "probas_ens": ENS_TEST[i].tolist(),
        "probas_par_run": {tag: arr[i].tolist() for tag, arr in runs_test.items()},
        "vraies_categories": [c for c, v in zip(CATEGORIES, test_labels[i]) if v],
    })
(sortie / "parite_attendu.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
shutil.make_archive("/kaggle/working/parite_backend", "zip", sortie)
print(f"{len(items)} ECG exportés -> /kaggle/working/parite_backend.zip")
for it in items:
    print(f"  {it['ecg_id']}  {it['age_annees']:.2f} ans  {it['sexe']}  {it['n_real']} dérivations  vérité={it['vraies_categories']}")
