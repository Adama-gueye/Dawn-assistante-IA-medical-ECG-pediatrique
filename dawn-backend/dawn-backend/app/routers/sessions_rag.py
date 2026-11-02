import json
import os
import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import require_medecin
from app.services import rag_service, ecg_service, wfdb_service, session_cleanup
from app import models, schemas

router = APIRouter(prefix="/medecin/sessions", tags=["sessions_rag"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _save_upload(file: UploadFile, sous_dossier: str) -> str:
    dossier = os.path.join(UPLOAD_DIR, sous_dossier)
    os.makedirs(dossier, exist_ok=True)
    nom_fichier = f"{uuid.uuid4().hex}_{file.filename}"
    chemin = os.path.join(dossier, nom_fichier)
    with open(chemin, "wb") as f:
        f.write(file.file.read())
    return chemin


def _save_wfdb_pair(fichier_hea: UploadFile, fichier_dat: UploadFile, sous_dossier: str):
    """
    Enregistre le couple .hea/.dat avec le MEME nom de base (seule l'extension
    change) : c'est une exigence du format WFDB, `wfdb.rdheader()` cherche le
    .dat a cote du .hea en ne changeant que l'extension.
    """
    dossier = os.path.join(UPLOAD_DIR, sous_dossier)
    os.makedirs(dossier, exist_ok=True)
    base = uuid.uuid4().hex
    chemin_hea = os.path.join(dossier, base + ".hea")
    chemin_dat = os.path.join(dossier, base + ".dat")
    with open(chemin_hea, "wb") as f:
        f.write(fichier_hea.file.read())
    with open(chemin_dat, "wb") as f:
        f.write(fichier_dat.file.read())
    return chemin_hea, chemin_dat, os.path.join(dossier, base)


@router.post("", response_model=schemas.SessionRAGOut, status_code=201)
def creer_session(
    payload: schemas.SessionRAGCreate,
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    if payload.dossier_patient_id is not None:
        dossier = (
            db.query(models.DossierPatient)
            .filter(
                models.DossierPatient.id == payload.dossier_patient_id,
                models.DossierPatient.medecin_id == medecin.id,
            )
            .first()
        )
        if not dossier:
            raise HTTPException(status_code=404, detail="Dossier introuvable")

    session = models.SessionRAG(
        titre=payload.titre, dossier_patient_id=payload.dossier_patient_id, medecin_id=medecin.id
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("", response_model=List[schemas.SessionRAGOut])
def lister_sessions(
    dossier_patient_id: Optional[int] = None,
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    q = db.query(models.SessionRAG).filter(models.SessionRAG.medecin_id == medecin.id)
    if dossier_patient_id is not None:
        q = q.filter(models.SessionRAG.dossier_patient_id == dossier_patient_id)
    return q.order_by(models.SessionRAG.date_session.desc()).all()


@router.get("/{session_id}/messages", response_model=List[schemas.MessageMedecinOut])
def lister_messages(
    session_id: int,
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    session = _get_session_or_404(db, session_id, medecin.id)
    # Chargement groupé : sans cela, chaque message déclenchait des requêtes séparées (sources, documents, et
    # surtout le texte complet + le vecteur d'embedding de chaque document cité) -> ouverture de session très lente.
    return (
        db.query(models.MessageMedecin)
        .filter(models.MessageMedecin.session_rag_id == session.id)
        .options(
            selectinload(models.MessageMedecin.sources_document)
            .selectinload(models.SourceDocument.document)
            .load_only(models.DocumentMedical.titre),
            selectinload(models.MessageMedecin.sources_cas),
        )
        .order_by(models.MessageMedecin.date_message, models.MessageMedecin.id)
        .all()
    )


@router.post("/{session_id}/messages/texte", response_model=schemas.MessageMedecinOut, status_code=201)
def envoyer_message_texte(
    session_id: int,
    payload: schemas.MessageTexteCreate,
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    session = _get_session_or_404(db, session_id, medecin.id)

    try:
        rag_result = rag_service.repondre_avec_rag(db, payload.contenu, session.dossier_patient_id, _derniere_analyse_ecg(db, session.id))
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail=(
                "Le moteur de réponse n'a pas pu répondre (Ollama arrêté, modèle non téléchargé "
                f"ou mémoire insuffisante ?) : {str(e)[:200]}"
            ),
        )

    message = models.MessageTexte(
        session_rag_id=session.id, contenu=payload.contenu, reponse=rag_result.reponse
    )
    db.add(message)
    db.flush()  # pour obtenir message.id avant de creer les sources

    for s in rag_result.sources_document:
        db.add(models.SourceDocument(
            message_id=message.id, document_id=s.document_id,
            extrait=s.extrait, score_relevance=s.score_relevance,
        ))
    for s in rag_result.sources_cas:
        db.add(models.SourceCas(
            message_id=message.id, cas_id=s.cas_id,
            extrait=s.extrait, score_relevance=s.score_relevance,
        ))

    _titrer_si_besoin(session, payload.contenu)
    db.commit()
    db.refresh(message)
    return message


@router.post("/{session_id}/messages/ecg", response_model=schemas.MessageMedecinOut, status_code=201)
def envoyer_message_ecg(
    session_id: int,
    question: Optional[str] = Form(None),
    age_annees: Optional[float] = Form(None, description="Obligatoire pour une session SANS dossier patient"),
    sexe: Optional[str] = Form(None, description="M ou F — obligatoire pour une session SANS dossier patient"),
    fichier_hea: UploadFile = File(..., description="Fichier d'en-tete WFDB (.hea)"),
    fichier_dat: UploadFile = File(..., description="Fichier de signal WFDB associe (.dat)"),
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    """
    Analyse un enregistrement ECG au format WFDB (paire .hea + .dat — le format
    du dataset d'entrainement). Rien n'est demande au medecin en dehors du
    fichier lui-meme et d'une question optionnelle : les derivations/frequence/
    duree sont lues dans le header, et l'age/le sexe viennent du DossierPatient
    lie a la session (s'il y en a un).
    """
    session = _get_session_or_404(db, session_id, medecin.id)
    age_jours, sexe = _contexte_clinique_ecg(db, session, age_annees, sexe)  # 422 avant d'ecrire quoi que ce soit
    chemin_hea, chemin_dat, chemin_base = _save_wfdb_pair(fichier_hea, fichier_dat, "ecg")

    try:
        meta = wfdb_service.lire_metadonnees(chemin_base)
    except Exception:
        session_cleanup.effacer_fichiers([chemin_hea, chemin_dat])
        raise HTTPException(status_code=422, detail="Fichier WFDB illisible (paire .hea/.dat invalide ou incomplete)")

    resultat = _analyser_ou_erreur(chemin_base, question, age_jours, sexe, meta.nb_derivations, [chemin_hea, chemin_dat])

    message = models.MessageECG(
        session_rag_id=session.id,
        fichier_ecg=chemin_hea,
        fichier_ecg_dat=chemin_dat,
        format_fichier="wfdb",
        question=question,
        reponse=resultat.reponse,
        nb_derivations=meta.nb_derivations,
        frequence_hz=meta.frequence_hz,
        duree_secondes=meta.duree_secondes,
        age_jours=age_jours,
        sexe=sexe,
        resultat_json=ecg_service.serialiser_details(resultat),
    )
    db.add(message)
    _titrer_si_besoin(session, question, repli="Analyse ECG")
    db.commit()
    db.refresh(message)
    return message


@router.post("/{session_id}/messages/ecg-csv", response_model=schemas.MessageMedecinOut, status_code=201)
def envoyer_message_ecg_depuis_csv(
    session_id: int,
    frequence_hz: float = Form(500, description="Frequence d'echantillonnage du CSV, en Hz"),
    a_entete: bool = Form(True, description="Le CSV a-t-il une ligne d'en-tete nommant les derivations ?"),
    question: Optional[str] = Form(None),
    age_annees: Optional[float] = Form(None, description="Obligatoire pour une session SANS dossier patient"),
    sexe: Optional[str] = Form(None, description="M ou F — obligatoire pour une session SANS dossier patient"),
    fichier: UploadFile = File(..., description="CSV du signal : une colonne par derivation, une ligne par echantillon"),
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    """
    OUTIL DE TEST — convertit un CSV en paire WFDB puis lance exactement la
    meme analyse que l'endpoint .hea/.dat normal. Permet de tester le flux
    complet avant d'avoir de vrais fichiers WFDB ou le modele final branche.
    Non destine a un usage clinique reel (aucune garantie sur la fiabilite
    d'un CSV, contrairement a un vrai export d'appareil).
    """
    session = _get_session_or_404(db, session_id, medecin.id)
    age_jours, sexe = _contexte_clinique_ecg(db, session, age_annees, sexe)  # 422 avant d'ecrire quoi que ce soit

    dossier_ecg = os.path.join(UPLOAD_DIR, "ecg")
    os.makedirs(dossier_ecg, exist_ok=True)
    base = uuid.uuid4().hex
    chemin_base = os.path.join(dossier_ecg, base)

    try:
        meta = wfdb_service.csv_vers_wfdb(fichier.file, chemin_base, frequence_hz=frequence_hz, a_entete=a_entete)
    except Exception as e:
        session_cleanup.effacer_fichiers([chemin_base + ".hea", chemin_base + ".dat"])
        raise HTTPException(status_code=422, detail=f"CSV illisible ou mal forme : {e}")

    chemin_hea, chemin_dat = chemin_base + ".hea", chemin_base + ".dat"

    resultat = _analyser_ou_erreur(chemin_base, question, age_jours, sexe, meta.nb_derivations, [chemin_hea, chemin_dat])

    message = models.MessageECG(
        session_rag_id=session.id,
        fichier_ecg=chemin_hea,
        fichier_ecg_dat=chemin_dat,
        format_fichier="wfdb_depuis_csv",
        question=question,
        reponse=resultat.reponse,
        nb_derivations=meta.nb_derivations,
        frequence_hz=meta.frequence_hz,
        duree_secondes=meta.duree_secondes,
        age_jours=age_jours,
        sexe=sexe,
        resultat_json=ecg_service.serialiser_details(resultat),
    )
    db.add(message)
    _titrer_si_besoin(session, question, repli="Analyse ECG (test CSV)")
    db.commit()
    db.refresh(message)
    return message


@router.delete("/{session_id}", status_code=204)
def supprimer_session_endpoint(
    session_id: int,
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    """Supprime definitivement la session, ses messages, leurs sources et les fichiers ECG associes."""
    session = _get_session_or_404(db, session_id, medecin.id)
    fichiers = session_cleanup.supprimer_session(db, session)
    db.commit()
    session_cleanup.effacer_fichiers(fichiers)


@router.patch("/{session_id}", response_model=schemas.SessionRAGOut)
def renommer_session(
    session_id: int,
    payload: schemas.SessionRAGUpdate,
    db: Session = Depends(get_db),
    medecin: models.Medecin = Depends(require_medecin),
):
    """Renomme une session (le titre automatique n'est qu'une proposition)."""
    session = _get_session_or_404(db, session_id, medecin.id)
    titre = payload.titre.strip()
    if not titre:
        raise HTTPException(status_code=422, detail="Le titre ne peut pas etre vide")
    session.titre = titre
    db.commit()
    db.refresh(session)
    return session


def _resumer_analyse_ecg(message_ecg) -> str:
    """
    Résumé STRUCTURÉ de l'analyse ECG, lisible sans ambiguïté par un petit modèle de langage : chaque catégorie est dite
    DÉTECTÉE / INDÉTERMINÉE / non détectée, avec sa probabilité ET son seuil de détection (un petit modèle confondait
    « détectée à 23 % » avec « absente », et « fiabilité limitée » avec la probabilité).
    """
    try:
        d = json.loads(message_ecg.resultat_json) if message_ecg.resultat_json else None
    except ValueError:
        d = None
    if not d or "categories" not in d:
        return message_ecg.reponse  # analyse sans détail structuré (ancienne ligne) : texte tel qu'affiché
    cats = d["categories"]
    detectees = sorted((c for c in cats if c["detecte"]), key=lambda c: -c["p_calibree"])
    indet = [c["code"] for c in cats if not c["detecte"] and c["conforme"] == "indetermine"]
    autres = [c["code"] for c in cats if not c["detecte"]]
    lignes = ["Catégories DÉTECTÉES par le modèle (anomalie signalée, même si la probabilité est faible : chaque catégorie a son propre seuil) :"]
    if detectees:
        for c in detectees:
            lignes.append(f"- {c['code']} — {c['libelle']} : probabilité {round(100 * c['p_calibree'])} %, supérieure ou égale au seuil de détection de cette catégorie ({round(100 * c['seuil'])} %) → DÉTECTÉE")
    else:
        lignes.append("- aucune")
    lignes.append("Catégories INDÉTERMINÉES (le modèle ne peut pas trancher) : " + (", ".join(indet) if indet else "aucune"))
    lignes.append("Catégories non détectées : " + (", ".join(autres) if autres else "aucune") + " (cela ne prouve pas leur absence).")
    lignes.append(f"Incertitude globale : {d.get('incertitude', 'inconnue')}.")
    attention = [l.strip("- ").strip() for l in (message_ecg.reponse or "").splitlines() if "⚠" in l]
    if attention:
        lignes.append("Points d'attention du modèle (fiabilité mesurée sur le jeu de test, ce n'est PAS la probabilité de ce patient ; « fiabilité limitée » veut dire que la détection est souvent fausse : prudence) :")
        lignes += [f"- {l}" for l in attention]
    return "\n".join(lignes)


def _derniere_analyse_ecg(db: Session, session_id: int, max_analyses: int = 3) -> Optional[str]:
    """Dernières analyses ECG de la session (les 3 plus récentes, de la plus ancienne à la plus récente), avec l'âge et le sexe
    utilisés, pour que le RAG explique CES résultats au lieu d'en inventer."""
    derniers = (
        db.query(models.MessageECG)
        .filter(models.MessageECG.session_rag_id == session_id)
        .order_by(models.MessageECG.id.desc())
        .limit(max_analyses)
        .all()
    )
    derniers = [m for m in reversed(derniers) if m.reponse]
    if not derniers:
        return None
    blocs = []
    for i, m in enumerate(derniers, start=1):
        contexte = []
        if m.age_jours is not None:
            contexte.append(f"âge {rag_service._age_lisible(m.age_jours)}")
        if m.sexe:
            contexte.append(f"sexe {m.sexe}")
        suffixe = f"\n(Données utilisées pour l'analyse : {', '.join(contexte)}.)" if contexte else ""
        etiquette = f"ANALYSE ECG n°{i} sur {len(derniers)}" + (" (la plus récente)" if i == len(derniers) else " (plus ancienne)")
        blocs.append(f"{etiquette}\n{_resumer_analyse_ecg(m)}{suffixe}")
    return "\n\n".join(blocs)


def _contexte_clinique_ecg(db: Session, session: models.SessionRAG, age_annees: Optional[float], sexe: Optional[str]):
    """
    Age et sexe du patient pour l'analyse ECG (entrees du modele) :
    - session liee a un dossier : on prend ceux du dossier (jamais ceux du formulaire) ;
    - session personnelle (sans dossier) : OBLIGATOIRES dans la requete — on n'invente pas de valeurs.
    Renvoie (age_jours, sexe « M »/« F »). Leve 422 avant tout ecriture de fichier.
    """
    if session.dossier_patient_id is not None:
        dossier = db.query(models.DossierPatient).filter(models.DossierPatient.id == session.dossier_patient_id).first()
        if dossier is None or not dossier.date_naissance or (dossier.sexe or "").strip().upper()[:1] not in ("M", "F"):
            raise HTTPException(
                status_code=422,
                detail="Le dossier de ce patient n'a pas d'age ou de sexe renseigne : completez-le (bouton Modifier) avant l'analyse ECG.",
            )
        return (date.today() - dossier.date_naissance).days, dossier.sexe.strip().upper()[:1]

    sexe_norm = (sexe or "").strip().upper()[:1]
    if age_annees is None or sexe_norm not in ("M", "F"):
        raise HTTPException(
            status_code=422,
            detail="Session sans dossier patient : l'age et le sexe (M ou F) du patient sont obligatoires pour l'analyse ECG.",
        )
    if age_annees < 0:
        raise HTTPException(status_code=422, detail="Age invalide.")
    return round(age_annees * 365.25), sexe_norm


def _analyser_ou_erreur(chemin_base, question, age_jours, sexe, nb_derivations, fichiers):
    """Appelle le service ECG ; en cas d'echec, supprime les fichiers deposes (pas de donnees patient orphelines)."""
    try:
        return ecg_service.analyser_ecg(chemin_base, question, age_jours=age_jours, sexe=sexe, nb_derivations=nb_derivations)
    except ecg_service.EntreeInvalide as e:
        session_cleanup.effacer_fichiers(fichiers)
        raise HTTPException(status_code=422, detail=str(e))
    except ecg_service.ModeleIndisponible as e:
        session_cleanup.effacer_fichiers(fichiers)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        session_cleanup.effacer_fichiers(fichiers)
        raise HTTPException(status_code=500, detail=f"Echec de l'analyse ECG : {type(e).__name__}: {str(e)[:200]}")


def _titre_est_par_defaut(titre: str) -> bool:
    """Titres crees automatiquement par le front a l'ouverture d'une session.
    Un titre saisi par le medecin (formulaire de session personnelle) n'en fait pas partie."""
    return titre == "Nouvelle session" or titre.startswith("Session — ")


def _titrer_si_besoin(session: models.SessionRAG, texte: Optional[str], repli: Optional[str] = None) -> None:
    """Donne a la session un titre adapte au sujet, une seule fois (1er message)."""
    if not _titre_est_par_defaut(session.titre):
        return
    if texte and rag_service.est_small_talk(texte):
        return  # « bonjour » ne decrit pas le sujet : on attend la premiere vraie question
    if texte and texte.strip():
        session.titre = rag_service.generer_titre(texte)
    elif repli:
        session.titre = repli


def _get_session_or_404(db: Session, session_id: int, medecin_id: int) -> models.SessionRAG:
    session = (
        db.query(models.SessionRAG)
        .filter(models.SessionRAG.id == session_id, models.SessionRAG.medecin_id == medecin_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session introuvable")
    return session