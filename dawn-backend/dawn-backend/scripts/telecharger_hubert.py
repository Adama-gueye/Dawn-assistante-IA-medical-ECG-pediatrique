"""
Télécharge UNE FOIS (connexion internet requise) la configuration et le code du dépôt Hugging Face
« Edoardo-Coppola/hubert-ecg-small » dans models/hubert-ecg-small/ — SANS les poids (inutiles : ils sont remplacés par ceux
du fine-tuning contenus dans dawn_ecg_model_final.pt).

Après cela, le backend fonctionne hors ligne et n'exécute que le code présent dans ce dossier (revision figée).

Usage (racine du backend, venv activé) :
    python scripts/telecharger_hubert.py
    python scripts/telecharger_hubert.py --revision <hash>    # pour figer une version précise
"""
import argparse
from pathlib import Path

DEPOT = "Edoardo-Coppola/hubert-ecg-small"
RACINE = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--revision", default=None, help="hash de commit à figer (par défaut : la dernière version)")
    ap.add_argument("--dossier", default=str(RACINE / "models" / "hubert-ecg-small"))
    a = ap.parse_args()

    from huggingface_hub import HfApi, snapshot_download

    sha = a.revision or HfApi().model_info(DEPOT).sha
    dossier = Path(a.dossier)
    snapshot_download(repo_id=DEPOT, revision=sha, local_dir=str(dossier), allow_patterns=["*.json", "*.py", "*.txt", "*.md"])
    (dossier / "REVISION.txt").write_text(f"{DEPOT}\nrevision {sha}\n", encoding="utf-8")

    fichiers = sorted(p.relative_to(dossier).as_posix() for p in dossier.rglob("*") if p.is_file())
    print(f"Dépôt {DEPOT} @ {sha}\nFichiers dans {dossier} :")
    for f in fichiers:
        print("  -", f)
    if "config.json" not in fichiers:
        raise SystemExit("ERREUR : config.json absent — le dépôt a peut-être changé de structure.")

    # Vérification : la configuration (et le code distant local) se chargent bien SANS internet
    try:
        from transformers import AutoConfig

        cfg = AutoConfig.from_pretrained(str(dossier), trust_remote_code=True, local_files_only=True)
        print(f"\nOK : configuration chargée hors ligne (hidden_size={getattr(cfg, 'hidden_size', '?')}). "
              f"Note la révision {sha} dans ton mémoire (reproductibilité).")
    except Exception as e:
        print(f"\nATTENTION : le chargement hors ligne a échoué : {type(e).__name__}: {str(e)[:300]}")
        print("Envoie-moi ce message et la liste des fichiers ci-dessus.")


if __name__ == "__main__":
    main()
