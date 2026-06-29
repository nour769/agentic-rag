# Agentic RAG — TenderScope

Agentic RAG (Retrieval-Augmented Generation) — TenderScope is a prototype system to index, search and summarise Terms of Reference (ToR) documents using vector search and LLMs. It provides a FastAPI backend, a React (Vite) frontend inspired by EY visual style, and a vector database (Qdrant) for semantic retrieval.

## Features
- Full-text semantic search with filters: domaine, bailleur, pays, région, dates.
- Agentic mode: LLM-driven synthesis with relevant source chunks.
- React frontend with responsive EY-like UI.
- Containerised via `docker-compose` for easy deployment.

## Architecture & Choices
- Backend: FastAPI (Python) — lightweight, async, good for model serving.
- Frontend: React + Vite — fast dev experience and production build.
- Vector DB: Qdrant — open-source vector database, easy to run in Docker.
- LLM: pluggable (local or API-based). Configure in `app/embeddings.py` or `app/theagent.py`.
- OCR (optional): use when ingesting PDFs with scanned pages.

## Quick Start (Local, using Docker)
Prerequisites: Docker & Docker Compose installed.

1. Build and start services:

```bash
docker compose up --build -d
```

2. Open the frontend in your browser:

- UI: http://localhost:3000
- API: http://localhost:8000

3. To stop:

```bash
docker compose down
```

## Project structure
- `app/` — backend code (search, ingestion, agent logic)
- `frontend/` — React UI (Vite)
- `data/` — source ToR files and metadata
- `qdrant_storage/` — persisted storage for Qdrant (mounted by compose)

## Deployment notes
- The `docker-compose.yml` starts three services: `backend`, `frontend` (Nginx) and `qdrant`.
- Set `VITE_API_URL` environment variable in `docker-compose.yml` if API runs on another host.

## Documentation to include in final deliverable
- Technical architecture and component diagram
- Preprocessing & chunking methodology
- Embeddings and LLM choices and configuration
- Evaluation strategy (metrics, test queries)
- Observability: logs, healthchecks, and basic monitoring

---

If tu veux, je peux maintenant:

- Finaliser et valider `VITE_API_URL` dans le build frontend.
- Lancer `docker compose up --build` ici et te donner l'URL accessible localement.
- Générer un document technique détaillé (architecture + méthodologies).

Dis-moi quelle(s) action(s) tu veux que je fasse en priorité.
