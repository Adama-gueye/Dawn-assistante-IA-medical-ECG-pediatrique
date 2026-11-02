from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_administrateur
from app.security import hash_password
from app import models, schemas

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/medecins", response_model=schemas.MedecinOut, status_code=status.HTTP_201_CREATED)
def creer_compte_medecin(
    payload: schemas.MedecinCreate,
    db: Session = Depends(get_db),
    _admin: models.Administrateur = Depends(require_administrateur),
):
    """creerCompteMedecin() — reserve a l'Administrateur."""
    if db.query(models.Utilisateur).filter(models.Utilisateur.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Cet email est deja utilise")

    medecin = models.Medecin(
        nom=payload.nom,
        prenom=payload.prenom,
        email=payload.email,
        mot_de_passe=hash_password(payload.mot_de_passe),
        specialite=payload.specialite,
        numero_ordre=payload.numero_ordre,
        est_actif=payload.est_actif,
    )
    db.add(medecin)
    db.commit()
    db.refresh(medecin)
    return medecin


@router.get("/utilisateurs", response_model=List[schemas.UtilisateurOut])
def gerer_utilisateurs(
    db: Session = Depends(get_db),
    _admin: models.Administrateur = Depends(require_administrateur),
):
    """gererUtilisateurs() — vue d'ensemble de tous les comptes."""
    return db.query(models.Utilisateur).order_by(models.Utilisateur.date_creation.desc()).all()


@router.patch("/utilisateurs/{utilisateur_id}/statut")
def changer_statut_utilisateur(
    utilisateur_id: int,
    est_actif: bool,
    db: Session = Depends(get_db),
    _admin: models.Administrateur = Depends(require_administrateur),
):
    """Active / desactive un compte (medecin le plus souvent)."""
    user = db.query(models.Utilisateur).filter(models.Utilisateur.id == utilisateur_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.est_actif = est_actif
    db.commit()
    return {"id": user.id, "est_actif": user.est_actif}


@router.get("/medecins", response_model=List[schemas.MedecinOut])
def lister_medecins(
    db: Session = Depends(get_db),
    _admin: models.Administrateur = Depends(require_administrateur),
):
    return db.query(models.Medecin).order_by(models.Medecin.date_creation.desc()).all()


# ------------------------------------------------------------
# STATISTIQUES
# ------------------------------------------------------------
_MOIS_FR = ["Janv.", "Févr.", "Mars", "Avr.", "Mai", "Juin",
            "Juil.", "Août", "Sept.", "Oct.", "Nov.", "Déc."]
_TYPE_LABELS = {"texte": "Texte", "ecg": "ECG"}


def _bornes_mois(mois: str | None):
    """Renvoie (debut, fin_exclusive, "YYYY-MM") du mois demande, ou du mois en cours si absent/invalide."""
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


def _derniers_mois(n: int = 3):
    """Liste des n derniers mois (le plus ancien d'abord), mois courant inclus."""
    today = datetime.utcnow()
    y, m = today.year, today.month
    mois = []
    for _ in range(n):
        mois.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    return list(reversed(mois))


def _age_en_annees(naissance: date) -> int:
    today = date.today()
    return today.year - naissance.year - ((today.month, today.day) < (naissance.month, naissance.day))


def _tranche_age(naissance) -> str:
    if naissance is None:
        return "Non renseigné"
    age = _age_en_annees(naissance)
    if age < 1:
        return "< 1 an"
    if age < 5:
        return "1–4 ans"
    if age < 10:
        return "5–9 ans"
    if age < 15:
        return "10–14 ans"
    return "15 ans et +"


@router.get("/statistiques", response_model=schemas.StatistiquesOut)
def statistiques(
    mois: str | None = Query(None, description='Mois a afficher, format "YYYY-MM". Par defaut : mois en cours.'),
    db: Session = Depends(get_db),
    _admin: models.Administrateur = Depends(require_administrateur),
):
    """
    Statistiques de la plateforme pour un mois donne (dossiers/sessions/messages crees ce
    mois-la), calculees a partir des donnees reelles. `evolution` reste toujours une
    tendance glissante sur les 3 derniers mois, independamment du mois choisi.
    """
    debut_mois, fin_mois, mois_effectif = _bornes_mois(mois)

    # --- Comptes medecins (pas de notion de mois : etat actuel des comptes)
    medecins_actifs = db.query(models.Medecin).filter(models.Medecin.est_actif.is_(True)).count()
    medecins_total = db.query(models.Medecin).count()

    # --- Totaux du mois selectionne
    dossiers = db.query(models.DossierPatient).filter(
        models.DossierPatient.date_creation >= debut_mois, models.DossierPatient.date_creation < fin_mois
    ).count()
    sessions_q = db.query(models.SessionRAG).filter(
        models.SessionRAG.date_session >= debut_mois, models.SessionRAG.date_session < fin_mois
    )
    sessions = sessions_q.count()
    sessions_perso = sessions_q.filter(models.SessionRAG.dossier_patient_id.is_(None)).count()
    messages_q = db.query(models.MessageMedecin).filter(
        models.MessageMedecin.date_message >= debut_mois, models.MessageMedecin.date_message < fin_mois
    )
    messages = messages_q.count()

    # --- Messages par type (texte / ecg), sur le mois selectionne
    par_type = dict(
        messages_q.with_entities(models.MessageMedecin.type, func.count(models.MessageMedecin.id))
        .group_by(models.MessageMedecin.type).all()
    )
    messages_par_type = [
        schemas.CompteurLabel(label=lbl, valeur=par_type.get(key, 0)) for key, lbl in _TYPE_LABELS.items()
    ]

    # --- Dossiers par sexe et par tranche d'age (population totale suivie, pas seulement le mois)
    naissances_sexes = db.query(models.DossierPatient.sexe, models.DossierPatient.date_naissance).all()
    sexes = {"Garçons": 0, "Filles": 0, "Non renseigné": 0}
    tranches = {t: 0 for t in ["< 1 an", "1–4 ans", "5–9 ans", "10–14 ans", "15 ans et +", "Non renseigné"]}
    for sexe, naissance in naissances_sexes:
        sexes["Garçons" if sexe == "M" else "Filles" if sexe == "F" else "Non renseigné"] += 1
        tranches[_tranche_age(naissance)] += 1
    dossiers_par_sexe = [schemas.CompteurLabel(label=k, valeur=v) for k, v in sexes.items() if v or k != "Non renseigné"]
    dossiers_par_tranche_age = [schemas.CompteurLabel(label=k, valeur=v) for k, v in tranches.items() if v or k != "Non renseigné"]

    # --- Base de connaissances
    base = schemas.BaseConnaissancesStats(
        documents_total=db.query(models.DocumentMedical).count(),
        documents_indexes=db.query(models.DocumentMedical).filter(models.DocumentMedical.vecteur_indexe.is_(True)).count(),
        cas_total=db.query(models.CasClinique).count(),
        cas_indexes=db.query(models.CasClinique).filter(models.CasClinique.vecteur_indexe.is_(True)).count(),
    )

    # --- Evolution sur les 3 derniers mois
    periodes = _derniers_mois(3)
    debut = datetime(periodes[0][0], periodes[0][1], 1)
    cles = {p: {"d": 0, "s": 0, "m": 0, "scores": []} for p in periodes}

    for (dt,) in db.query(models.DossierPatient.date_creation).filter(models.DossierPatient.date_creation >= debut):
        if (dt.year, dt.month) in cles:
            cles[(dt.year, dt.month)]["d"] += 1
    for (dt,) in db.query(models.SessionRAG.date_session).filter(models.SessionRAG.date_session >= debut):
        if (dt.year, dt.month) in cles:
            cles[(dt.year, dt.month)]["s"] += 1
    for (dt,) in db.query(models.MessageMedecin.date_message).filter(models.MessageMedecin.date_message >= debut):
        if (dt.year, dt.month) in cles:
            cles[(dt.year, dt.month)]["m"] += 1
    for source in (models.SourceDocument, models.SourceCas):
        rows = (
            db.query(models.MessageMedecin.date_message, source.score_relevance)
            .join(source, source.message_id == models.MessageMedecin.id)
            .filter(models.MessageMedecin.date_message >= debut)
        )
        for dt, score in rows:
            if (dt.year, dt.month) in cles:
                cles[(dt.year, dt.month)]["scores"].append(score)

    evolution = []
    for (y, m) in periodes:
        c = cles[(y, m)]
        moyenne = round(sum(c["scores"]) / len(c["scores"]) * 100) if c["scores"] else None
        evolution.append(schemas.EvolutionMois(
            mois=f"{y}-{m:02d}", label=_MOIS_FR[m - 1],
            nouveaux_dossiers=c["d"], nouvelles_sessions=c["s"], nouveaux_messages=c["m"],
            pertinence_moyenne=moyenne,
        ))

    # --- Activite par medecin
    dossiers_par_med = dict(
        db.query(models.DossierPatient.medecin_id, func.count(models.DossierPatient.id))
        .filter(models.DossierPatient.date_creation >= debut_mois, models.DossierPatient.date_creation < fin_mois)
        .group_by(models.DossierPatient.medecin_id).all()
    )
    sessions_par_med = dict(
        db.query(models.SessionRAG.medecin_id, func.count(models.SessionRAG.id))
        .filter(models.SessionRAG.date_session >= debut_mois, models.SessionRAG.date_session < fin_mois)
        .group_by(models.SessionRAG.medecin_id).all()
    )
    messages_par_med = dict(
        db.query(models.SessionRAG.medecin_id, func.count(models.MessageMedecin.id))
        .join(models.MessageMedecin, models.MessageMedecin.session_rag_id == models.SessionRAG.id)
        .filter(models.MessageMedecin.date_message >= debut_mois, models.MessageMedecin.date_message < fin_mois)
        .group_by(models.SessionRAG.medecin_id).all()
    )
    activite = [
        schemas.ActiviteMedecin(
            id=med.id, prenom=med.prenom, nom=med.nom, specialite=med.specialite, est_actif=med.est_actif,
            dossiers=dossiers_par_med.get(med.id, 0),
            sessions=sessions_par_med.get(med.id, 0),
            messages=messages_par_med.get(med.id, 0),
        )
        for med in db.query(models.Medecin).order_by(models.Medecin.date_creation.desc()).all()
    ]

    return schemas.StatistiquesOut(
        mois=mois_effectif,
        medecins_actifs=medecins_actifs,
        medecins_inactifs=medecins_total - medecins_actifs,
        dossiers=dossiers, sessions=sessions, sessions_personnelles=sessions_perso, messages=messages,
        messages_par_type=messages_par_type,
        dossiers_par_sexe=dossiers_par_sexe,
        dossiers_par_tranche_age=dossiers_par_tranche_age,
        base_connaissances=base,
        evolution=evolution,
        activite_medecins=activite,
    )
