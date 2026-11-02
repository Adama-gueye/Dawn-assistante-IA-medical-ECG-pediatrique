from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg2://dawn_user:dawn_password@localhost:5432/dawn_db"
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    CORS_ORIGINS: str = "http://localhost:3000"

    # RAG (voir app/services/rag_service.py) — porte de dawn-rag (Streamlit/FAISS)
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    # Fenetre de contexte envoyee a Ollama. Les documents DAWN font ~4-5 Ko chacun : sans valeur
    # explicite, Ollama peut utiliser une fenetre trop petite et tronquer le prompt (consignes comprises).
    OLLAMA_NUM_CTX: int = 8192
    # Taille max (caracteres) des extraits injectes dans le prompt ; ~16000 car. = ~5000 tokens,
    # ce qui laisse de la place au prompt systeme et a la reponse dans 8192 tokens.
    RAG_MAX_CONTEXT_CHARS: int = 16000
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-base"
    RAG_TOP_K: int = 4

    # Modele ECG DAWN (voir app/services/ecg_service.py et app/ml/). Chemins relatifs = relatifs a la racine du backend.
    ECG_MODEL_PATH: str = "models/dawn_ecg_model_final.pt"
    ECG_HUBERT_DIR: str = "models/hubert-ecg-small"       # config.json + code HF (scripts/telecharger_hubert.py)
    ECG_MODELES: str = "all"                              # « all », un nombre N, ou « ASL:42,CB:1337 »
    ECG_DEVICE: str = "cpu"
    ECG_THREADS: int = 0                                  # 0 = reglage par defaut de torch
    ECG_TORCH_WEIGHTS_ONLY: bool = True                   # laisser True ; false seulement si torch refuse de lire le .pt
    # Récupération automatique depuis Hugging Face (dépôt privé). HF_TOKEN : jeton en LECTURE SEULE, uniquement dans .env (non versionné).
    HF_TOKEN: str = ""
    ECG_AUTO_DOWNLOAD: bool = True
    ECG_HF_REPO: str = "adama9900/dawn-ecg-pediatrique"
    ECG_HF_FILENAME: str = "dawn_ecg_model_final.pt"
    ECG_HF_CALIBRATION_FILENAME: str = "calibration_artifacts.json"  # calibration/seuils/conforme, récupérée dans le même dépôt
    ECG_CALIBRATION_PATH: str = "models/calibration_artifacts.json"  # copie locale du fichier téléchargé (sinon : copie livrée dans app/ml/artifacts/)
    ECG_HF_REVISION: str = ""                             # hash de commit à figer (recommandé pour la soutenance) ; vide = dernière version
    ECG_HUBERT_REVISION: str = ""                         # idem pour le code HuBERT-ECG public
    ECG_PRECHARGER: bool = True                           # charge le modèle ECG + les embeddings au démarrage (1re requête rapide)
    TEMPS_LOG_ACTIF: bool = True                          # enregistre la durée de chaque analyse ECG / question texte (voir scripts/resume_temps.py)
    TEMPS_LOG_PATH: str = "logs/temps_reponses.csv"
    ECG_AGE_MAX_ANS: float = 18.0                         # au-dela : analyse refusee (modele entraine sur 0-15 ans)

    @property
    def cors_origins_list(self):
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
