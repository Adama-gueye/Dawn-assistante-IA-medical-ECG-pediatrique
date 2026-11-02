from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_medecin
from app.services import rag_service
from app import models, schemas

router = APIRouter(prefix="/cas-cliniques", tags=["cas_clinique"])


@router.post("", response_model=schemas.CasCliniqueOut, status_code=201)
def ajouter_cas(
    payload: schemas.CasCliniqueCreate,
    db: Session = Depends(get_db),
    _medecin: models.Medecin = Depends(require_medecin),
):
    cas = models.CasClinique(
        symptomes=payload.symptomes, diagnostic=payload.diagnostic,
        age_patient=payload.age_patient, source=payload.source, vecteur_indexe=False,
    )
    db.add(cas)
    db.commit()
    db.refresh(cas)
    return cas


@router.get("", response_model=List[schemas.CasCliniqueOut])
def lister_cas(db: Session = Depends(get_db), _medecin: models.Medecin = Depends(require_medecin)):
    return db.query(models.CasClinique).order_by(models.CasClinique.id.desc()).all()


@router.post("/{cas_id}/indexer", response_model=schemas.CasCliniqueOut)
def indexer(
    cas_id: int,
    db: Session = Depends(get_db),
    _medecin: models.Medecin = Depends(require_medecin),
):
    """indexer() — declenche l'ingestion du cas clinique dans le pipeline RAG."""
    cas = db.query(models.CasClinique).filter(models.CasClinique.id == cas_id).first()
    if not cas:
        raise HTTPException(status_code=404, detail="Cas clinique introuvable")

    texte = f"{cas.symptomes} {cas.diagnostic or ''}"
    succes = rag_service.indexer_cas_clinique(cas.id, texte)
    cas.vecteur_indexe = succes
    db.commit()
    db.refresh(cas)
    return cas
