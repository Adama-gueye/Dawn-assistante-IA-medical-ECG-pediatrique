"""
Service RAG — porte depuis le prototype dawn-rag (Streamlit + FAISS + Ollama),
meme pipeline mais sur pgvector (Postgres) au lieu d'un index FAISS local :
un seul endroit pour les donnees + leurs embeddings, pas de fichier d'index a
recharger/synchroniser separement.

Pipeline :
  1. indexer_document()   : decoupe un .md (frontmatter + sections ##),
                             calcule l'embedding, stocke tout sur la ligne
                             DocumentMedical correspondante.
  2. repondre_avec_rag()  : recherche par similarite cosinus (pgvector),
                             construit le contexte, interroge Ollama.

Le modele d'embeddings (E5 multilingue) utilise le prefixage "query: "/
"passage: " — c'est une exigence du modele, pas un detail cosmetique (cf.
sa documentation), a conserver tel quel.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import List, Optional

import numpy as np
import frontmatter
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy.orm import Session

from app.config import settings
from app import models

SPECIAL_SECTIONS = {"Sources indicatives", "Utilisation par DAWN"}

SYSTEM_PROMPT = """Tu es DAWN, assistant d'aide à la décision en cardiologie pédiatrique. Ton interlocuteur est TOUJOURS un médecin : réponds-lui de confrère à confrère, de façon concise et clinique. Ne lui conseille jamais de « consulter un médecin » et ne rédige jamais comme pour un patient ou ses parents.

SOURCES — règle absolue :
- Tu t'appuies UNIQUEMENT sur les extraits de documentation ci-dessous (et sur le contexte du patient s'il est fourni). Aucune connaissance extérieure : ni valeur chiffrée, ni seuil, ni médicament, ni dose, ni diagnostic qui ne figure pas dans les extraits.
- Les extraits portent sur l'interprétation de l'ECG pédiatrique. Si la question porte sur autre chose (traitement, médicaments, posologie, conduite à tenir thérapeutique...) et que les extraits n'en parlent pas, dis-le explicitement (« Les documents DAWN ne couvrent pas ce point ») et n'improvise rien, même à titre indicatif.
- Si les extraits ne permettent pas de répondre, commence ta réponse par exactement [HORS_DOCUMENTS] puis explique en une ou deux phrases ce qui manque.
- Cite par leur titre les documents sur lesquels tu t'appuies.

ÂGE — règle pédiatrique :
- Les valeurs normales dépendent de l'âge : n'énonce jamais une valeur « normale » unique. Si l'âge du patient est connu (contexte patient ou question), donne la valeur de sa tranche d'âge telle qu'elle figure dans les extraits ; sinon, précise que la valeur dépend de l'âge et donne les repères par tranche d'âge des extraits.

ANALYSE ECG DE LA SESSION — règle absolue :
- Le bloc « Analyse ECG automatique » ci-dessous (s'il existe) est la SEULE source sur l'ECG de ce patient. Il donne des catégories AHA et des probabilités ; il ne mesure NI fréquence cardiaque, NI intervalle PR, NI durée QRS, NI QTc.
- N'attribue JAMAIS au patient une valeur mesurée (bpm, ms) : les tableaux des extraits sont des valeurs NORMALES DE RÉFÉRENCE par âge, pas des mesures de ce patient.
- Ne conclus pas « ECG normal » ou « pas de trouble » de ta propre initiative : rapporte ce que dit l'analyse (catégories, probabilités, incertitude, points d'attention), puis ce que les extraits disent de ces catégories.
- Une catégorie DÉTECTÉE est une anomalie signalée par le modèle, même avec une probabilité faible (chaque catégorie a son seuil : une probabilité de 23 % peut dépasser le seuil de 17 %). Ne dis JAMAIS qu'une catégorie détectée est absente, et ne qualifie pas une anomalie de « significative » : dis « signalée par le modèle ».
- Compare toujours la probabilité au seuil tel qu'il est écrit : probabilité supérieure ou égale au seuil = DÉTECTÉE. Ne dis jamais qu'une probabilité supérieure au seuil est « inférieure ». Cite les chiffres tels quels.
- Si plusieurs analyses ECG sont fournies, traite-les TOUTES, une par une dans l'ordre, et n'omets aucune catégorie détectée.
- Pour chaque catégorie détectée, dis en une ou deux phrases ce que les extraits en disent, sans ajouter de diagnostic, de fréquence ou de cause qui ne soit pas dans les extraits.
- « Fiabilité limitée » est la part de détections justes mesurée sur le jeu de test : ce n'est PAS la probabilité de ce patient. Ne confonds jamais ces deux nombres. Une catégorie INDÉTERMINÉE n'est pas détectée.
- Si le bloc indique qu'aucune analyse ECG n'a été effectuée et que la question porte sur « l'analyse » ou « l'ECG » du patient, réponds qu'aucune analyse ECG n'est disponible dans cette session.

SYMPTÔMES ET FORME DE LA RÉPONSE :
- Ce que le médecin décrit (ex. « le cœur bat très fort » à la palpation) est un signe clinique, PAS une mesure et PAS un constat d'ECG : n'en déduis ni fréquence cardiaque, ni rythme, ni résultat d'ECG. Dis ce que les extraits permettent de dire de ce signe et ce qui manque pour conclure (fréquence mesurée, ECG, contexte).
- Ne recopie jamais les extraits ni leurs en-têtes (« [Extrait 1] », titres, tableaux entiers) : reformule en quelques phrases.

STYLE :
- En français, en quelques paragraphes courts ou une liste brève. Pas d'introduction générale, pas de mise en garde standard.
- Respecte les « Instructions d'usage » de chaque extrait (ton, niveau de vigilance : ne pas alarmer inutilement, ou au contraire signaler la gravité).
- Si le contexte patient mentionne des allergies ou antécédents pertinents pour la question, signale-le brièvement.

{analyse_ecg}{contexte_patient}Extraits de documentation :
{context}
"""


# ============================================================
# EMBEDDINGS (modele charge une seule fois, reutilise)
# ============================================================
_embeddings: Optional[HuggingFaceEmbeddings] = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


# ============================================================
# INDEXATION — decoupe un .md et remplit la ligne DocumentMedical
# ============================================================
def _parse_markdown(chemin_fichier: str):
    """Reproduit le decoupage de dawn-rag/rag/documents.py, mais pour un
    seul fichier (un DocumentMedical = un fichier, pas un chunk — cf. le
    diagramme ou SourceDocument cite directement DocumentMedical)."""
    post = frontmatter.load(chemin_fichier)
    titre = post.get("titre", Path(chemin_fichier).stem)
    type_doc = post.get("type_doc", "")

    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("##", "section")])
    sections = splitter.split_text(post.content)

    usage_dawn = ""
    sources_indicatives = ""
    corps = []
    for doc in sections:
        section = doc.metadata.get("section", "Introduction")
        texte = doc.page_content.strip()
        if section == "Utilisation par DAWN":
            usage_dawn = texte
        elif section == "Sources indicatives":
            sources_indicatives = texte
        elif len(texte) >= 80:  # ignore les sections quasi-vides
            corps.append(f"## {section}\n{texte}")

    return titre, type_doc, "\n\n".join(corps), usage_dawn, sources_indicatives


def indexer_document(db: Session, document: "models.DocumentMedical") -> bool:
    """
    indexer() — lit `document.chemin_fichier`, decoupe le markdown, calcule
    l'embedding et met a jour la ligne en place (titre/type_doc inclus, au
    cas ou le frontmatter differe de ce qui avait ete saisi a l'upload).
    Ne fait PAS le commit (laisse au routeur, comme avant).
    """
    try:
        titre, type_doc, contenu, usage_dawn, sources_indicatives = _parse_markdown(document.chemin_fichier)
        if not contenu.strip():
            return False

        embeddings = get_embeddings()
        vecteur = embeddings.embed_query(f"passage: {titre}\n\n{contenu}")

        document.titre = titre
        document.type_doc = type_doc or document.type_doc
        document.contenu = contenu
        document.usage_dawn_instructions = usage_dawn
        document.sources_indicatives = sources_indicatives
        document.embedding = vecteur
        return True
    except Exception:
        return False


def indexer_cas_clinique(cas_id: int, texte: str) -> bool:
    """TODO: meme logique que indexer_document, une fois un corpus de cas cliniques fourni."""
    return False


# ============================================================
# GENERATION — recherche pgvector + appel Ollama
# ============================================================
@dataclass
class SourceDocumentResult:
    document_id: int
    extrait: str
    score_relevance: float


@dataclass
class SourceCasResult:
    cas_id: int
    extrait: str
    score_relevance: float


@dataclass
class RagResponse:
    reponse: str
    sources_document: List[SourceDocumentResult] = field(default_factory=list)
    sources_cas: List[SourceCasResult] = field(default_factory=list)


def _format_context(resultats: List[tuple]) -> str:
    blocks = []
    for i, (doc, _distance) in enumerate(resultats, start=1):
        block = f"[Extrait {i}] {doc.titre}\n{doc.contenu}"
        if doc.usage_dawn_instructions:
            block += f"\n(Instructions d'usage pour cette catégorie : {doc.usage_dawn_instructions})"
        blocks.append(block)
    return "\n\n---\n\n".join(blocks)


MARQUEUR_HORS_DOCUMENTS = "[HORS_DOCUMENTS]"

# Messages de politesse : pas de recherche documentaire, pas d'appel au modele, pas de sources
# (avant : un simple « bonjour » faisait afficher 4 documents comme « sources citees »).
_POLITESSE_MOTS = {
    "bonjour", "bonsoir", "salut", "hello", "coucou", "hey", "merci", "ok", "okay", "dac", "daccord",
    "parfait", "super", "bien", "bravo", "top", "cava", "ca", "va", "au", "revoir", "a", "bientot",
    "bonne", "journee", "soiree", "docteur", "dr", "dawn", "beaucoup", "tres",
}


def _mots_normalises(texte: str) -> List[str]:
    sans_accents = "".join(
        c for c in unicodedata.normalize("NFD", texte.lower()) if unicodedata.category(c) != "Mn"
    )
    return re.findall(r"[a-z0-9]+", sans_accents)


def est_small_talk(texte: str) -> bool:
    """Vrai si le message n'est QUE de la politesse (aucun mot hors de la liste ci-dessus)."""
    mots = _mots_normalises(texte)
    return 0 < len(mots) <= 6 and all(m in _POLITESSE_MOTS for m in mots)


def _reponse_small_talk(texte: str) -> str:
    mots = set(_mots_normalises(texte))
    if mots & {"merci", "bravo", "top", "parfait", "super"}:
        return "Avec plaisir, docteur. N'hésitez pas si vous avez une autre question."
    if mots & {"revoir", "bientot"}:
        return "Bonne continuation, docteur."
    return (
        "Bonjour docteur. Posez-moi votre question sur l'interprétation de l'ECG pédiatrique : "
        "repères normaux par âge, troubles du rythme ou de la conduction, anomalies de repolarisation..."
    )


def _age_lisible(jours: int) -> str:
    jours = max(jours, 0)
    if jours < 60:
        return f"{jours} jour{'s' if jours > 1 else ''}"
    if jours < 730:
        return f"{round(jours / 30.44)} mois"
    return f"{round(jours / 365.25)} ans"


def _court(texte: str, max_len: int = 300) -> str:
    texte = " ".join(texte.split())
    return texte if len(texte) <= max_len else texte[:max_len].rstrip() + "…"


def _contexte_patient(db: Session, dossier_patient_id: Optional[int]) -> str:
    """Age, sexe, antecedents et allergies du dossier (jamais le nom du patient)."""
    if dossier_patient_id is None:
        return ""
    dossier = db.query(models.DossierPatient).filter(models.DossierPatient.id == dossier_patient_id).first()
    if dossier is None:
        return ""
    sexe = {"M": "garçon", "F": "fille"}.get(dossier.sexe or "", "patient")
    elements = []
    if dossier.date_naissance:
        elements.append(f"{sexe} de {_age_lisible((date.today() - dossier.date_naissance).days)}")
    elif dossier.sexe:
        elements.append(sexe)
    if dossier.antecedents and dossier.antecedents.strip():
        elements.append(f"antécédents : {_court(dossier.antecedents)}")
    if dossier.allergies and dossier.allergies.strip():
        elements.append(f"allergies : {_court(dossier.allergies)}")
    if not elements:
        return ""
    return (
        "Contexte du patient (dossier) : " + " ; ".join(elements) + ".\n"
        "Utilise ce contexte pour adapter ta réponse (valeurs normales à son âge, allergies ou antécédents pertinents).\n\n"
    )


def _bloc_analyse_ecg(analyse_ecg: Optional[str]) -> str:
    """Dernière analyse ECG de la session (texte déjà affiché au médecin), ou mention explicite qu'il n'y en a pas."""
    if not analyse_ecg or not analyse_ecg.strip():
        return "Analyse ECG automatique : aucune analyse ECG n'a été effectuée dans cette session.\n\n"
    return "Analyse ECG automatique (la plus récente de cette session) :\n" + analyse_ecg.strip() + "\n\n"


def _selectionner_contexte(resultats: List[tuple], max_chars: int) -> List[tuple]:
    """Garde les documents les mieux classes tant qu'ils tiennent dans le budget de contexte
    (toujours au moins le premier). Seuls ces documents sont ensuite cites comme sources."""
    retenus, total = [], 0
    for doc, score in resultats:
        taille = len(doc.titre) + len(doc.contenu or "") + len(doc.usage_dawn_instructions or "") + 120
        if retenus and total + taille > max_chars:
            break
        retenus.append((doc, score))
        total += taille
    return retenus


def repondre_avec_rag(db: Session, question: str, dossier_patient_id: int | None = None,
                      analyse_ecg: Optional[str] = None) -> RagResponse:
    """
    Recherche par similarite cosinus dans les DocumentMedical deja indexes,
    puis genere la reponse avec Ollama a partir du contexte trouve.
    Si la session est liee a un dossier patient, son age/sexe/antecedents/allergies
    sont injectes dans le prompt (pas son nom).
    """
    if est_small_talk(question):
        return RagResponse(reponse=_reponse_small_talk(question))

    embeddings = get_embeddings()
    vecteur_question = embeddings.embed_query(f"query: {question}")

    lignes = (
        db.query(models.DocumentMedical)
        .filter(models.DocumentMedical.vecteur_indexe.is_(True))
        .order_by(models.DocumentMedical.embedding.cosine_distance(vecteur_question))
        .limit(settings.RAG_TOP_K)
        .all()
    )

    if not lignes:
        return RagResponse(
            reponse=(
                "Aucun document n'est encore indexé dans la base de connaissances — "
                "impossible de répondre à partir de sources vérifiées pour l'instant."
            )
        )

    # recalcule les scores affiches (la requete ne les renvoie pas directement) :
    # embeddings normalises => le produit scalaire EST la similarite cosinus.
    resultats = []
    for doc in lignes:
        score = float(np.dot(doc.embedding, vecteur_question)) if doc.embedding is not None else 0.0
        resultats.append((doc, score))
    resultats = _selectionner_contexte(resultats, settings.RAG_MAX_CONTEXT_CHARS)

    llm = ChatOllama(
        model=settings.OLLAMA_MODEL, temperature=0.1,
        base_url=settings.OLLAMA_BASE_URL, num_ctx=settings.OLLAMA_NUM_CTX,
    )
    prompt = ChatPromptTemplate.from_messages([("system", SYSTEM_PROMPT), ("user", "{question}")])
    chain = prompt | llm | StrOutputParser()
    reponse = chain.invoke({
        "context": _format_context(resultats),
        "analyse_ecg": _bloc_analyse_ecg(analyse_ecg),
        "contexte_patient": _contexte_patient(db, dossier_patient_id),
        "question": question,
    })

    # Le modele signale que les documents ne couvrent pas la question : on n'affiche pas de sources.
    if MARQUEUR_HORS_DOCUMENTS in reponse or "ne couvrent pas ce point" in reponse.strip().lower()[:160]:
        return RagResponse(reponse=reponse.replace(MARQUEUR_HORS_DOCUMENTS, "").strip())

    sources_document = [
        SourceDocumentResult(document_id=doc.id, extrait=doc.contenu[:300], score_relevance=score)
        for doc, score in resultats
    ]
    return RagResponse(reponse=reponse, sources_document=sources_document)

# ============================================================
# TITRES DE SESSION — titre court decrivant le sujet de la 1re question
# ============================================================
TITRE_SYSTEM_PROMPT = (
    "Tu génères des titres de conversation. Réponds UNIQUEMENT par un titre de "
    "3 à 6 mots, en français, qui décrit le sujet de la question de l'utilisateur. "
    "Pas de guillemets, pas de point final, pas d'explication."
)


def _titre_de_repli(texte: str, max_len: int = 50) -> str:
    """Debut de la question, coupe proprement : sert si Ollama est indisponible."""
    texte = " ".join(texte.split())
    if len(texte) <= max_len:
        return texte[:1].upper() + texte[1:]
    coupe = texte[:max_len].rsplit(" ", 1)[0]
    return coupe[:1].upper() + coupe[1:] + "…"


def generer_titre(texte: str) -> str:
    """
    Titre de session adapte au sujet (comme le nom d'une conversation), genere
    par le LLM local avec une sortie tres courte. Ne leve jamais d'exception :
    en cas de probleme (Ollama arrete, sortie vide), renvoie le debut de la question.
    """
    repli = _titre_de_repli(texte)
    try:
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL, temperature=0.2,
            base_url=settings.OLLAMA_BASE_URL, num_ctx=settings.OLLAMA_NUM_CTX, num_predict=24,
        )
        prompt = ChatPromptTemplate.from_messages([("system", TITRE_SYSTEM_PROMPT), ("user", "{texte}")])
        brut = (prompt | llm | StrOutputParser()).invoke({"texte": texte})
        titre = brut.strip().splitlines()[0].strip().strip("\"'“”«» ").rstrip(".").strip() if brut.strip() else ""
        return titre[:80] if len(titre) >= 3 else repli
    except Exception:
        return repli