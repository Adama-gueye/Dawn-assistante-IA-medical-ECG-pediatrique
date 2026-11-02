# DAWN — Assistant IA médical pour l'ECG pédiatrique

**DAWN** (*Diagnostic Assistance With Neural Networks*) est un système intelligent multimodal d'aide à l'analyse des anomalies électrocardiographiques pédiatriques. Il combine le **signal ECG** (12 dérivations) et des **données cliniques** (âge, sexe) pour proposer une classification multilabel sur **12 catégories AHA**, et met à disposition du médecin un **assistant documentaire (RAG)** fondé sur des documents de référence.

Projet réalisé dans le cadre d'un mémoire de Master 2 Data Science & Intelligence Artificielle (ISI, Sénégal, 2025–2026).

> ⚠️ **Avertissement.** DAWN est un prototype de recherche. C'est un outil d'aide à l'analyse : il ne remplace ni le jugement du professionnel de santé ni une validation médicale, et il n'a fait l'objet d'aucune validation clinique. Il ne doit pas être utilisé pour des décisions de soins réelles.

---

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Résultats du modèle](#résultats-du-modèle)
- [Architecture](#architecture)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Variables d'environnement](#variables-denvironnement)
- [Routes principales de l'API](#routes-principales-de-lapi)
- [Limites connues](#limites-connues)
- [Auteur](#auteur)

---

## Fonctionnalités

**Espace médecin**

- **Dossiers patients** : créer, consulter, modifier et supprimer un dossier (informations cliniques, antécédents, allergies…).
- **Analyse ECG** : envoyer un enregistrement ECG (format WFDB : fichiers `.hea` + `.dat`) avec l'âge et le sexe de l'enfant. Le système renvoie les catégories détectées avec leur **probabilité calibrée**, les catégories **indéterminées** (lorsque le modèle ne peut pas trancher) et une **incertitude globale**.
- **Assistant documentaire (RAG)** : poser des questions en langage naturel sur les documents de référence indexés et consulter les sources associées ; historique des sessions et suppression d'une session.

**Espace administrateur**

- Créer un compte médecin, l'activer ou le désactiver.
- Consulter la liste des médecins et les statistiques générales de la plateforme.

Il n'y a pas d'espace patient : seuls les professionnels de santé utilisent l'application.

---

## Résultats du modèle

Entraîné et évalué sur le jeu de données public **ZZU Pediatric ECG** (ECG pédiatriques de l'université de Zhengzhou, 12 453 enregistrements retenus après contrôle qualité, séparés par patient : 7 464 / 2 486 / 2 503).

Résultats sur l'ensemble de test (2 503 ECG de patients jamais vus) :

| Métrique | Valeur |
|---|---|
| Macro-F1 | 0,5550 (IC 95 % bootstrap : 0,5303 – 0,5763) |
| Micro-F1 | 0,6641 |
| AUC macro | 0,8893 |
| mAP | 0,5675 |
| Exactitude stricte (exact match) | 0,3352 |

- **Modèle** : ensemble de 6 modèles HuBERT-ECG affinés (signal ECG) fusionnés avec une branche clinique (MLP sur l'âge, le sexe et le nombre de dérivations), entraînés avec deux fonctions de coût (Asymmetric Loss et Class-Balanced BCE).
- **Fiabilité** : calibration de Platt (erreur de calibration 0,1133 → 0,0151), seuils de décision par catégorie, prédiction conforme (α = 0,10).
- **Apport des données cliniques** : l'ablation ne met pas en évidence de gain mesurable de l'âge et du sexe par rapport au signal seul (macro-F1 0,532 pour le signal seul, 0,529 pour signal + âge + sexe).

Les performances sont mesurées sur une seule source de données : la généralisation à d'autres populations n'est pas démontrée.

---

## Architecture

```
Frontend (React)  ──►  Backend (FastAPI)  ──►  PostgreSQL + pgvector
                          │
                          ├──► Module d'analyse ECG (HuBERT-ECG, PyTorch)
                          │        └─ poids hébergés sur Hugging Face (dépôt privé)
                          └──► Module RAG (LangChain, embeddings E5, Ollama / Qwen 2.5)
```

| Couche | Technologies |
|---|---|
| Frontend | React |
| Backend | Python, FastAPI, SQLAlchemy, Alembic, authentification JWT |
| Base de données | PostgreSQL avec l'extension pgvector |
| Analyse ECG | PyTorch, Hugging Face Transformers, WFDB |
| RAG | LangChain, sentence-transformers (`intfloat/multilingual-e5-base`), Ollama (`qwen2.5:3b`) |

**Structure du backend**

```
app/
  main.py  config.py  database.py  deps.py  security.py  models.py  schemas.py
  routers/   auth · admin · medecin · sessions_rag · documents · cas_clinique
  services/  rag_service · ecg_service · dawn_ecg_model · wfdb_service · session_cleanup
data/docs/   documents de référence indexés (Markdown)
seed_admin.py  seed_documents.py
```

---

## Installation

### Prérequis

- Python 3.10+
- Node.js (pour le frontend)
- Docker (pour PostgreSQL avec pgvector)
- [Ollama](https://ollama.com) (pour l'assistant documentaire)

### 1. Base de données

```bash
docker run -d --name dawn-postgres \
  -e POSTGRES_USER=<utilisateur> -e POSTGRES_PASSWORD=<mot_de_passe> -e POSTGRES_DB=dawn_db \
  -p 5432:5432 pgvector/pgvector:pg16

docker exec -it dawn-postgres psql -U <utilisateur> -d dawn_db \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

L'extension `vector` doit exister avant le premier démarrage de l'API.

### 2. Backend

```bash
python -m venv venv
source venv/bin/activate            # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # puis éditer .env (voir ci-dessous)
```

Créer le premier administrateur, télécharger le modèle de langage et indexer les documents :

```bash
python seed_admin.py
ollama pull qwen2.5:3b
python seed_documents.py
```

Au premier calcul d'embeddings, le modèle E5 est téléchargé (connexion internet nécessaire).

### 3. Modèle ECG

Les poids du modèle ECG (environ 732 Mo pour les six modèles) **ne sont pas dans ce dépôt**. Ils sont hébergés dans un dépôt privé Hugging Face. Pour les utiliser :

- renseigner `ECG_MODEL_REPO` et `HF_TOKEN` dans `.env`, ou
- pointer `ECG_MODEL_LOCAL_DIR` vers un dossier local contenant le modèle.

Ne jamais commiter le jeton `HF_TOKEN`.

### 4. Frontend

```bash
cd frontend                         # adapter au nom du dossier du frontend
npm install
npm start                           # http://localhost:3000
```

---

## Utilisation

```bash
docker start dawn-postgres
source venv/bin/activate
uvicorn app.main:app --reload
```

- API : http://localhost:8000
- Documentation interactive (Swagger) : http://localhost:8000/docs
- Ollama doit tourner en parallèle (`ollama list` pour vérifier que le modèle est présent).

Format ECG accepté : **WFDB** (paire `.hea` + `.dat`). Le nombre de dérivations, la fréquence et la durée sont lus dans l'en-tête ; l'âge et le sexe viennent du dossier patient.

---

## Variables d'environnement

| Variable | Rôle | Défaut |
|---|---|---|
| `DATABASE_URL` | Connexion PostgreSQL | voir `.env.example` |
| `SECRET_KEY` | Signature des jetons JWT — **à changer** | `change-me` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Durée de connexion | `480` |
| `CORS_ORIGINS` | Origines autorisées (frontend) | `http://localhost:3000` |
| `OLLAMA_BASE_URL` | Adresse d'Ollama | `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Modèle de génération | `qwen2.5:3b` |
| `OLLAMA_NUM_CTX` | Fenêtre de contexte | `8192` |
| `EMBEDDING_MODEL` | Modèle d'embeddings | `intfloat/multilingual-e5-base` |
| `RAG_TOP_K` | Documents récupérés par question | `4` |
| `RAG_MAX_CONTEXT_CHARS` | Taille max des extraits injectés | `16000` |
| `ECG_MODEL_REPO` | Dépôt Hugging Face du modèle ECG | voir `.env.example` |
| `HF_TOKEN` | Jeton Hugging Face (dépôt privé) | — |
| `ECG_MODEL_LOCAL_DIR` | Dossier local du modèle (alternative hors ligne) | — |
| `ECG_MODEL_ENABLED` | Activer l'analyse ECG | `true` |
| `ECG_PRELOAD_AT_STARTUP` | Charger le modèle au démarrage | `false` |

---

## Routes principales de l'API

| Préfixe | Routes |
|---|---|
| `/auth` | `POST /login` · `POST /logout` · `GET`/`PATCH /me` · `POST /changer-mot-de-passe` |
| `/admin` | `POST`/`GET /medecins` · `GET /utilisateurs` · `PATCH /utilisateurs/{id}/statut` · `GET /statistiques` |
| `/medecin` | `POST`/`GET /dossiers` · `GET`/`PATCH`/`DELETE /dossiers/{id}` · `GET /statistiques` |
| `/medecin/sessions` | `POST`/`GET` · `PATCH`/`DELETE /{id}` · `GET /{id}/messages` · `POST /{id}/messages/texte` · `POST /{id}/messages/ecg` |
| `/documents` | `POST`/`GET` · `POST /{id}/indexer` |

La liste complète est dans la documentation Swagger (`/docs`).

---

## Limites connues

- **Pas de validation clinique** : le modèle n'a pas été évalué par des cardiologues ni sur des données indépendantes du jeu ZZU.
- **Catégories rares** (par exemple G et M) : très peu d'exemples dans le jeu de test, donc performances non validables.
- **Niveau de détail** : le modèle prédit des **catégories AHA** (12 classes) et non le code diagnostique fin.
- **Module RAG** : il repose sur un petit modèle de langage exécuté localement (Qwen 2.5 3B). Sur la machine de test, une réponse prend environ 100 à 270 secondes (six mesures). Les réponses peuvent rester imprécises et doivent être relues par le médecin. La liste de « sources » affiche les documents les plus proches de la question, pas des citations vérifiées. Le module n'a pas fait l'objet d'une évaluation chiffrée. Le corpus actuel ne couvre que l'interprétation de l'ECG pédiatrique, pas la thérapeutique.
- **Suppression définitive** : supprimer une session ou un dossier est irréversible. Un déploiement réel préférerait un archivage.
- **Mesures de performance logicielle limitées** : l'analyse ECG prend environ 3,5 à 4,6 s (trois mesures) ; ce ne sont pas des mesures de charge.

---

## Auteur

**Adama Gueye** — Master 2 Data Science & Intelligence Artificielle, Institut Supérieur d'Informatique (ISI), Sénégal.
Encadrement : M. Ibrahima Sy.

## Licence

Le jeu de données ZZU Pediatric ECG et les modèles pré-entraînés utilisés ont leurs propres licences et conditions d'utilisation.
