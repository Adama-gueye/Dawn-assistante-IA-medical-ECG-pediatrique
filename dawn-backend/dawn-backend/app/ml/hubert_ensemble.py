"""
Modèle DAWN-ECG : ensemble de HuBERT-ECG fine-tunés (port de la cellule 14 du notebook DAWN V6) et inférence.

Ce module importe torch : il n'est chargé que quand le modèle est activé (voir app/services/ecg_service.py).

Le backbone est construit à partir de config.json + du code du dépôt Hugging Face « Edoardo-Coppola/hubert-ecg-small »
copiés dans models/hubert-ecg-small (scripts/telecharger_hubert.py) : aucun accès internet à l'exécution, et le code
exécuté (trust_remote_code) est celui qui est dans le projet. Les poids pré-entraînés ne servent à rien ici :
ils sont intégralement remplacés par ceux du fine-tuning (state_dict du .pt).
"""
import copy
import gc
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from app.ml import bundle as B
from app.ml.calibration import Calibration


class HuBERTECG_ML(nn.Module):
    """Identique à la classe du notebook (branche d'entraînement aléatoire retirée : ici toujours en évaluation).
    Les noms d'attributs (backbone, clinical_fc, classifier) doivent rester identiques : ce sont les clés du state_dict."""

    def __init__(self, backbone, n_classes=12, clinical_dim=3, dropout=0.3):
        super().__init__()
        self.backbone = backbone
        if hasattr(backbone, "freeze_feature_encoder"):
            backbone.freeze_feature_encoder()
        hid = backbone.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.clinical_fc = nn.Sequential(nn.Linear(clinical_dim, 32), nn.ReLU(inplace=True))
        self.classifier = nn.Linear(hid + 32, n_classes)

    def _encode(self, x):  # x : (B, 12, 500) à 100 Hz
        x = x / x.abs().amax(dim=(1, 2), keepdim=True).clamp_min(1e-6)
        out = self.backbone(x.flatten(1))
        h = out.last_hidden_state if hasattr(out, "last_hidden_state") else out[0]
        return h.mean(1)

    def forward(self, sig, clinical):
        x = F.avg_pool1d(sig.float(), 5)  # 500 Hz -> 100 Hz
        feats = 0.5 * (self._encode(x[:, :, :500]) + self._encode(x[:, :, -500:]))  # moyenne des deux moitiés de 5 s
        c = self.clinical_fc(clinical)
        return self.classifier(torch.cat([self.dropout(feats), c], dim=1))


def _construire_backbone(dossier_hubert: Path):
    from transformers import AutoConfig, AutoModel

    try:
        cfg = AutoConfig.from_pretrained(str(dossier_hubert), trust_remote_code=True, local_files_only=True)
    except Exception as e:
        raise RuntimeError(
            f"Impossible de lire la configuration HuBERT-ECG dans « {dossier_hubert} » "
            f"({type(e).__name__}: {str(e)[:200]}). Lance d'abord : python scripts/telecharger_hubert.py"
        ) from e
    cfg.mask_time_prob = 0.0  # comme à l'entraînement : pas de masquage SpecAugment
    cfg.layerdrop = 0.0
    try:
        return AutoModel.from_config(cfg, trust_remote_code=True)
    except Exception as e_cfg:
        try:  # repli : charge aussi les poids du dépôt s'ils sont présents (inutile, mais certains dépôts l'exigent)
            return AutoModel.from_pretrained(str(dossier_hubert), config=cfg, trust_remote_code=True, local_files_only=True)
        except Exception as e_pre:
            raise RuntimeError(
                "Construction du backbone HuBERT-ECG impossible : "
                f"from_config -> {type(e_cfg).__name__}: {str(e_cfg)[:200]} ; from_pretrained -> {type(e_pre).__name__}: {str(e_pre)[:200]}"
            ) from e_pre


def _charger_bundle(chemin: Path, weights_only: bool):
    kwargs = dict(map_location="cpu", weights_only=weights_only)
    try:
        return torch.load(str(chemin), mmap=True, **kwargs)  # mmap : évite de doubler la mémoire pendant le chargement
    except Exception as e:
        if not (isinstance(e, TypeError) or "mmap" in str(e).lower()):
            raise
        return torch.load(str(chemin), **kwargs)


class HuBERTEnsemble:
    def __init__(self, chemin_pt, dossier_hubert, calibration: Calibration, selection: str = "all",
                 weights_only: bool = True, n_threads: int = 0, device: str = "cpu"):
        if n_threads and n_threads > 0:
            torch.set_num_threads(n_threads)
        chemin_pt = Path(chemin_pt)
        try:
            bundle = _charger_bundle(chemin_pt, weights_only)
        except Exception as e:
            conseil = (" Si l'erreur mentionne 'weights_only', mets ECG_TORCH_WEIGHTS_ONLY=false dans .env "
                       "(uniquement pour un fichier que tu as toi-même produit)." if "weights_only" in str(e).lower() or "unpickl" in str(e).lower() else "")
            raise RuntimeError(f"Lecture du fichier de modèle impossible ({type(e).__name__}: {str(e)[:250]}).{conseil}") from e

        B.verifier_bundle(bundle, calibration.categories, dict(zip(calibration.categories, calibration.seuils_bruts)))
        retenus = B.choisir_modeles(bundle["models"], selection)
        self.ensemble_complet = len(retenus) == len(bundle["models"])
        self.n_modeles_total = len(bundle["models"])

        backbone = _construire_backbone(Path(dossier_hubert))
        self.modeles: List[nn.Module] = []
        self.etiquettes: List[str] = []
        for m in retenus:
            modele = HuBERTECG_ML(copy.deepcopy(backbone), n_classes=len(calibration.categories))
            try:
                modele.load_state_dict(m["state_dict"], strict=True)
            except RuntimeError as e:
                raise RuntimeError(
                    f"Les poids de {B.etiquette(m)} ne correspondent pas à l'architecture HuBERT-ECG chargée depuis « {dossier_hubert} » "
                    f"(version du code Hugging Face ou de transformers différente de l'entraînement ?). Détail : {str(e)[:400]}"
                ) from e
            modele.to(device).eval()
            for p in modele.parameters():
                p.requires_grad_(False)
            self.modeles.append(modele)
            self.etiquettes.append(B.etiquette(m))
        self.device = device
        del bundle, retenus, backbone
        gc.collect()

    def predire(self, fenetres: np.ndarray, clinique: np.ndarray, detail: bool = False):
        """
        fenetres : (K, 12, 5000) float32 ; clinique : (3,).
        Reproduit `predict` du notebook : sigmoïde des logits de chaque fenêtre, moyenne sur les K fenêtres,
        puis moyenne sur les modèles. Renvoie (12,) — ou ((12,), [(étiquette, (12,)), ...]) si detail=True.
        """
        with torch.inference_mode():
            s = torch.from_numpy(np.ascontiguousarray(fenetres, dtype=np.float32)).to(self.device)
            c = torch.from_numpy(np.asarray(clinique, dtype=np.float32)).to(self.device)
            c = c.unsqueeze(0).expand(s.shape[0], -1).contiguous()
            par_modele = [torch.sigmoid(m(s, c).float()).mean(0).cpu().numpy() for m in self.modeles]
        moyenne = np.mean(par_modele, axis=0)
        if detail:
            return moyenne, list(zip(self.etiquettes, par_modele))
        return moyenne
