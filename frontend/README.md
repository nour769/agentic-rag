TenderScope — Agentic RAG pour Termes de Référence

Plateforme de recherche sémantique et d'interrogation intelligente d'une base de Termes de Référence (TdR) d'appels d'offres, développée dans le cadre d'un stage chez EY.

L'objectif : permettre de retrouver les missions, profils et compétences exigés à travers une base documentaire hétérogène, en allant au-delà de la simple correspondance par mots-clés — et de répondre fidèlement à des questions précises sur un TdR nommé, sans halluciner.


Sommaire


Architecture
Choix technologiques
Méthodologie
Alternatives étudiées
Installation et exécution
Structure du projet
État de la base documentaire
Limites connues et pistes d'amélioration



Architecture

Le système est construit en couches indépendantes, pour que chaque composant puisse évoluer sans affecter les autres :

PDF (data/tdrs/)
   │
   ▼
[Ingestion]  pypdf (texte natif) → fallback OCR (Tesseract + Poppler) si texte natif insuffisant
   │
   ▼
[Chunking]   découpage section-aware (Contexte / Objectifs / Profil / Livrables…), multilingue FR/EN/DE
   │
   ▼
[Embeddings] intfloat/multilingual-e5-small → vecteurs 384 dimensions
   │
   ▼
[Indexation] Qdrant (base vectorielle), métadonnées en payload
   │
   ▼
[Recherche]  recherche par similarité cosinus + détection de document nommé explicitement
   │
   ▼
[Agent]      Groq (Llama 3.3 70B) — reformulation de requête OU lecture intégrale du document ciblé
   │
   ▼
[API]        FastAPI — endpoints REST (/ask, /search, /similar, /download)
   │
   ▼
[Frontend]   React + Vite — interface de recherche, filtres, résultats, téléchargement

Le composant "agentic" du pipeline

Ce qui distingue ce système d'un RAG classique est une étape de décision avant la recherche :


Si la question nomme un TdR précis (ex. "quel est le barème de notation du TdR ERP UVT ?"), l'agent détecte le document visé et lit l'intégralité de ses chunks plutôt que de chercher par similarité globale. Ça garantit une réponse fidèle à ce document précis, même si la question porte sur un détail peu saillant sémantiquement.
Sinon, l'agent reformule la requête en plusieurs variantes (synonymes métier, traduction implicite), lance une recherche multiple, fusionne et déduplique les résultats par document.


Dans les deux cas, la génération de réponse est contrainte par un prompt strict qui interdit la spéculation : si l'information n'est pas dans les extraits fournis, l'agent répond explicitement que l'information n'est pas mentionnée, plutôt que d'inventer.


Choix technologiques

ComposantChoix retenuJustificationExtraction PDFpypdf + fallback OCRGratuit, rapide pour le texte natif ; l'OCR ne se déclenche que si le texte natif est insuffisant (< 50 mots), pour ne pas pénaliser les performances sur les PDF texteOCRTesseract + pdf2image/PopplerOpen source, support multilingue (français, anglais, allemand) via les packs de langue fra, eng, deuChunkingRègles maison (regex section-aware)Les TdR ont une structure de sections récurrente ; découper par section plutôt que par nombre de mots fixe préserve la cohérence sémantique des chunksEmbeddingsintfloat/multilingual-e5-smallCompromis qualité/vitesse retenu après deux itérations : bge-small-en-v1.5 (mono-anglais, résultats incohérents sur du contenu FR/DE) puis bge-m3 (qualité supérieure mais ~9h d'indexation sur CPU, jugé trop coûteux en temps de développement)Base vectorielleQdrant (mode serveur, conteneurisable)Open source, performant, API Python claire, supporte le filtrage par métadonnées en plus de la similarité vectorielleLLM agentGroq (Llama 3.3 70B Versatile)Gratuit en usage modéré, latence faible, bon support multilingueAPIFastAPITypage des requêtes via Pydantic, documentation interactive automatique (/docs), performances correctes pour ce volumeFrontendReact + ViteDemandé explicitement dans le brief ; Vite pour un cycle de développement rapide


Méthodologie

Prétraitement

Chaque PDF passe par :


Extraction de texte natif page par page (pypdf)
Si le texte extrait fait moins de 50 mots → bascule automatique sur l'OCR (conversion en image à 300 DPI, lecture Tesseract multilingue)
Filtrage heuristique des documents hors périmètre (noms de fichiers contenant des marqueurs comme report, progress, slides, results, qui se sont avérés correspondre à des documents non-TdR mélangés dans le lot fourni — voir État de la base documentaire)


Chunking

Le texte de chaque document est d'abord découpé par sections logiques détectées via expressions régulières multilingues (Contexte/Context/Kontext, Objectifs/Objectives/Ziel, Profil/Profile, Compétences/Competencies, etc.). Si une section dépasse 350 mots, elle est sous-découpée avec un overlap de 60 mots pour ne pas perdre le contexte aux frontières.

Évaluation de la pertinence

L'évaluation a été menée de façon empirique et itérative plutôt que par une métrique automatisée formelle (faute de jeu de données annoté disponible) :


Comparaison qualitative avant/après changement de modèle d'embedding sur des requêtes de référence
Vérification systématique, pour chaque réponse générée sur un document ciblé, que les faits cités sont bien présents dans le texte source (contrôle anti-hallucination par extraction manuelle du passage concerné)
Calibration du seuil de score (score_threshold) par observation directe de la distribution des scores réels sur des requêtes tests


Observabilité

Le pipeline d'indexation affiche une trace complète (document par document : chargement, détection OCR, exclusion, comptage de mots) directement dans la console. Chaque réponse de l'agent en mode ciblé indique le fichier source détecté, ce qui permet de vérifier que la bonne source a été identifiée avant même de lire la réponse.


Alternatives étudiées


LangChain : aurait permis d'aller plus vite en assemblant des composants préexistants (loaders, text splitters, retrievers). Choix délibéré de construire chaque brique manuellement pour maîtriser et pouvoir justifier chaque décision technique (modèle d'embedding, stratégie de chunking, logique de l'agent), plutôt que d'hériter du comportement par défaut d'un framework. Une migration vers LangChain/LangGraph reste une piste d'industrialisation pertinente pour une phase ultérieure.
RAGFlow : architecture de référence étudiée pour le découpage de documents et la gestion de pipelines RAG ; non adoptée directement pour les mêmes raisons de maîtrise du code, mais a influencé l'approche de chunking section-aware.
Modèles d'embedding alternatifs testés :

bge-small-en-v1.5 (mono-anglais) → abandonné, résultats incohérents sur le contenu français/allemand de la base
BAAI/bge-m3 (multilingue, 1024 dim) → meilleure qualité observée mais temps d'indexation prohibitif sur CPU sans GPU dans le contexte du stage
intfloat/multilingual-e5-small (retenu) → meilleur compromis qualité/vitesse pour ce projet






Installation et exécution

Prérequis


Python 3.11+
Node.js 20+
Docker Desktop (pour Qdrant et la conteneurisation complète)
Tesseract OCR avec les packs de langue fra, eng, deu
Poppler (pour la conversion PDF → image utilisée par l'OCR)
Une clé API Groq (gratuite sur console.groq.com)


Configuration

Créer un fichier .env à la racine du projet :

GROQ_API_KEY=votre_cle_ici

Dans app/preprocess.py, adapter les chemins vers Tesseract et Poppler à votre installation locale si vous n'utilisez pas Docker.

Installation locale (développement)

bash# Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Démarrer Qdrant
docker run -d -p 6333:6333 -p 6334:6334 -v "${PWD}/qdrant_storage:/qdrant/storage" qdrant/qdrant

# Indexer la base documentaire (place vos PDF dans data/tdrs/ au préalable)
python -m app.build_index

# Démarrer l'API
python -m uvicorn app.api:app --port 8000

bash# Frontend (dans un terminal séparé)
cd frontend
npm install
npm run dev

L'interface est accessible sur http://localhost:5173, l'API sur http://localhost:8000 (documentation interactive sur http://localhost:8000/docs).

Via Docker Compose

bashdocker compose build
docker compose up

Les conteneurs servent l'application à partir d'une base déjà indexée (le volume qdrant_storage doit être présent localement) ; l'indexation avec OCR doit être effectuée en amont, hors conteneur, car les dépendances OCR locales (chemins Windows spécifiques) ne sont pas reproduites dans l'image Linux du conteneur.


Structure du projet

agentic-rag/
├── app/
│   ├── preprocess.py       # extraction PDF + OCR
│   ├── chunking.py         # découpage section-aware
│   ├── embeddings.py       # encodage vectoriel
│   ├── vector_db.py        # interface Qdrant
│   ├── build_index.py      # orchestration de l'indexation
│   ├── search.py           # recherche, détection de document, missions similaires
│   ├── theagent.py         # logique agentique et génération de réponse
│   └── api.py               # endpoints FastAPI
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── App.css
├── data/tdrs/               # PDF source (non versionnés)
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── requirements.txt


État de la base documentaire

Sur les 100 fichiers PDF fournis, 91 sont indexés avec succès. Les 9 documents non indexés ont été analysés individuellement :


6 documents hors périmètre : noms de fichiers indiquant des rapports d'activité, de progrès, ou des supports de présentation plutôt que des Termes de Référence (filtrage automatique sur mots-clés du nom de fichier)
1 document corrompu : fichier .pdf dont le contenu réel est une page HTML (probablement une erreur de téléchargement à la source)
1 document hors périmètre métier : règlement de procurement générique, pas un TdR de mission
1 document non traité en raison d'une extension en majuscules (.PDF), bug connu et non corrigé à ce stade par manque de temps


Cette base a aussi révélé que le lot de 100 fichiers contient, au-delà des 9 exclus, des documents totalement étrangers au domaine des appels d'offres de développement (notamment des rapports techniques du laboratoire de physique European XFEL, où l'acronyme "TDR" désigne Technical Design Report et non Termes de Référence). Le filtrage actuel sur mots-clés ne les détecte que partiellement ; une classification automatique par analyse de contenu serait nécessaire pour les exclure de façon exhaustive.


Limites connues et pistes d'amélioration


Métadonnées structurées (domaine, bailleur, pays, région) non systématiquement extraites : un module d'extraction (app/extract_metadata.py) a été développé mais n'est pas encore intégré au pipeline d'indexation principal. Les filtres présents dans l'interface ne sont donc pas garantis de filtrer sur des valeurs réellement renseignées pour chaque document à ce stade.
Filtre par date non implémenté dans l'interface utilisateur.
OCR non exécutable dans les conteneurs Docker : les chemins Tesseract/Poppler utilisés en développement sont spécifiques à l'environnement Windows local ; une version conteneurisée de l'indexation nécessiterait l'installation de ces dépendances via le gestionnaire de paquets Linux de l'image.
Pas d'évaluation quantitative formalisée (type précision/rappel sur un jeu de questions-réponses annoté) : la validation s'est appuyée sur une vérification manuelle ciblée des réponses générées, faute de temps pour constituer un jeu de test annoté représentatif.
Détection de document nommé basée sur une heuristique de correspondance de mots (pas d'embedding sémantique du nom de fichier) : fonctionne bien sur les cas testés mais pourrait échouer sur des formulations très éloignées du nom réel du fichier.


Ces points constituent les prochaines étapes naturelles pour une version industrialisée du système.