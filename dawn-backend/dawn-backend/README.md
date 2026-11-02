# DAWN — Backend (FastAPI · PostgreSQL + pgvector · Ollama)

API de l'assistant médical DAWN (cardiologie pédiatrique), destinée aux **médecins**.
Entités issues du diagramme de classe : `Utilisateur` → `Administrateur` / `Medecin`,
`DossierPatient`, `SessionRAG`, `MessageMedecin` → `MessageTexte` / `MessageECG`,
`DocumentMedical`, `CasClinique`, `SourceDocument`, `SourceCas`.

Pas de portail patient : l'administrateur crée les comptes médecins, le médecin crée
les dossiers de ses patients.

## Lancer au quotidien

```powershell
docker start dawn-postgres          # la base (nom du conteneur : adapter)
venv\Scripts\activate               # Linux/macOS : source venv/bin/activate
uvicorn app.main:app --reload
```

API : http://localhost:8000 — documentation interactive (Swagger) : http://localhost:8000/docs
Ollama doit tourner en parallèle (`ollama list` pour vérifier que le modèle est présent).

## Première installation

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env              # puis éditer .env
```

**1. PostgreSQL avec l'extension pgvector** (exemple Docker — adapter noms et mot de passe,
et mettre les mêmes valeurs dans `DATABASE_URL`) :

```powershell
docker run -d --name dawn-postgres -e POSTGRES_USER=<user> -e POSTGRES_PASSWORD=<mot_de_passe> -e POSTGRES_DB=dawn_db -p 5432:5432 pgvector/pgvector:pg16
docker exec -it dawn-postgres psql -U <user> -d dawn_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

L'extension doit exister **avant** le premier démarrage de l'API (la colonne `embedding` en dépend).
Les tables sont créées automatiquement au démarrage.

**2. Premier administrateur, puis base de connaissances :**

```powershell
python seed_admin.py                # crée le compte administrateur
ollama pull qwen2.5:3b              # ou le modèle choisi dans OLLAMA_MODEL
python seed_documents.py            # importe et indexe data/docs/*.md (embeddings → pgvector)
```

`seed_documents.py` peut être relancé : il met à jour les documents déjà présents.
Au tout premier calcul, le modèle d'embeddings est téléchargé (connexion internet nécessaire).

## Variables d'environnement (`.env`)

| Variable | Rôle | Défaut |
|---|---|---|
| `DATABASE_URL` | Connexion PostgreSQL | voir `.env.example` |
| `SECRET_KEY` | Signature des jetons JWT — **à changer** | `change-me` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de connexion | `480` |
| `CORS_ORIGINS` | Origines autorisées (front) | `http://localhost:3000` |
| `OLLAMA_BASE_URL` | Adresse d'Ollama | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Modèle de génération | `qwen2.5:3b` |
| `OLLAMA_NUM_CTX` | Fenêtre de contexte envoyée à Ollama | `8192` |
| `EMBEDDING_MODEL` | Modèle d'embeddings (E5 multilingue, 768 dim.) | `intfloat/multilingual-e5-base` |
| `RAG_TOP_K` | Documents récupérés par question | `4` |
| `RAG_MAX_CONTEXT_CHARS` | Taille max des extraits injectés dans le prompt | `16000` |
| `ECG_MODEL_PATH` | Fichier du modèle ECG | `models/dawn_ecg_model_final.pt` |
| `ECG_HUBERT_DIR` | Config + code HuBERT-ECG | `models/hubert-ecg-small` |
| `HF_TOKEN` | Jeton Hugging Face (lecture seule) pour le dépôt privé — dans `.env` uniquement | vide |
| `ECG_AUTO_DOWNLOAD` / `ECG_HF_REPO` / `ECG_HF_FILENAME` / `ECG_HF_REVISION` | Téléchargement auto du modèle depuis Hugging Face | `true` / `adama9900/dawn-ecg-pediatrique` / `dawn_ecg_model_final.pt` / dernière |
| `ECG_MODELES` | `all`, un nombre N, ou `ASL:42,CB:1337` (la calibration est établie pour l'ensemble complet) | `all` |
| `ECG_DEVICE` / `ECG_THREADS` | Calcul (`cpu`/`cuda`) et nombre de threads (0 = défaut) | `cpu` / `0` |
| `ECG_AGE_MAX_ANS` | Âge au-delà duquel l'analyse est refusée | `18` |

## Principales routes

| Préfixe | Routes |
|---|---|
| `/auth` | `POST /login` · `GET`/`PATCH /me` · `POST /changer-mot-de-passe` |
| `/admin` | `POST`/`GET /medecins` · `GET /utilisateurs` · `PATCH /utilisateurs/{id}/statut` · `GET /statistiques?mois=YYYY-MM` |
| `/medecin` | `POST`/`GET /dossiers` · `GET`/`PATCH`/`DELETE /dossiers/{id}` · `GET /statistiques?mois=YYYY-MM` |
| `/medecin/sessions` | `POST`/`GET` · `PATCH`/`DELETE /{id}` · `GET /{id}/messages` · `POST /{id}/messages/texte` · `/ecg` (paire .hea + .dat) · `/ecg-csv` (outil de test) |
| `/documents`, `/cas-cliniques` | `POST`/`GET` · `POST /{id}/indexer` |

## Fonctionnement du RAG

1. `seed_documents.py` / `POST /documents/{id}/indexer` : lecture du Markdown (front-matter + sections `##`),
   embedding E5 (préfixe `passage:`), stockage dans `documents_medicaux.embedding` (pgvector).
2. À chaque question : embedding (`query:`) → recherche par similarité cosinus → extraits dans le prompt
   (dans la limite de `RAG_MAX_CONTEXT_CHARS`) → réponse Ollama. Seuls les documents réellement transmis au modèle
   sont affichés comme sources.
3. Dans une session liée à un patient, son âge, son sexe, ses antécédents et ses allergies sont ajoutés au prompt
   (jamais son nom).
4. Le prompt impose de répondre uniquement à partir des extraits. Si la question sort du corpus, le modèle doit
   le dire (marqueur `[HORS_DOCUMENTS]` → aucune source affichée).

**Le corpus actuel (`data/docs`) ne couvre que l'interprétation de l'ECG pédiatrique, pas la thérapeutique.**

## Modèle ECG (DAWN-ECG)

Ensemble de 6 modèles **HuBERT-ECG** affinés (notebook DAWN V6), 12 catégories AHA (A, C à M) en multi-label, avec âge et sexe
en entrée. Format accepté : **WFDB** (paire `.hea` + `.dat`), celui du jeu de données d'entraînement. Nombre de dérivations,
fréquence et durée sont lus dans l'en-tête ; l'âge et le sexe viennent du dossier patient — **ils sont obligatoires** dans une
session personnelle (sans dossier), et une analyse est refusée au-delà de 18 ans (modèle entraîné sur 0–15 ans).
`POST .../messages/ecg-csv` convertit un CSV en WFDB pour tester sans vrais fichiers (usage test uniquement).

**Installation — automatique** : le modèle (~730 Mo) est récupéré par l'API elle-même depuis le dépôt Hugging Face privé, plus de script à lancer.
Dans `.env` (non versionné) :

```
HF_TOKEN=hf_...                 # jeton « fine-grained » en LECTURE SEULE limité au dépôt
ECG_HF_REPO=adama9900/dawn-ecg-pediatrique
# ECG_HF_REVISION=<hash>        # optionnel : figer la version du modèle (soutenance / reproductibilité)
```

Au démarrage, `uvicorn` lance le téléchargement en arrière-plan (poids privés + code/config HuBERT-ECG public) ; il n'a lieu qu'une fois.
La **calibration** (Platt, seuils, quantiles conformes : `calibration_artifacts.json`, quelques Ko) est lue dans le **même dépôt Hugging Face** :
tout ce qui définit le modèle vient donc d'un seul endroit versionné. Pour la publier, déposer sur la page du dépôt
(Files and versions → Add file → Upload files) le fichier `app/ml/artifacts/calibration_artifacts.json`. Si ce fichier est absent du dépôt
ou inutilisable, le backend utilise la copie livrée dans `app/ml/artifacts/` et le signale dans les journaux ; la source réellement
utilisée (`hugging_face` ou `locale`) est enregistrée dans le résultat de chaque analyse (`source_calibration`).
Le modèle ECG et le modèle d'embeddings sont ensuite chargés en mémoire dès le démarrage (`ECG_PRECHARGER=true`), pour que la 1re requête ne soit pas lente.
Pendant le téléchargement, une analyse ECG répond 503 « en cours de téléchargement ». Suivi : `GET /ecg/modele/statut`
(`pret` · `telechargement` · `erreur` · `absent` · `desactive`), relance après une erreur : `POST /ecg/modele/reessayer`.
`ECG_AUTO_DOWNLOAD=false` désactive tout cela (retour au mode manuel avec `scripts/telecharger_modele.py` + `scripts/telecharger_hubert.py`).

```powershell
pip install -r requirements.txt
python scripts/test_parite.py --hea <enregistrement_sans_extension> --age-annees 7 --sexe F   # essai + temps de calcul
```

Si `ECG_AUTO_DOWNLOAD=false` et que `models/dawn_ecg_model_final.pt` / `models/hubert-ecg-small/` sont absents, l'analyse ECG renvoie une **réponse simulée**
explicitement signalée. Si le modèle est installé mais ne se charge pas, l'API répond 503 avec la cause.

**Chaîne d'inférence** : WFDB → prétraitement identique au notebook (500 Hz, retrait de ligne de base, normalisation, 5 fenêtres de
10 s) → 6 modèles → calibration de Platt par catégorie → seuils → prédiction conforme (α = 0,10).
Les paramètres de calibration (dépôt Hugging Face, copie de secours dans `app/ml/artifacts/calibration_artifacts.json`) sont reconstruits depuis les prédictions de
validation et **vérifiés chiffre à chiffre** contre les fichiers du notebook (`verification_calibration.txt`,
`scripts/reproduire_calibration.py`). Le résultat structuré de chaque analyse est conservé dans `messages_ecg.resultat_json`.

**Vérifier la fidélité au notebook** : exécuter `scripts/cellule_kaggle_export_parite.py` en fin de notebook (session ouverte),
télécharger `parite_backend.zip`, puis `python scripts/test_parite.py --dossier <dossier décompressé>`.

**Lecture du résultat** : « détection nette » = la prédiction conforme (90 %) ne laisse qu'une étiquette ; ce n'est **pas** une
garantie de justesse pour cet ECG. L'incertitude globale (faible / moyenne / élevée) est l'entropie moyenne des 12 catégories,
découpée en tertiles sur le jeu de test.

**Limites** (à reprendre dans le mémoire) : prototype de recherche, **non validé cliniquement** ; un seul jeu de données, un seul
centre ; catégories rares G et M non validables ; précision de M ≈ 5 % ; performances plus faibles chez les nourrissons et à
9 dérivations ; l'âge et le sexe n'améliorent pas de façon mesurable le signal seul (ablation). Licence : dérive de HuBERT-ECG
(CC BY-NC) → usage non commercial.

## Suppression

Supprimer une session efface ses messages, leurs sources et les fichiers ECG du disque. Supprimer un dossier
patient supprime aussi toutes ses sessions. **Suppression définitive** : un déploiement réel préférerait un
archivage (obligations de conservation du dossier médical).

## Limites connues / à faire

- Analyse ECG : fidélité au notebook vérifiée pour le prétraitement et la calibration ; l'inférence du modèle lui-même
  doit être validée chez toi avec `scripts/test_parite.py` (nécessite les poids).
- Temps de calcul sur CPU : 6 modèles × 5 fenêtres × 2 moitiés ; à mesurer (`ECG_MODELES=1` pour réduire).
- `rag_service.indexer_cas_clinique` : non implémenté (pas encore de corpus de cas cliniques).
- Les colonnes manquantes (nullables) sont ajoutées automatiquement au démarrage (`ajouter_colonnes_manquantes`, ex. `messages_ecg.resultat_json`).
- `create_all()` ne modifie pas une table existante : après un changement de modèle, soit repartir d'une base
  vide, soit `ALTER TABLE`, soit passer par Alembic (`alembic revision --autogenerate`, `alembic upgrade head`).

## Structure

```
app/
  main.py  config.py  database.py  deps.py  security.py  models.py  schemas.py
  routers/   auth · admin · medecin · sessions_rag · documents · cas_clinique
  services/  rag_service · ecg_service · wfdb_service · session_cleanup
  ml/        preprocessing · calibration · bundle · hubert_ensemble · categories · artifacts/
data/docs/   documents de référence indexés (Markdown)
scripts/     telecharger_modele · telecharger_hubert · test_parite · cellule_kaggle_export_parite · reproduire_calibration
models/      modèle et code HuBERT (non versionnés)
seed_admin.py  seed_documents.py
```

## Mesure des temps de réponse

Chaque analyse ECG et chaque question texte est chronométrée côté serveur et ajoutée à `logs/temps_reponses.csv` (non versionné ;
`TEMPS_LOG_ACTIF=false` pour désactiver). Résumé (n, min, médiane, moyenne, p90, max, configuration de la machine) :
`python scripts/resume_temps.py`. La durée va de la réception de la requête à l'envoi de la réponse, hors réseau et affichage.
