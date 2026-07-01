import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from search import search, find_similar
from theagent import agentic_search

app = FastAPI(title="Agentic RAG TdR API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "tdrs"))


class QueryRequest(BaseModel):
    query: str
    top_k: int = 10
    score_threshold: float = 0.45
    domaine: Optional[str] = None
    bailleur: Optional[str] = None
    pays: Optional[str] = None
    region: Optional[str] = None


class SimilarRequest(BaseModel):
    file_name: str
    chunk_id: int = 0
    top_k: int = 5


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/search")
def simple_search(req: QueryRequest):
    filters = {k: v for k, v in req.dict().items()
               if k in ["domaine", "bailleur", "pays", "region"] and v}
    results = search(
        req.query,
        top_k=req.top_k,
        score_threshold=req.score_threshold,
        **filters
    )
    return {
        "query": req.query,
        "results": results
    }


@app.post("/ask")
def ask(req: QueryRequest):
    filters = {k: v for k, v in req.dict().items()
               if k in ["domaine", "bailleur", "pays", "region"] and v}
    result = agentic_search(
        req.query,
        top_k=req.top_k,
        score_threshold=req.score_threshold,
        **filters
    )
    return result


@app.post("/similar")
def similar_missions(req: SimilarRequest):
    results = find_similar(req.file_name, req.chunk_id, top_k=req.top_k)
    return {"results": results}


@app.get("/download/{file_name}")
def download_tdr(file_name: str):
    file_path = os.path.join(DATA_FOLDER, file_name)
    if not os.path.exists(file_path):
        return {"error": "Fichier introuvable"}
    return FileResponse(file_path, media_type="application/pdf", filename=file_name)
