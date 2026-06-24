from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from app.search import search
from app.theagent import agentic_search

app = FastAPI(title="Agentic RAG - TdR Search API")

# CORS pour permettre à React (localhost:3000 ou autre port) d'appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à restreindre en prod
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "Agentic RAG TdR API"}


@app.get("/search")
def search_endpoint(
    query: str = Query(..., description="Texte de la requête"),
    top_k: int = Query(10, ge=1, le=50),
    score_threshold: float = Query(0.45, ge=0.0, le=1.0),
    domaine: Optional[str] = None,
    bailleur: Optional[str] = None,
    pays: Optional[str] = None,
    region: Optional[str] = None,
):
    """Recherche vectorielle simple, sans agent (rapide)."""
    filters = {k: v for k, v in {
        "domaine": domaine, "bailleur": bailleur, "pays": pays, "region": region
    }.items() if v}

    results = search(query, top_k=top_k, score_threshold=score_threshold, **filters)
    return {"query": query, "results": results}


@app.get("/agent-search")
def agent_search_endpoint(
    query: str = Query(..., description="Texte de la requête"),
    top_k: int = Query(10, ge=1, le=50),
    score_threshold: float = Query(0.45, ge=0.0, le=1.0),
    domaine: Optional[str] = None,
    bailleur: Optional[str] = None,
    pays: Optional[str] = None,
    region: Optional[str] = None,
):
    """Recherche agentic complète : expansion de requête + synthèse LLM (plus lent, plus riche)."""
    filters = {k: v for k, v in {
        "domaine": domaine, "bailleur": bailleur, "pays": pays, "region": region
    }.items() if v}

    result = agentic_search(query, top_k=top_k, score_threshold=score_threshold, **filters)
    return result