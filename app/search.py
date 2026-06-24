from app.embeddings import embed
from app.vector_db import client, COLLECTION_NAME

from qdrant_client.models import Filter, FieldCondition, MatchValue
import re


def build_filter(domaine=None, bailleur=None, pays=None, region=None):
    """Build Qdrant filter from optional metadata."""
    conditions = []
    if domaine:
        conditions.append(FieldCondition(key="domaine", match=MatchValue(value=domaine)))
    if bailleur:
        conditions.append(FieldCondition(key="bailleur", match=MatchValue(value=bailleur)))
    if pays:
        conditions.append(FieldCondition(key="pays", match=MatchValue(value=pays)))
    if region:
        conditions.append(FieldCondition(key="region", match=MatchValue(value=region)))
    return Filter(must=conditions) if conditions else None


def preprocess_query(query):
    """Normalize and clean query for better matching."""
    # Convert to lowercase
    query = query.lower().strip()
    # Remove extra spaces
    query = re.sub(r'\s+', ' ', query)
    # Remove special characters but keep meaningful ones
    query = re.sub(r'[^\w\s\-\']', ' ', query)
    query = re.sub(r'\s+', ' ', query).strip()
    return query


def search(query, top_k=10, score_threshold=0.35, **filters):
    """
    Semantic search with optimized scoring.
    
    Args:
        query: Search query
        top_k: Number of results to return
        score_threshold: Minimum similarity score (lowered for better recall)
        **filters: Optional metadata filters
    """
    # Preprocess query for better matching
    processed_query = preprocess_query(query)
    
    # Generate query embedding with is_query=True
    query_vector = embed([processed_query], is_query=True)[0]

    query_filter = build_filter(**filters)

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k * 2,  # Fetch more, then filter
        score_threshold=score_threshold,
        query_filter=query_filter,
        with_payload=True,
    )

    results = []
    for point in response.points:
        results.append({
            "score": round(point.score, 4),
            "text": point.payload.get("text", ""),
            "section": point.payload.get("section", "unknown"),
            "file": point.payload.get("file_name", "unknown"),
            "chunk_id": point.payload.get("chunk_id", None),
            "domaine": point.payload.get("domaine"),
            "bailleur": point.payload.get("bailleur"),
            "pays": point.payload.get("pays"),
            "region": point.payload.get("region"),
        })

    # Sort by score and return top_k
    return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]


def ask(query, top_k=10, score_threshold=0.35, **filters):
    """
    Execute search and display results with better formatting.
    
    Args:
        query: Search query
        top_k: Number of results to display
        score_threshold: Minimum similarity score
        **filters: Optional metadata filters
    """
    results = search(query, top_k=top_k, score_threshold=score_threshold, **filters)
    
    if not results:
        print("[ERROR] NO RESULTS FOUND")
        return results
    
    print(f"\n[SEARCH] TOP {len(results)} RESULTS FOR: '{query}'\n")
    
    for i, r in enumerate(results, 1):
        print(f"{'='*60}")
        print(f"#{i} - File: {r['file']} | Section: {r['section']}")
        print(f"Score: {r['score']} | Chunk: {r['chunk_id']}")
        if r.get("domaine"):
            print(f"Domain: {r['domaine']}")
        print(f"\nContent:\n{r['text'][:400]}...")
        print()
    
    return results