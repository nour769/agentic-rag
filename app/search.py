from app.embeddings import embed
from app.vector_db import client, COLLECTION_NAME

from qdrant_client.models import Filter, FieldCondition, MatchValue


def build_filter(domaine=None, bailleur=None, pays=None, region=None):
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


def search(query, top_k=10, score_threshold=0.45, **filters):
    query_vector = embed([query], is_query=True)[0]
    query_filter = build_filter(**filters)

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
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

    return sorted(results, key=lambda x: x["score"], reverse=True)


def multi_search(user_query, top_k=10, score_threshold=0.45, **filters):
    """
    Recherche simple basee sur la requete originale (sans expansion LLM ici,
    cette fonction est utilisee directement par theagent.py).
    """
    return search(user_query, top_k=top_k, score_threshold=score_threshold, **filters)


_file_list_cache = None

def list_all_files():
    """
    Retourne la liste unique de tous les noms de fichiers presents dans Qdrant.
    Mise en cache en memoire.
    """
    global _file_list_cache
    if _file_list_cache is not None:
        return _file_list_cache

    seen = set()
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=500,
            offset=offset,
            with_payload=["file_name"],
            with_vectors=False,
        )
        for p in points:
            fn = p.payload.get("file_name")
            if fn:
                seen.add(fn)
        if offset is None:
            break

    _file_list_cache = list(seen)
    return _file_list_cache


def match_file_in_query(query_text):
    """
    Cherche si le nom (ou une partie significative du nom) d'un fichier indexe
    apparait dans la question de l'utilisateur.
    """
    files = list_all_files()
    query_lower = query_text.lower()

    stopwords = {"tdr", "termes", "reference", "pdf", "document", "fichier", "le", "la", "de", "du", "des"}

    best_match = None
    best_match_count = 0

    for fname in files:
        base_name = fname.rsplit(".", 1)[0].lower()
        normalized_base = base_name.replace("_", " ").replace("-", " ")
        normalized_query = query_lower.replace("_", " ").replace("-", " ")

        name_words = [w for w in normalized_base.split() if len(w) >= 3 and w not in stopwords and not w.isdigit()]
        if not name_words:
            continue

        matches = sum(1 for w in name_words if w in normalized_query)
        if matches == 0:
            continue

        match_ratio = matches / len(name_words)

        if match_ratio >= 0.3 and matches > best_match_count:
            best_match = fname
            best_match_count = matches

    return best_match


def get_all_chunks_for_file(file_name):
    """
    Retourne tous les chunks d'un document precis, tries par chunk_id.
    """
    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[FieldCondition(key="file_name", match=MatchValue(value=file_name))]
        ),
        limit=1000,
        with_payload=True,
        with_vectors=False,
    )

    chunks = []
    for p in points:
        chunks.append({
            "text": p.payload.get("text", ""),
            "section": p.payload.get("section", "unknown"),
            "file": p.payload.get("file_name", "unknown"),
            "chunk_id": p.payload.get("chunk_id", 0),
            "score": 1.0,
            "domaine": p.payload.get("domaine"),
            "bailleur": p.payload.get("bailleur"),
            "pays": p.payload.get("pays"),
            "region": p.payload.get("region"),
        })

    chunks.sort(key=lambda c: c["chunk_id"])
    return chunks


def find_similar(file_name, chunk_id=0, top_k=5):
    """
    Trouve les chunks les plus similaires a un chunk donne (par son vecteur),
    en excluant les chunks provenant du meme fichier source.
    """
    scroll_result = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="file_name", match=MatchValue(value=file_name)),
                FieldCondition(key="chunk_id", match=MatchValue(value=chunk_id)),
            ]
        ),
        limit=1,
        with_vectors=True,
    )

    points = scroll_result[0]
    if not points:
        return []

    source_vector = points[0].vector

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=source_vector,
        limit=top_k + 5,
        with_payload=True,
    )

    similar = []
    seen_files = set()
    for point in response.points:
        pf = point.payload.get("file_name", "")
        if pf == file_name:
            continue
        if pf in seen_files:
            continue
        seen_files.add(pf)
        similar.append({
            "score": round(point.score, 4),
            "text": point.payload.get("text", ""),
            "file": pf,
            "section": point.payload.get("section", "unknown"),
        })
        if len(similar) >= top_k:
            break

    return similar


def ask(query, **filters):
    results = search(query, **filters)
    print("\nTOP RESULTS\n")
    for r in results:
        print(f"File: {r['file']} | Section: {r['section']}")
        print(f"Score: {r['score']}")
        print(r["text"][:300])
        print("-" * 50)
    return results