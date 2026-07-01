# 🔍 Agentic RAG — Indexation et Recherche de Termes de Référence (TdR)

> Projet de stage EY — Nour Mrabet  
> Système de recherche intelligente de Termes de Référence d'appels d'offres internationaux

---

## 📋 Description

Ce projet implémente un système **Agentic RAG** (Retrieval-Augmented Generation) permettant d'indexer et d'interroger une base de 100 Termes de Référence (TdR) d'appels d'offres internationaux.

L'utilisateur peut effectuer des recherches en langage naturel sur les TdR, filtrer par domaine, bailleur, pays ou région, et obtenir une réponse synthétique générée par un LLM, avec citation des sources.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│               Interface React (port 3000)            │
│   Recherche + Filtres + Résultats + Scores           │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP REST
┌──────────────────────▼──────────────────────────────┐
│               API FastAPI (port 8000)                │
│   /search  /ask  /similar  /download                 │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │            Agent Orchestrator                  │  │
│  │  1. Query Expansion (reformulations LLM)       │  │
│  │  2. Multi-search + fusion + déduplication      │  │
│  │  3. Synthèse avec citations                    │  │
│  └────────────────────────────────────────────────┘  │
└──────────────┬───────────────────┬──────────────────┘
               │                   │
   ┌───────────▼──────┐  ┌────────▼────────┐
   │  Qdrant (6333)   │  │   Groq API      │
   │  867 chunks      │  │  llama-3.3-70b  │
   │  384 dimensions  │  │                 │
   └──────────────────┘  └─────────────────┘
```

---

## 🛠️ Stack Technologique

| Composant | Technologie | Justification |
|---|---|---|
| **Backend** | Python 3.11 + FastAPI | Rapide, async, doc auto Swagger |
| **Base vectorielle** | Qdrant | Docker-native, filtres sur métadonnées, performant |
| **Embeddings** | `intfloat/multilingual-e5-small` (384 dim) | Multilingue FR/EN, léger, rapide |
| **LLM Agent** | Groq — `llama-3.3-70b-versatile` | Inférence ultra-rapide, multilingue |
| **Extraction PDF** | pypdf + Tesseract OCR | Gestion PDFs natifs ET scannés |
| **Frontend** | React + Vite + Axios | Interface moderne, palette EY |
| **Conteneurisation** | Docker Compose | 3 services orchestrés |

---

## 📁 Structure du Projet

```
agentic-rag/
├── app/
│   ├── api.py                  # API FastAPI — endpoints REST
│   ├── build_index.py          # Pipeline d'indexation complet
│   ├── preprocess.py           # Extraction texte PDF + OCR
│   ├── chunking.py             # Découpage section-aware multilingue
│   ├── embeddings.py           # Création des embeddings (e5-small)
│   ├── vector_db.py            # Client Qdrant — insert/search
│   ├── search.py               # Recherche sémantique + filtres
│   ├── theagent.py             # Agent RAG — pipeline complet
│   └── metadata_extractor.py  # Extraction métadonnées TdR
├── frontend/
│   └── src/
│       ├── App.jsx             # Interface React style EY
│       └── App.css             # Palette EY noir/jaune
├── data/
│   └── tdrs/                   # 100 TdR PDF (non versionnés)
├── docker-compose.yml          # Orchestration 3 services
├── Dockerfile.backend          # Image Python backend
├── Dockerfile.frontend         # Image Nginx frontend
├── requirements.txt            # Dépendances Python
└── .env                        # Clés API (non versionné)
```

---

## ⚙️ Méthodologie

### 1. Ingestion et Prétraitement

- Lecture des PDFs avec `pypdf` pour les documents natifs
- Détection automatique des PDFs scannés (< 50 mots extraits)
- Fallback OCR avec **Tesseract** (FR + EN) via `pdf2image`
- Filtrage des documents hors périmètre (rapports techniques, documents de physique, etc.) via `est_tdr()`

### 2. Chunking Section-Aware

- Découpage intelligent aux frontières naturelles (titres, paragraphes)
- Taille : ~500 tokens avec chevauchement de 50 tokens
- Détection des sections FR/EN/DE (Contexte, Objectifs, Profils, Livrables...)
- Chaque chunk conserve les métadonnées de son document parent

### 3. Embeddings

- Modèle : `intfloat/multilingual-e5-small` (384 dimensions)
- Préfixe obligatoire : `"query: "` pour les requêtes, `"passage: "` pour les chunks
- Choix justifié : 9h d'indexation avec `bge-m3` → migré vers `e5-small` (~5 min)

### 4. Indexation Qdrant

- Collection `tdr_chunks` avec distance COSINE
- Payload enrichi : `text`, `file_name`, `chunk_id`, `section`, `bailleur`, `pays`, `domaine`, `annee`
- Insertion par batches de 200 points

### 5. Pipeline Agentic RAG

```
Requête utilisateur
    │
    ▼
[Agent 1] Query Expansion
    Génère 3 reformulations (synonymes FR/EN, termes techniques)
    │
    ▼
[Qdrant] Multi-search (requête originale + reformulations)
    Fusion + déduplication par (file, chunk_id)
    Score threshold : 0.45
    │
    ▼
[Agent 2] Détection fichier ciblé (match_file_in_query)
    Si nom de fichier détecté → récupération de tous ses chunks
    │
    ▼
[Agent 3] Synthèse LLM
    Réponse factuelle avec citations, max 5 phrases
    Anti-hallucination : "Cette information n'est pas mentionnée"
```

---

## 📊 Résultats d'Indexation

| Métrique | Valeur |
|---|---|
| Documents fournis | 100 TdR |
| Documents indexés | 91 |
| Chunks générés | 867 |
| PDFs scannés (OCR) | ~10 |
| Documents filtrés | 9 |

### Documents non indexés (justifiés)

| Fichier | Raison |
|---|---|
| `*report*`, `*progress*`, `*slides*` | Hors périmètre TdR (filtrés par `est_tdr()`) |
| `TR-2012-006_TDR_WP73.pdf` | Fichier HTML déguisé en PDF (corrompu) |
| `20180528_TdR-Assistance-tech_...PDF` | Extension `.PDF` majuscule |
| Document Banque Mondiale | Document de régulation interne, pas un TdR |

---

## 🚀 Installation et Exécution

### Prérequis

- Docker Desktop
- Python 3.11+
- Node.js 18+
- Clé API Groq (gratuite sur [console.groq.com](https://console.groq.com))

### 1. Cloner le projet

```bash
git clone https://github.com/nour769/agentic-rag.git
cd agentic-rag
```

### 2. Configurer les variables d'environnement

```bash
# Créer le fichier .env
echo GROQ_API_KEY=votre_clé_ici > .env
```

### 3. Lancer avec Docker Compose

```bash
docker compose up --build
```

Les 3 services démarrent :
- Frontend : http://localhost:3000
- Backend API : http://localhost:8000
- Qdrant Dashboard : http://localhost:6333/dashboard

### 4. Indexer les TdR

Placer les PDFs dans `data/tdrs/` puis :

```bash
cd app
python build_index.py
```

### 5. Accéder à l'interface

Ouvrir http://localhost:3000

---

## 🔌 API Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| `POST` | `/search` | Recherche sémantique simple |
| `POST` | `/ask` | Recherche Agentic RAG avec synthèse LLM |
| `POST` | `/similar` | Missions similaires à un TdR |
| `GET` | `/download/{file_name}` | Téléchargement du PDF original |
| `GET` | `/` | Health check |

### Exemple de requête `/ask`

```json
{
  "query": "Expert en gestion de l'eau potable en Afrique",
  "top_k": 10,
  "score_threshold": 0.45,
  "pays": "Tunisie",
  "bailleur": "Banque Mondiale"
}
```

---

## 🔄 Alternatives Étudiées

| Composant | Alternative étudiée | Choix retenu | Raison |
|---|---|---|---|
| Base vectorielle | ChromaDB, Weaviate | **Qdrant** | Meilleur support Docker, filtres sur payload |
| Embeddings | `bge-m3` (1024 dim) | **e5-small** (384 dim) | bge-m3 = 9h d'indexation, e5-small = 5 min |
| LLM | OpenAI GPT-4o | **Groq llama-3.3-70b** | Gratuit, ultra-rapide, multilingue |
| Framework agent | LangChain, LangGraph | **Pipeline custom** | Plus léger, contrôle total, moins de dépendances |
| OCR | EasyOCR | **Tesseract** | Plus stable sur Windows, support FR+EN natif |

---

## ⚠️ Limites Connues

- Les filtres `domaine/bailleur/pays` dans l'UI sont partiellement fonctionnels (extraction automatique de métadonnées à enrichir)
- L'OCR Tesseract fonctionne en local Windows uniquement (chemins hardcodés) — non disponible dans le conteneur Docker
- Les tableaux dans les PDFs sont parfois mal extraits selon la qualité du document

---

## 👤 Auteur

**Nour Mrabet** — Stagiaire EY  
GitHub : [@nour769](https://github.com/nour769)
