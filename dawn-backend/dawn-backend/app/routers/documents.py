import os
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_medecin
from app.services import rag_service
from app import models, schemas

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "documents")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=schemas.DocumentMedicalOut, status_code=201)
def ajouter_document(
    titre: str = Form(...),
    type_doc: str = Form(None),
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
    _medecin: models.Medecin = Depends(require_medecin),
):
    nom_fichier = f"{uuid.uuid4().hex}_{fichier.filename}"
    chemin = os.path.join(UPLOAD_DIR, nom_fichier)
    with open(chemin, "wb") as f:
        f.write(fichier.file.read())

    document = models.DocumentMedical(
        titre=titre, type_doc=type_doc, chemin_fichier=chemin, vecteur_indexe=False
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("", response_model=List[schemas.DocumentMedicalOut])
def lister_documents(db: Session = Depends(get_db), _medecin: models.Medecin = Depends(require_medecin)):
    return db.query(models.DocumentMedical).order_by(models.DocumentMedical.id.desc()).all()


@router.post("/{document_id}/indexer", response_model=schemas.DocumentMedicalOut)
def indexer(
    document_id: int,
    db: Session = Depends(get_db),
    _medecin: models.Medecin = Depends(require_medecin),
):
    """indexer() — declenche l'ingestion du document dans le pipeline RAG."""
    document = db.query(models.DocumentMedical).filter(models.DocumentMedical.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")

    succes = rag_service.indexer_document(db, document)
    document.vecteur_indexe = succes
    document.date_indexation = datetime.utcnow() if succes else document.date_indexation
    db.commit()
    db.refresh(document)
    return document
