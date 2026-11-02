"""
Calibration des probabilités, seuils de décision et prédiction conforme.

Python/numpy pur (aucun torch) : les paramètres viennent de artifacts/calibration_artifacts.json,
reconstruit depuis les prédictions de validation du notebook DAWN V6 (voir scripts/reproduire_calibration.py).
Les formules reprennent celles du notebook (cellule 33).
"""
import json
from pathlib import Path
from typing import Dict, List

import numpy as np

EPS = 1e-6
ARTEFACTS_PAR_DEFAUT = Path(__file__).resolve().parent / "artifacts" / "calibration_artifacts.json"


def logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def sigmoide(z):
    return 1 / (1 + np.exp(-z))


def entropie_binaire(p):
    p = np.clip(p, EPS, 1 - EPS)
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))


class Calibration:
    def __init__(self, artefacts: dict):
        self.version = artefacts.get("version")
        self.categories: List[str] = list(artefacts["categories"])
        n = len(self.categories)
        self._platt = [artefacts["platt"][c] for c in self.categories]
        self.seuils_calibres = np.array([artefacts["seuils_calibres"][c] for c in self.categories], dtype=np.float64)
        self.seuils_bruts = np.array([artefacts["seuils_bruts"][c] for c in self.categories], dtype=np.float64)
        self._q = {
            alpha: np.array([[np.inf if v is None else float(v) for v in ligne] for ligne in obj["q"]], dtype=np.float64)
            for alpha, obj in artefacts["conforme"].items()
        }
        assert all(q.shape == (n, 2) for q in self._q.values())
        self.metriques: Dict[str, dict] = artefacts["metriques_test_par_categorie"]
        self.incertitude_tertiles = tuple(artefacts["incertitude_tertiles"])

    @classmethod
    def charger(cls, chemin=ARTEFACTS_PAR_DEFAUT) -> "Calibration":
        with open(chemin, encoding="utf-8") as f:
            return cls(json.load(f))

    def calibrer(self, p):
        """p : probabilités brutes de l'ensemble, forme (12,) ou (N, 12) -> probabilités calibrées (Platt par catégorie)."""
        p = np.asarray(p, dtype=np.float64)
        z = logit(p)
        sortie = p.copy()
        for i, params in enumerate(self._platt):
            if params is not None:  # null = < 10 positifs en validation : pas de calibration (identité), comme le notebook
                sortie[..., i] = sigmoide(params["coef"] * z[..., i] + params["intercept"])
        return sortie

    def ensembles_conformes(self, p_cal, alpha: str = "0.10"):
        """Pour chaque catégorie c et étiquette y : y est retenue si 1-(p si y==1 sinon 1-p) <= q[c][y]. Forme (..., 12, 2) bool."""
        p_cal = np.asarray(p_cal, dtype=np.float64)
        q = self._q[alpha]
        sets = np.zeros(p_cal.shape + (2,), dtype=bool)
        for y in (0, 1):
            score = 1 - (p_cal if y == 1 else 1 - p_cal)
            sets[..., y] = score <= q[:, y]
        return sets

    def incertitude_globale(self, p_cal) -> float:
        return float(entropie_binaire(np.asarray(p_cal)).mean())

    def niveau_incertitude(self, p_cal) -> str:
        u = self.incertitude_globale(p_cal)
        t1, t2 = self.incertitude_tertiles
        return "faible" if u < t1 else ("moyenne" if u < t2 else "élevée")

    def analyser(self, p_brute, alpha: str = "0.10") -> List[dict]:
        """Une entrée par catégorie : probabilités brute/calibrée, détection au seuil calibré, statut conforme."""
        p_brute = np.asarray(p_brute, dtype=np.float64)
        p_cal = self.calibrer(p_brute)
        sets = self.ensembles_conformes(p_cal, alpha)
        ent = entropie_binaire(p_cal)
        lignes = []
        for i, c in enumerate(self.categories):
            retenu0, retenu1 = bool(sets[i, 0]), bool(sets[i, 1])
            if retenu1 and not retenu0:
                conforme = "present"
            elif retenu0 and not retenu1:
                conforme = "absent"
            else:
                conforme = "indetermine"  # les deux étiquettes (ambigu) ou aucune (incohérent)
            lignes.append({
                "code": c,
                "p_brute": float(p_brute[i]),
                "p_calibree": float(p_cal[i]),
                "seuil": float(self.seuils_calibres[i]),
                "detecte": bool(p_cal[i] >= self.seuils_calibres[i]),
                "conforme": conforme,
                "entropie": float(ent[i]),
            })
        return lignes
