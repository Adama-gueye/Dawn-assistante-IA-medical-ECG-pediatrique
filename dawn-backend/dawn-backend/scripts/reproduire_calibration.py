"""
Reconstruit les artefacts d'inférence du notebook DAWN V6 (calibration de Platt, seuils, prédiction conforme,
seuils de sécurité) à partir de predictions_test_val.npz, et les compare aux fichiers produits par le notebook.
Le code reprend VERBATIM les fonctions des cellules 16 et 33.
"""
import json, sys
import numpy as np, pandas as pd
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, average_precision_score, f1_score, hamming_loss

RES = sys.argv[1]
z = np.load(f"{RES}/predictions_test_val.npz", allow_pickle=True)
CATEGORIES = [str(c) for c in z["categories"]]; N_CLASSES = len(CATEGORIES)
val_labels, test_labels = z["val_labels"].astype(np.float64), z["test_labels"].astype(np.float64)
PV, PT = z["ENS_val"].astype(np.float64), z["ENS_test"].astype(np.float64)

# ---------- cellule 16 ----------
THR_GRID = np.linspace(0.02, 0.95, 94)
def f1_grid(p, y, grid=THR_GRID):
    pred = p[:, None] >= grid[None, :]; yy = (y[:, None] > 0.5)
    tp = (pred & yy).sum(0); fp = (pred & ~yy).sum(0); fn = (~pred & yy).sum(0)
    return 2 * tp / np.maximum(2 * tp + fp + fn, 1)
def calibrate_thresholds(probs, labels):
    thr = np.full(N_CLASSES, 0.5)
    for i in range(N_CLASSES):
        f = f1_grid(probs[:, i], labels[:, i])
        if f.max() > 0: thr[i] = float(np.median(THR_GRID[np.isclose(f, f.max())]))
    return thr
def safe_ap(y, p): return average_precision_score(y, p) if y.sum() > 0 else np.nan
def safe_auc(y, p): return roc_auc_score(y, p) if 0 < y.sum() < len(y) else np.nan
def full_report(probs, labels, thr):
    pred = (probs >= thr[None, :]).astype(int); rows = []
    for i, c in enumerate(CATEGORIES):
        y, p = labels[:, i] > 0.5, pred[:, i] > 0
        tp, fp, fn = int((y & p).sum()), int((~y & p).sum()), int((y & ~p).sum())
        rows.append({"f1": 2 * tp / max(2 * tp + fp + fn, 1)})
    macro = float(pd.DataFrame(rows)["f1"].mean())
    return macro, float((pred == labels).all(axis=1).mean())

# ---------- cellule 33 ----------
EPS = 1e-6
def logit(p): p = np.clip(p, EPS, 1 - EPS); return np.log(p / (1 - p))
def sigm(z): return 1 / (1 + np.exp(-z))
def nll(p, y): p = np.clip(p, EPS, 1 - EPS); return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
def ece(p, y, n_bins=15):
    p, y = p.ravel(), y.ravel(); b = np.minimum((p * n_bins).astype(int), n_bins - 1); e = 0.0
    for k in range(n_bins):
        m = b == k
        if m.any(): e += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(e)

zv, zt = logit(PV), logit(PT)
platt = {}; pv_pl, pt_pl = PV.copy(), PT.copy()
for i in range(N_CLASSES):
    if val_labels[:, i].sum() >= 10:
        lr_ = LogisticRegression(C=1e4, max_iter=1000).fit(zv[:, [i]], val_labels[:, i])
        pv_pl[:, i], pt_pl[:, i] = lr_.predict_proba(zv[:, [i]])[:, 1], lr_.predict_proba(zt[:, [i]])[:, 1]
        platt[CATEGORIES[i]] = {"coef": float(lr_.coef_[0, 0]), "intercept": float(lr_.intercept_[0])}
    else:
        platt[CATEGORIES[i]] = None   # < 10 positifs en validation : pas de calibration (identité), comme le notebook
PVc, PTc = pv_pl, pt_pl
THR_raw = calibrate_thresholds(PV, val_labels)
THRc = calibrate_thresholds(PVc, val_labels)

def conformal(pv, yv, pt, alpha):
    sets = np.zeros(pt.shape + (2,), bool); qs = np.zeros((N_CLASSES, 2))
    for c in range(N_CLASSES):
        for y in (0, 1):
            s = 1 - (pv[yv[:, c] == y, c] if y == 1 else 1 - pv[yv[:, c] == y, c]); n = len(s); k = int(np.ceil((n + 1) * (1 - alpha)))
            qs[c, y] = np.sort(s)[k - 1] if (k <= n and n > 0) else np.inf
            sets[:, c, y] = (1 - (pt[:, c] if y == 1 else 1 - pt[:, c])) <= qs[c, y]
    return sets, qs
yt, yv = test_labels.astype(int), val_labels.astype(int)
conf, conf_rows = {}, []
for alpha in (0.05, 0.10, 0.20):
    sets, qs = conformal(PVc, yv, PTc, alpha); conf[alpha] = qs
    size = sets.sum(-1); single = size == 1; cover = np.take_along_axis(sets, yt[..., None], axis=2)[..., 0]
    pred_lab = sets[..., 1].astype(int); err_single = (pred_lab != yt) & single; auto = single.all(1)
    conf_rows.append({"alpha": alpha, "couverture_positifs": float(cover[yt == 1].mean()), "couverture_negatifs": float(cover[yt == 0].mean()),
                      "pct_decisions_certaines": float(100 * single.mean()), "pct_ambigues({0,1})": float(100 * (size == 2).mean()),
                      "erreur_parmi_decisions_certaines": float(err_single.sum() / max(single.sum(), 1)),
                      "pct_ECG_entierement_automatiques": float(100 * auto.mean())})
conf_df = pd.DataFrame(conf_rows)

safe_thr = {}
for i, c in enumerate(CATEGORIES):
    pv_i, yv_i = PVc[:, i], val_labels[:, i] > 0.5
    ok = [t for t in THR_GRID if yv_i.sum() and ((pv_i >= t) & yv_i).sum() / yv_i.sum() >= 0.90]
    safe_thr[c] = round(float(max(ok) if ok else THR_GRID[0]), 3)

# ---------- COMPARAISONS avec ce que le notebook a écrit ----------
ok_all = True
def verifie(nom, calc, ref, tol=1e-6):
    global ok_all
    bon = abs(calc - ref) <= tol; ok_all &= bon
    print(f"{'OK   ' if bon else 'ECART'} {nom:62s} recalculé={calc:.6f}  notebook={ref:.6f}")

summ = json.load(open(f"{RES}/summary.json"))
for c, i in zip(CATEGORIES, range(N_CLASSES)):
    verifie(f"seuil brut {c} (summary.json)", float(THR_raw[i]), summ["thresholds"][c])
cal = pd.read_csv(f"{RES}/calibration.csv").set_index("calibration")
verifie("ECE globale AVANT calibration (test)", ece(PT, test_labels), float(cal.iloc[0]["test_ECE_global"]))
verifie("ECE globale APRÈS Platt (test)", ece(PTc, test_labels), summ["approche_probabiliste"]["ECE_global_apres"])
verifie("NLL test après Platt", nll(PTc, test_labels), float(cal.loc["Platt par catégorie", "test_NLL"]))
mf1_raw, em_raw = full_report(PT, test_labels, THR_raw)
verifie("macro-F1 test, seuils bruts (summary.json)", mf1_raw, summ["test_summary"]["macro_f1"])
mf1_c, em_c = full_report(PTc, test_labels, THRc)
print(f"      macro-F1 test après recalibrage = {mf1_c:.4f}   (le notebook affichait 0.5511)")
cs = pd.read_csv(f"{RES}/conformal_summary.csv")
for _, r in cs.iterrows():
    row = conf_df[np.isclose(conf_df.alpha, r["alpha"])].iloc[0]
    for k in ("couverture_positifs", "couverture_negatifs", "pct_decisions_certaines", "erreur_parmi_decisions_certaines"):
        verifie(f"conforme α={r['alpha']:.2f} {k}", float(row[k]), float(r[k]), tol=1e-6)
sf = pd.read_csv(f"{RES}/safety_thresholds_recall90.csv")
for _, r in sf.iterrows():
    verifie(f"seuil sécurité rappel90 {r['categorie']}", safe_thr[r["categorie"]], float(r["seuil_rappel90"]), tol=1e-3)
print("\n=> TOUT CONCORDE AVEC LE NOTEBOOK" if ok_all else "\n=> DES ECARTS : voir lignes ECART")

# ---------- compléments pour l'application : fiabilité par catégorie et repères d'incertitude ----------
def Hb(p): p = np.clip(p, EPS, 1 - EPS); return -(p * np.log(p) + (1 - p) * np.log(1 - p))
predc = (PTc >= THRc[None, :]).astype(int)
sets10, _ = conformal(PVc, yv, PTc, 0.10)
metriques = {}
for i, c in enumerate(CATEGORIES):
    y, p = yt[:, i] > 0, predc[:, i] > 0
    tp, fp, fn = int((y & p).sum()), int((~y & p).sum()), int((y & ~p).sum())
    metriques[c] = {"support_test": int(y.sum()), "precision": round(tp / max(tp + fp, 1), 4), "rappel": round(tp / max(tp + fn, 1), 4),
                    "f1": round(2 * tp / max(2 * tp + fp + fn, 1), 4),
                    "pct_ambigu_conforme": round(float(100 * (sets10[:, i, 0] & sets10[:, i, 1]).mean()), 1)}
u_ecg = Hb(PTc).mean(1)
tertiles = [float(np.quantile(u_ecg, 1 / 3)), float(np.quantile(u_ecg, 2 / 3))]
print("\nincertitude par ECG (entropie moyenne), tertiles du test :", [round(t, 4) for t in tertiles])
print("précision/rappel par catégorie aux seuils calibrés (test) :")
for c, m in metriques.items(): print(f"  {c}: n={m['support_test']:4d} précision={m['precision']:.3f} rappel={m['rappel']:.3f} f1={m['f1']:.3f} ambigu={m['pct_ambigu_conforme']:.0f}%")

def inf_vers_null(a): return [[None if np.isinf(v) else float(v) for v in ligne] for ligne in a]
art = {
    "version": 1,
    "origine": "reconstruit depuis predictions_test_val.npz (ENS, validation) avec le code des cellules 16 et 33 du notebook DAWN V6 ; "
               "chaque valeur a été comparée aux fichiers produits par le notebook (voir verification_calibration.txt)",
    "categories": CATEGORIES,
    "ensemble": "moyenne arithmétique des probabilités des 6 modèles (ASL et CB × graines 42, 1337, 2024), puis moyenne sur les fenêtres",
    "eps": EPS,
    "platt": platt,
    "platt_note": "p_calibree = sigmoid(coef * logit(p_ensemble) + intercept) ; null = pas de calibration (moins de 10 positifs en validation)",
    "seuils_bruts": {c: float(THR_raw[i]) for i, c in enumerate(CATEGORIES)},
    "seuils_bruts_note": "à appliquer aux probabilités NON calibrées de l'ensemble (ce que contient le .pt)",
    "seuils_calibres": {c: float(THRc[i]) for i, c in enumerate(CATEGORIES)},
    "seuils_calibres_note": "à appliquer aux probabilités calibrées (macro-F1 test %.4f)" % mf1_c,
    "seuils_securite_rappel90": safe_thr,
    "conforme": {f"{a:.2f}": {"q": inf_vers_null(q)} for a, q in conf.items()},
    "conforme_note": "q[c][y] ; null = infini. Étiquette y retenue pour la catégorie c si 1-(p si y==1 sinon 1-p) <= q[c][y] ; "
                     "les deux étiquettes retenues = ambigu, aucune = vide",
    "metriques_test_reference": summ["test_summary"],
    "metriques_test_par_categorie": metriques,
    "metriques_test_par_categorie_note": "mesurées sur le jeu de test, aux seuils calibrés ; support_test < 30 = évaluation peu fiable",
    "incertitude_tertiles": tertiles,
    "incertitude_note": "entropie binaire moyenne des 12 catégories (probabilités calibrées) ; < tertile 1 = faible, < tertile 2 = moyenne, sinon élevée",
}
json.dump(art, open("calibration_artifacts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("écrit : calibration_artifacts.json")
