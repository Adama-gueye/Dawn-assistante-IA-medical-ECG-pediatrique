"""
Prétraitement ECG : port fidèle des cellules 6, 8 et 9 du notebook DAWN V6.

Toute modification ici change ce que le modèle reçoit : le modèle a été entraîné avec EXACTEMENT ce prétraitement
(500 Hz, retrait de la ligne de base sur 1 s, normalisation par l'écart-type global des dérivations présentes,
écrêtage à ±10, stockage en float16, 5 fenêtres de 10 s réparties sur tout l'enregistrement).

Seul ajout par rapport au notebook : le rééchantillonnage à 500 Hz si l'enregistrement a une autre fréquence
(le jeu d'entraînement était entièrement à 500 Hz).
"""
from fractions import Fraction
from typing import List, Optional, Tuple

import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.signal import resample_poly

SAMPLE_RATE = 500
WINDOW_SEC = 10
WINDOW_LEN = WINDOW_SEC * SAMPLE_RATE
N_LEADS = 12
N_EVAL_WIN = 5
AGE_SCALE = 15.0
STD_LEADS = ["I", "II", "III", "AVR", "AVL", "AVF", "V1", "V2", "V3", "V4", "V5", "V6"]


def _canon(name) -> str:
    return str(name).strip().upper().replace(" ", "")


def mapper_derivations(p_signal_t: np.ndarray, noms: Optional[List[str]]) -> Tuple[np.ndarray, int]:
    """
    p_signal_t : (nb_dérivations_du_fichier, T). Renvoie ([12, T], nb de dérivations réelles).
    Les dérivations absentes (enregistrements à 9 dérivations) restent à 0 ; ordre standard I, II, III, AVR, AVL, AVF, V1..V6.
    """
    sig = np.nan_to_num(p_signal_t.astype(np.float32))
    n_real = sig.shape[0]
    out = np.zeros((N_LEADS, sig.shape[1]), dtype=np.float32)
    canon = [_canon(n) for n in noms] if noms is not None else None
    if canon is not None and all(n in STD_LEADS for n in canon):
        for i, n in enumerate(canon):
            out[STD_LEADS.index(n)] = sig[i]
    else:
        k = min(n_real, N_LEADS)
        out[:k] = sig[:k]
    return out, n_real


def _lire_record_renomme(chemin_base: str):
    """
    Le backend enregistre la paire envoyée sous un nom aléatoire (<uuid>.hea / <uuid>.dat), alors que le .hea cite encore le
    nom d'origine du .dat (ex. « P08004_E01.dat ») : wfdb.rdrecord() cherche alors un fichier qui n'existe pas. On lit donc
    une copie temporaire dont l'en-tête désigne le .dat réellement présent (le signal n'est pas modifié).
    """
    import shutil
    import tempfile
    from pathlib import Path

    import wfdb

    base = Path(chemin_base)
    lignes = base.with_suffix(".hea").read_text(encoding="utf-8", errors="replace").splitlines()
    idx = [i for i, l in enumerate(lignes) if l.strip() and not l.lstrip().startswith("#")]
    if not idx:
        raise ValueError("En-tête WFDB vide.")
    premiere = lignes[idx[0]].split()
    try:
        n_sig = int(premiere[1])
    except (IndexError, ValueError):
        raise ValueError("En-tête WFDB invalide (nombre de dérivations illisible).")
    nom = "enregistrement"
    lignes[idx[0]] = " ".join([nom] + premiere[1:])
    for i in idx[1:1 + n_sig]:
        champs = lignes[i].split()
        champs[0] = nom + ".dat"
        lignes[i] = " ".join(champs)
    with tempfile.TemporaryDirectory(prefix="dawn_wfdb_") as tmp:
        shutil.copyfile(base.with_suffix(".dat"), Path(tmp) / (nom + ".dat"))
        (Path(tmp) / (nom + ".hea")).write_text("\n".join(lignes) + "\n", encoding="utf-8")
        return wfdb.rdrecord(str(Path(tmp) / nom))


def lire_wfdb(chemin_base_sans_extension: str) -> Tuple[np.ndarray, int, float]:
    """Lit un enregistrement WFDB -> (signal [12, T] brut, nb de dérivations réelles, fréquence d'échantillonnage)."""
    rec = _lire_record_renomme(chemin_base_sans_extension)
    sig, n_real = mapper_derivations(rec.p_signal.T, list(rec.sig_name))
    return sig, n_real, float(rec.fs)


def reechantillonner(sig: np.ndarray, fs: float) -> np.ndarray:
    """Ramène le signal à 500 Hz (rien à faire si déjà à 500 Hz)."""
    if abs(fs - SAMPLE_RATE) < 1e-6:
        return sig
    frac = Fraction(SAMPLE_RATE / fs).limit_denominator(1000)
    return resample_poly(sig, frac.numerator, frac.denominator, axis=1).astype(np.float32)


def pretraiter(sig: np.ndarray) -> np.ndarray:
    """Dérive de ligne de base + mise à l'échelle ('record'). Les dérivations absentes restent à 0. Sortie float16, comme le cache du notebook."""
    sig = sig.astype(np.float32)
    present = np.abs(sig).sum(axis=1) > 0
    sig = sig - uniform_filter1d(sig, size=SAMPLE_RATE, axis=1, mode="nearest")
    sd = sig[present].std() if present.any() else 1.0
    sig = sig / (sd if sd > 1e-6 else 1.0)
    sig[~present] = 0.0
    return np.clip(sig, -10, 10).astype(np.float16)


def _crop(sig: np.ndarray, start: int) -> np.ndarray:
    T = sig.shape[1]
    if T >= WINDOW_LEN:
        return sig[:, start:start + WINDOW_LEN]
    return np.pad(sig, ((0, 0), (0, WINDOW_LEN - T)))


def fenetres(sig16: np.ndarray, k: int = N_EVAL_WIN) -> np.ndarray:
    """K fenêtres de 10 s régulièrement réparties sur TOUT l'enregistrement -> (K, 12, 5000) float32."""
    T = sig16.shape[1]
    starts = np.linspace(0, max(T - WINDOW_LEN, 0), k).round().astype(int)
    return np.stack([_crop(sig16, st).astype(np.float32) for st in starts])


def age_annees_depuis_jours(age_jours: float) -> float:
    return float(age_jours) / 365.25


def sexe_masculin(sexe: Optional[str]) -> float:
    return 1.0 if str(sexe).strip().lower().startswith("m") else 0.0


def vecteur_clinique(age_annees: float, sexe: Optional[str], n_real: int) -> np.ndarray:
    """[âge/15 écrêté à [0, 1.2], sexe masculin (1/0), nb de dérivations réelles / 12]."""
    age_norm = float(np.clip(age_annees / AGE_SCALE, 0, 1.2))
    return np.array([age_norm, sexe_masculin(sexe), n_real / 12.0], dtype=np.float32)


def preparer_ecg(chemin_base: str, age_annees: float, sexe: Optional[str]):
    """Chaîne complète : fichier WFDB -> (fenêtres (K,12,5000), vecteur clinique (3,), infos de lecture)."""
    sig, n_real, fs = lire_wfdb(chemin_base)
    sig = reechantillonner(sig, fs)
    fen = fenetres(pretraiter(sig))
    infos = {"nb_derivations": n_real, "frequence_hz": fs, "duree_s": round(sig.shape[1] / SAMPLE_RATE, 2),
             "reechantillonne": abs(fs - SAMPLE_RATE) > 1e-6}
    return fen, vecteur_clinique(age_annees, sexe, n_real), infos
