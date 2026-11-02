"""
Modeles SQLAlchemy, traduits directement du diagramme de classe DAWN.

Strategie d'heritage : "joined table inheritance" (une table par sous-classe,
liee a la table parente par une FK sur la cle primaire). C'est le choix le
plus proche semantiquement d'un diagramme UML avec heritage, et ca reste
interrogeable simplement (SQLAlchemy fait la jointure automatiquement).

Deux hierarchies concernees :
  - Utilisateur -> Administrateur / Medecin
  - MessageMedecin -> MessageTexte / MessageECG

Le systeme est recentre sur l'usage Medecin : il n'y a plus de compte
Patient ni de portail cote patient (SessionPatient/MessagePatient/
ResumeClinique/NotificationEmail ont disparu). DossierPatient porte
desormais directement les informations demographiques du patient
(dateNaissance, sexe) puisque ce n'est plus un Utilisateur.
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text, Float, ForeignKey
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


# ============================================================
# UTILISATEUR (abstrait) -> Administrateur / Medecin
# ============================================================
class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True)
    nom = Column(String(120), nullable=False)
    prenom = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    mot_de_passe = Column(String(255), nullable=False)  # hash bcrypt, jamais en clair
    date_creation = Column(DateTime, default=datetime.utcnow, nullable=False)
    est_actif = Column(Boolean, default=True, nullable=False)

    type = Column(String(50))  # discriminant d'heritage

    __mapper_args__ = {"polymorphic_identity": "utilisateur", "polymorphic_on": type}

    def __repr__(self):
        return f"<Utilisateur id={self.id} email={self.email}>"


class Administrateur(Utilisateur):
    __tablename__ = "administrateurs"

    id = Column(Integer, ForeignKey("utilisateurs.id"), primary_key=True)
    niveau = Column(String(50))

    __mapper_args__ = {"polymorphic_identity": "administrateur"}


class Medecin(Utilisateur):
    __tablename__ = "medecins"

    id = Column(Integer, ForeignKey("utilisateurs.id"), primary_key=True)
    specialite = Column(String(120))
    numero_ordre = Column(String(50))

    __mapper_args__ = {"polymorphic_identity": "medecin"}

    dossiers = relationship("DossierPatient", back_populates="medecin")
    sessions_rag = relationship("SessionRAG", back_populates="medecin")


# ============================================================
# DOSSIER PATIENT (cree par un Medecin ; porte directement les
# informations demographiques du patient, qui n'est plus un Utilisateur)
# ============================================================
class DossierPatient(Base):
    __tablename__ = "dossiers_patient"

    id = Column(Integer, primary_key=True)
    date_creation = Column(DateTime, default=datetime.utcnow, nullable=False)
    # NB: absents du diagramme de classe (le patient n'est plus un Utilisateur),
    # mais indispensables pour identifier le dossier dans l'UI medecin.
    prenom_enfant = Column(String(120), nullable=False)
    nom_enfant = Column(String(120), nullable=False)
    date_naissance = Column(Date)
    sexe = Column(String(10))
    antecedents = Column(Text)
    allergies = Column(Text)
    groupe_sanguin = Column(String(10))
    vaccinations = Column(Text)
    notes_complementaires = Column(Text)

    medecin_id = Column(Integer, ForeignKey("medecins.id"), nullable=False)

    medecin = relationship("Medecin", back_populates="dossiers")
    sessions_rag = relationship("SessionRAG", back_populates="dossier")


# ============================================================
# SESSION RAG (cote medecin) + MESSAGES (heritage)
# ============================================================
class SessionRAG(Base):
    __tablename__ = "sessions_rag"

    id = Column(Integer, primary_key=True)
    date_session = Column(DateTime, default=datetime.utcnow, nullable=False)
    titre = Column(String(255), nullable=False)

    dossier_patient_id = Column(Integer, ForeignKey("dossiers_patient.id"), nullable=True)
    medecin_id = Column(Integer, ForeignKey("medecins.id"), nullable=False)

    dossier = relationship("DossierPatient", back_populates="sessions_rag")
    medecin = relationship("Medecin", back_populates="sessions_rag")
    messages = relationship(
        "MessageMedecin", back_populates="session",
        order_by="MessageMedecin.date_message", cascade="all, delete-orphan",
    )


class MessageMedecin(Base):
    __tablename__ = "messages_medecin"

    id = Column(Integer, primary_key=True)
    reponse = Column(Text)
    date_message = Column(DateTime, default=datetime.utcnow, nullable=False)

    session_rag_id = Column(Integer, ForeignKey("sessions_rag.id"), nullable=False)
    type = Column(String(50))

    # with_polymorphic="*" : charge texte/ECG dans UNE requête (sinon une requête supplémentaire par message)
    __mapper_args__ = {"polymorphic_identity": "message_medecin", "polymorphic_on": type, "with_polymorphic": "*"}

    session = relationship("SessionRAG", back_populates="messages")
    sources_document = relationship(
        "SourceDocument", back_populates="message", cascade="all, delete-orphan"
    )
    sources_cas = relationship(
        "SourceCas", back_populates="message", cascade="all, delete-orphan"
    )


class MessageTexte(MessageMedecin):
    __tablename__ = "messages_texte"

    id = Column(Integer, ForeignKey("messages_medecin.id"), primary_key=True)
    contenu = Column(Text, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "texte"}


class MessageECG(MessageMedecin):
    __tablename__ = "messages_ecg"

    id = Column(Integer, ForeignKey("messages_medecin.id"), primary_key=True)
    fichier_ecg = Column(String(500), nullable=False)      # chemin du .hea
    fichier_ecg_dat = Column(String(500), nullable=False)  # chemin du .dat associe (meme nom de base)
    format_fichier = Column(String(50), default="wfdb")
    question = Column(Text)

    # Extraits automatiquement (jamais saisis par le medecin) :
    # - nb_derivations / frequence_hz / duree_secondes : lus depuis le header WFDB (record.hea)
    # - age_jours / sexe : lus depuis le DossierPatient lie a la session, au moment de l'analyse
    #   (photo de l'age au jour J, pour tracabilite — pas une resaisie)
    nb_derivations = Column(Integer)
    frequence_hz = Column(Float)
    duree_secondes = Column(Float)
    age_jours = Column(Integer)
    sexe = Column(String(10))
    # Resultat structure du modele (categories, probabilites brutes/calibrees, statut conforme...) : trace exacte de ce qui a ete calcule
    resultat_json = Column(Text)

    __mapper_args__ = {"polymorphic_identity": "ecg"}


# ============================================================
# BASE DE CONNAISSANCES RAG : DocumentMedical + CasClinique
# ============================================================
class DocumentMedical(Base):
    __tablename__ = "documents_medicaux"

    id = Column(Integer, primary_key=True)
    titre = Column(String(255), nullable=False)
    type_doc = Column(String(100))  # guideline, article, protocole...
    chemin_fichier = Column(String(500), nullable=False)
    vecteur_indexe = Column(Boolean, default=False, nullable=False)
    date_indexation = Column(DateTime)

    # Absents du diagramme (DocumentMedical n'y a qu'une reference de fichier),
    # mais necessaires pour que le document soit reellement cherchable : le
    # diagramme fait de DocumentMedical l'unite citee par SourceDocument, donc
    # c'est ici que vivent le texte et son embedding (pas de table "chunk"
    # separee, pour rester fidele a cette relation du diagramme).
    contenu = Column(Text)                     # texte indexe (sections cliniques du markdown)
    usage_dawn_instructions = Column(Text)      # consignes de ton/vigilance a injecter dans le prompt
    sources_indicatives = Column(Text)          # references bibliographiques (affichage seulement)
    embedding = Column(Vector(768))             # intfloat/multilingual-e5-base = 768 dimensions

    sources = relationship("SourceDocument", back_populates="document")


class CasClinique(Base):
    __tablename__ = "cas_cliniques"

    id = Column(Integer, primary_key=True)
    symptomes = Column(Text, nullable=False)
    diagnostic = Column(Text)
    age_patient = Column(Integer)
    source = Column(String(255))  # origine du cas (dataset, publication...)
    vecteur_indexe = Column(Boolean, default=False, nullable=False)

    sources_cas = relationship("SourceCas", back_populates="cas")


# ============================================================
# CITATIONS RAG (jointures message <-> connaissance, avec score)
# ============================================================
class SourceDocument(Base):
    """Citation d'un DocumentMedical dans la reponse a un MessageMedecin."""
    __tablename__ = "sources_document"

    id = Column(Integer, primary_key=True)
    extrait = Column(Text, nullable=False)
    score_relevance = Column(Float, nullable=False)

    message_id = Column(Integer, ForeignKey("messages_medecin.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents_medicaux.id"), nullable=False)

    message = relationship("MessageMedecin", back_populates="sources_document")
    document = relationship("DocumentMedical", back_populates="sources")

    @property
    def document_titre(self):
        return self.document.titre if self.document is not None else None


class SourceCas(Base):
    """Citation d'un CasClinique dans la reponse a un MessageMedecin (cote medecin)."""
    __tablename__ = "sources_cas"

    id = Column(Integer, primary_key=True)
    extrait = Column(Text, nullable=False)
    score_relevance = Column(Float, nullable=False)

    message_id = Column(Integer, ForeignKey("messages_medecin.id"), nullable=False)
    cas_id = Column(Integer, ForeignKey("cas_cliniques.id"), nullable=False)

    message = relationship("MessageMedecin", back_populates="sources_cas")
    cas = relationship("CasClinique", back_populates="sources_cas")

