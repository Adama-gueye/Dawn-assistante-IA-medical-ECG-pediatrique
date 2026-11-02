from datetime import datetime, date
from typing import Optional, List, Literal

from pydantic import BaseModel, EmailStr, ConfigDict, Field


# ============================================================
# AUTH
# ============================================================
class LoginRequest(BaseModel):
    email: EmailStr
    mot_de_passe: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str  # administrateur | medecin


# ============================================================
# UTILISATEURS
# ============================================================
class UtilisateurOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nom: str
    prenom: str
    email: EmailStr
    date_creation: datetime
    est_actif: bool


class ProfilOut(UtilisateurOut):
    """Profil de l'utilisateur connecte (champs propres au role si applicables)."""
    type: str
    specialite: Optional[str] = None
    numero_ordre: Optional[str] = None
    niveau: Optional[str] = None


class ProfilUpdate(BaseModel):
    nom: Optional[str] = Field(default=None, min_length=1, max_length=120)
    prenom: Optional[str] = Field(default=None, min_length=1, max_length=120)
    specialite: Optional[str] = Field(default=None, min_length=1, max_length=120)


class ChangerMotDePasse(BaseModel):
    ancien_mot_de_passe: str
    nouveau_mot_de_passe: str = Field(min_length=8)


class AdministrateurCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    mot_de_passe: str
    niveau: Optional[str] = None


class MedecinCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    mot_de_passe: str
    specialite: str
    numero_ordre: str
    est_actif: bool = True


class MedecinOut(UtilisateurOut):
    specialite: Optional[str] = None
    numero_ordre: Optional[str] = None


# ============================================================
# DOSSIER PATIENT
# ============================================================
class DossierPatientCreate(BaseModel):
    prenom_enfant: str
    nom_enfant: str
    # Saisie naturelle pour un contexte pediatrique : "5 mois", "2 ans", "10
    # jours" — plutot qu'une date de naissance a calculer mentalement. Le
    # routeur convertit ca en date_naissance (stockee telle quelle pour
    # recalculer l'age exact a chaque analyse ECG future).
    age_valeur: Optional[int] = Field(default=None, ge=0)
    age_unite: Optional[Literal["jours", "mois", "annees"]] = None
    sexe: Optional[str] = None
    antecedents: Optional[str] = None
    allergies: Optional[str] = None
    groupe_sanguin: Optional[str] = None
    vaccinations: Optional[str] = None
    notes_complementaires: Optional[str] = None


class DossierPatientUpdate(BaseModel):
    prenom_enfant: Optional[str] = None
    nom_enfant: Optional[str] = None
    age_valeur: Optional[int] = Field(default=None, ge=0)
    age_unite: Optional[Literal["jours", "mois", "annees"]] = None
    sexe: Optional[str] = None
    antecedents: Optional[str] = None
    allergies: Optional[str] = None
    groupe_sanguin: Optional[str] = None
    vaccinations: Optional[str] = None
    notes_complementaires: Optional[str] = None


class DossierPatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date_creation: datetime
    prenom_enfant: str
    nom_enfant: str
    date_naissance: Optional[date] = None
    sexe: Optional[str] = None
    antecedents: Optional[str] = None
    allergies: Optional[str] = None
    groupe_sanguin: Optional[str] = None
    vaccinations: Optional[str] = None
    notes_complementaires: Optional[str] = None
    medecin_id: int


# ============================================================
# SOURCES (citations RAG)
# ============================================================
class SourceDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    extrait: str
    score_relevance: float
    document_id: int
    document_titre: Optional[str] = None  # titre lisible du document cite (affiche a la place de « Document #3 »)


class SourceCasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    extrait: str
    score_relevance: float
    cas_id: int


# ============================================================
# SESSION RAG + MESSAGES MEDECIN
# ============================================================
class SessionRAGCreate(BaseModel):
    titre: str
    dossier_patient_id: Optional[int] = None


class SessionRAGUpdate(BaseModel):
    titre: str = Field(min_length=1, max_length=255)


class SessionRAGOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titre: str
    date_session: datetime
    dossier_patient_id: Optional[int] = None
    medecin_id: int


class MessageMedecinOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: str
    reponse: Optional[str] = None
    date_message: datetime
    session_rag_id: int
    # champs specifiques aux sous-types (optionnels selon `type`)
    contenu: Optional[str] = None
    fichier_ecg: Optional[str] = None
    # metadonnees ECG extraites automatiquement (jamais saisies par le medecin)
    nb_derivations: Optional[int] = None
    frequence_hz: Optional[float] = None
    duree_secondes: Optional[float] = None
    age_jours: Optional[int] = None
    sexe: Optional[str] = None
    resultat_json: Optional[str] = None
    format_fichier: Optional[str] = None
    question: Optional[str] = None
    sources_document: List[SourceDocumentOut] = []
    sources_cas: List[SourceCasOut] = []


class MessageTexteCreate(BaseModel):
    contenu: str


# ============================================================
# BASE DE CONNAISSANCES
# ============================================================
class DocumentMedicalCreate(BaseModel):
    titre: str
    type_doc: Optional[str] = None


class DocumentMedicalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    titre: str
    type_doc: Optional[str] = None
    chemin_fichier: str
    vecteur_indexe: bool
    date_indexation: Optional[datetime] = None


class CasCliniqueCreate(BaseModel):
    symptomes: str
    diagnostic: Optional[str] = None
    age_patient: Optional[int] = None
    source: Optional[str] = None


class CasCliniqueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    symptomes: str
    diagnostic: Optional[str] = None
    age_patient: Optional[int] = None
    source: Optional[str] = None
    vecteur_indexe: bool


# ============================================================
# STATISTIQUES (vue medecin — son activite personnelle du mois)
# ============================================================
class StatistiquesMedecinOut(BaseModel):
    mois: str  # "YYYY-MM"
    dossiers_total: int             # nombre total de patients suivis (pas borne au mois)
    sessions_mois: int
    sessions_personnelles_mois: int
    messages_mois: int
    messages_par_type_mois: List["CompteurLabel"]


# ============================================================
# STATISTIQUES (vue administrateur)
# ============================================================
class CompteurLabel(BaseModel):
    label: str
    valeur: int


class EvolutionMois(BaseModel):
    mois: str                      # "2026-09"
    label: str                     # "Sept."
    nouveaux_dossiers: int
    nouvelles_sessions: int
    nouveaux_messages: int
    pertinence_moyenne: Optional[int] = None  # 0-100, None si aucune source citee ce mois-la


class ActiviteMedecin(BaseModel):
    id: int
    prenom: str
    nom: str
    specialite: str
    est_actif: bool
    dossiers: int
    sessions: int
    messages: int


class BaseConnaissancesStats(BaseModel):
    documents_total: int
    documents_indexes: int
    cas_total: int
    cas_indexes: int


class StatistiquesOut(BaseModel):
    mois: str  # "YYYY-MM" — periode a laquelle se referent les compteurs mensuels ci-dessous
    medecins_actifs: int
    medecins_inactifs: int
    dossiers: int
    sessions: int
    sessions_personnelles: int
    messages: int
    messages_par_type: List[CompteurLabel]
    dossiers_par_sexe: List[CompteurLabel]
    dossiers_par_tranche_age: List[CompteurLabel]
    base_connaissances: BaseConnaissancesStats
    evolution: List[EvolutionMois]
    activite_medecins: List[ActiviteMedecin]
