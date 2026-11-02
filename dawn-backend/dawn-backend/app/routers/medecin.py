from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_medecin
from app import models, schemas
from app.services import session_cleanup

router = APIRouter(prefix="/medecin", tags=["medecin"])

_JOURS_PAR_UNITE = {"jours": 1, "mois": 30.44, "annees": 365.25}


def _age_vers_date_naissance(valeur: Optional[int], unite: Optional[str]) -> Optional[date]:
    """
    Convertit une saisie naturelle ("5 mois", "2 ans"...) en date de
    naissance approximative, stockee telle quelle pour permettre de
    recalculer l'age exact a chaque future analyse ECG (plutot que de figer
    un age en jours qui deviendrait faux au fil des mois).
    """
    if valeur is None or not unite:
        return None
    jours = round(valeur * _JOURS_PAR_UNITE[unite])
    return date.today() - timedelta(days=jours)


@router.post("/dossiers", response_model=schemas.DossierPatientOut, status_code=status.HTTP_201_CREATED)
def creer_dossier_patient(
    payload: schemas.DossierPatientCreate,
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    """creerDossierPatient() — cree la fiche clinique (le patient n'est plus un compte Utilisateur)."""
    dossier = models.DossierPatient(
        medecin_id=medecin.id,
        prenom_enfant=payload.prenom_enfant,
        nom_enfant=payload.nom_enfant,
        date_naissance=_age_vers_date_naissance(payload.age_valeur, payload.age_unite),
        sexe=payload.sexe,
        antecedents=payload.antecedents,
        allergies=payload.allergies,
        groupe_sanguin=payload.groupe_sanguin,
        vaccinations=payload.vaccinations,
        notes_complementaires=payload.notes_complementaires,
    )
    db.add(dossier)
    db.commit()
    db.refresh(dossier)
    return dossier


@router.get("/dossiers", response_model=List[schemas.DossierPatientOut])
def lister_dossiers(
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    return (
        db.query(models.DossierPatient)
        .filter(models.DossierPatient.medecin_id == medecin.id)
        .order_by(models.DossierPatient.date_creation.desc())
        .all()
    )


@router.get("/dossiers/{dossier_id}", response_model=schemas.DossierPatientOut)
def obtenir_dossier(
    dossier_id: int,
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    dossier = _get_dossier_or_404(db, dossier_id, medecin.id)
    return dossier


@router.patch("/dossiers/{dossier_id}", response_model=schemas.DossierPatientOut)
def modifier_dossier(
    dossier_id: int,
    payload: schemas.DossierPatientUpdate,
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    dossier = _get_dossier_or_404(db, dossier_id, medecin.id)
    data = payload.model_dump(exclude_unset=True)
    age_valeur = data.pop("age_valeur", None)
    age_unite = data.pop("age_unite", None)
    if age_valeur is not None or age_unite is not None:
        nouvelle_date = _age_vers_date_naissance(age_valeur, age_unite)
        if nouvelle_date is not None:
            dossier.date_naissance = nouvelle_date
    for field, value in data.items():
        setattr(dossier, field, value)
    db.commit()
    db.refresh(dossier)
    return dossier


def _get_dossier_or_404(db: Session, dossier_id: int, medecin_id: int) -> models.DossierPatient:
    dossier = (
        db.query(models.DossierPatient)
        .filter(models.DossierPatient.id == dossier_id, models.DossierPatient.medecin_id == medecin_id)
        .first()
    )
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return dossier


def _bornes_mois(mois: Optional[str]):
    today = datetime.utcnow()
    y, m = today.year, today.month
    if mois:
        try:
            y, m = (int(p) for p in mois.split("-", 1))
            if not (1 <= m <= 12):
                raise ValueError
        except (ValueError, TypeError):
            y, m = today.year, today.month
    debut = datetime(y, m, 1)
    fin = datetime(y + 1, 1, 1) if m == 12 else datetime(y, m + 1, 1)
    return debut, fin, f"{y:04d}-{m:02d}"


@router.delete("/dossiers/{dossier_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_dossier_patient(
    dossier_id: int,
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    """
    Supprime definitivement le dossier ET toutes les sessions qui lui sont liees (messages,
    sources, fichiers ECG compris). On ne detache pas les sessions : elles deviendraient des
    « sessions personnelles » contenant des donnees patient.
    """
    dossier = _get_dossier_or_404(db, dossier_id, medecin.id)
    sessions = db.query(models.SessionRAG).filter(models.SessionRAG.dossier_patient_id == dossier.id).all()
    fichiers = []
    for session in sessions:
        fichiers.extend(session_cleanup.supprimer_session(db, session))
    db.delete(dossier)
    db.commit()
    session_cleanup.effacer_fichiers(fichiers)


@router.get("/statistiques", response_model=schemas.StatistiquesMedecinOut)
def statistiques_medecin(
    mois: Optional[str] = Query(None, description='Mois a afficher, format "YYYY-MM". Par defaut : mois en cours.'),
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    """Activite personnelle du medecin connecte pour le mois demande (par defaut : mois en cours)."""
    debut_mois, fin_mois, mois_effectif = _bornes_mois(mois)

    dossiers_total = db.query(models.DossierPatient).filter(models.DossierPatient.medecin_id == medecin.id).count()

    sessions_q = db.query(models.SessionRAG).filter(
        models.SessionRAG.medecin_id == medecin.id,
        models.SessionRAG.date_session >= debut_mois, models.SessionRAG.date_session < fin_mois,
    )
    sessions_mois = sessions_q.count()
    sessions_perso_mois = sessions_q.filter(models.SessionRAG.dossier_patient_id.is_(None)).count()

    messages_q = (
        db.query(models.MessageMedecin)
        .join(models.SessionRAG, models.MessageMedecin.session_rag_id == models.SessionRAG.id)
        .filter(
            models.SessionRAG.medecin_id == medecin.id,
            models.MessageMedecin.date_message >= debut_mois, models.MessageMedecin.date_message < fin_mois,
        )
    )
    messages_mois = messages_q.count()
    par_type = dict(
        messages_q.with_entities(models.MessageMedecin.type, func.count(models.MessageMedecin.id))
        .group_by(models.MessageMedecin.type).all()
    )
    messages_par_type_mois = [
        schemas.CompteurLabel(label=lbl, valeur=par_type.get(key, 0))
        for key, lbl in (("texte", "Texte"), ("ecg", "ECG"))
    ]

    return schemas.StatistiquesMedecinOut(
        mois=mois_effectif,
        dossiers_total=dossiers_total,
        sessions_mois=sessions_mois,
        sessions_personnelles_mois=sessions_perso_mois,
        messages_mois=messages_mois,
        messages_par_type_mois=messages_par_type_mois,
    )
