"""
Importe et indexe les documents de reference (data/docs/*.md) dans la base
de connaissances. A lancer une fois, apres avoir cree l'extension pgvector
et applique les migrations necessaires (voir README).

Usage:
    python seed_documents.py

Idempotent : relance = re-indexe (met a jour) les documents deja presents
au lieu de les dupliquer (matching par chemin_fichier).
"""
import os
from datetime import datetime
from pathlib import Path

from app.database import SessionLocal
from app import models
from app.services import rag_service

DOCS_DIR = Path(__file__).resolve().parent / "data" / "docs"


def main():
    db = SessionLocal()
    try:
        fichiers = sorted(DOCS_DIR.glob("*.md"))
        if not fichiers:
            print(f"Aucun .md trouve dans {DOCS_DIR}")
            return

        for chemin in fichiers:
            chemin_str = str(chemin)
            document = db.query(models.DocumentMedical).filter(
                models.DocumentMedical.chemin_fichier == chemin_str
            ).first()
            if document is None:
                document = models.DocumentMedical(
                    titre=chemin.stem, chemin_fichier=chemin_str, vecteur_indexe=False
                )
                db.add(document)
                db.flush()

            succes = rag_service.indexer_document(db, document)
            document.vecteur_indexe = succes
            document.date_indexation = datetime.utcnow() if succes else document.date_indexation
            statut = "OK" if succes else "ECHEC"
            print(f"[{statut}] {chemin.name} -> {document.titre!r}")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
