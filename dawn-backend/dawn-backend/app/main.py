from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine, ajouter_colonnes_manquantes
import time

from app.services import model_fetch, mesure_temps
from app.routers import auth, admin, medecin, sessions_rag, documents, cas_clinique

# Cree les tables si elles n'existent pas encore (pratique en dev).
# En production, prefere les migrations Alembic (voir alembic/ et README.md).
Base.metadata.create_all(bind=engine)
ajouter_colonnes_manquantes()  # ex. messages_ecg.resultat_json sur une base créée avant son ajout

@asynccontextmanager
async def lifespan(_app):
    # Récupère le modèle ECG (dépôt Hugging Face privé) en arrière-plan : l'API démarre tout de suite.
    if not model_fetch.demarrer_telechargement():  # déjà téléchargé (ou désactivé) : on précharge directement
        model_fetch.demarrer_prechauffage()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="DAWN API",
    description="Backend de l'assistant medical pediatrique DAWN, cote medecin — auth, dossiers "
                "patients, sessions RAG (texte/ECG), base de connaissances (documents et cas cliniques).",
    version="0.1.0",
)

@app.middleware("http")
async def mesurer_temps_de_reponse(request, call_next):
    """Enregistre la durée des analyses ECG et des questions texte (logs/temps_reponses.csv)."""
    type_requete = mesure_temps.type_de_requete(request.method, request.url.path) if settings.TEMPS_LOG_ACTIF else None
    if type_requete is None:
        return await call_next(request)
    debut = time.perf_counter()
    reponse = await call_next(request)
    mesure_temps.enregistrer(type_requete, reponse.status_code, time.perf_counter() - debut)
    return reponse


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(medecin.router)
app.include_router(sessions_rag.router)
app.include_router(documents.router)
app.include_router(cas_clinique.router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "service": "DAWN API"}


@app.get("/ecg/modele/statut", tags=["health"])
def statut_modele_ecg():
    """État du modèle ECG : pret | telechargement | erreur | absent | desactive."""
    return model_fetch.statut()


@app.post("/ecg/modele/reessayer", tags=["health"])
def reessayer_modele_ecg():
    model_fetch.reessayer()
    return model_fetch.statut()
