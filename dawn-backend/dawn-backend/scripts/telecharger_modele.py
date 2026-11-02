"""
Télécharge le modèle DAWN-ECG (~730 Mo) depuis le dépôt Hugging Face PRIVÉ vers models/ :
  - dawn_ecg_model_final.pt  -> models/dawn_ecg_model_final.pt   (chemin attendu par le backend)
  - calibration_artifacts.json -> models/calibration_artifacts.json (utilisé par le backend à la place de la copie livrée)

Le jeton Hugging Face n'est JAMAIS écrit dans le code ni dans un fichier versionné :
  PowerShell :  $env:HF_TOKEN = "hf_..."        puis   python scripts/telecharger_modele.py
  ou une fois pour toutes :  huggingface-cli login   (le jeton est alors lu depuis le cache de huggingface_hub)
Utilise un jeton « fine-grained » en LECTURE SEULE limité à ce dépôt.

Licence : le modèle dérive de HuBERT-ECG (CC BY-NC) -> usage non commercial uniquement.
"""
import argparse
import os
from pathlib import Path

DEPOT_PAR_DEFAUT = "adama9900/dawn-ecg-pediatrique"
RACINE = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--depot", default=os.environ.get("DAWN_HF_REPO", DEPOT_PAR_DEFAUT))
    ap.add_argument("--revision", default=None, help="hash de commit à figer (recommandé pour la soutenance)")
    ap.add_argument("--dossier", default=str(RACINE / "models"))
    ap.add_argument("--sans-modele", action="store_true", help="ne télécharge pas le .pt (seulement la calibration)")
    a = ap.parse_args()

    from huggingface_hub import hf_hub_download

    token = os.environ.get("HF_TOKEN") or None  # None -> jeton mis en cache par `huggingface-cli login`
    Path(a.dossier).mkdir(parents=True, exist_ok=True)
    fichiers = ["calibration_artifacts.json"] + ([] if a.sans_modele else ["dawn_ecg_model_final.pt"])
    for nom in fichiers:
        try:
            chemin = hf_hub_download(repo_id=a.depot, filename=nom, revision=a.revision, token=token, local_dir=a.dossier)
        except Exception as e:
            raise SystemExit(
                f"ECHEC du téléchargement de « {nom} » depuis {a.depot} : {type(e).__name__}: {str(e)[:250]}\n"
                "Vérifie : le nom du dépôt, que HF_TOKEN est défini (ou `huggingface-cli login` fait) et que le jeton a accès à ce dépôt privé."
            )
        taille = Path(chemin).stat().st_size / 1e6
        print(f"OK  {nom}  ({taille:.1f} Mo) -> {chemin}")
    print("\nEnsuite : python scripts/telecharger_hubert.py   (code HuBERT-ECG, public, ~quelques Ko)")


if __name__ == "__main__":
    main()
