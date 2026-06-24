from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import os

# ✅ Use local storage instead of remote server
db_path = os.path.join(os.path.dirname(__file__), "..", "qdrant_storage")
os.makedirs(db_path, exist_ok=True)
client = QdrantClient(path=db_path)

COLLECTION_NAME = "tdr_chunks"
BATCH_SIZE = 200


# 1. CREATE COLLECTION
def create_collection(vector_size=1024):
    """
    Crée la collection dans Qdrant.
    Si elle existe déjà, on la supprime et recrée proprement.
    vector_size=1024 car on utilise BAAI/bge-m3 (multilingue FR/EN/DE).
    """
    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in existing:
        print(f"[WARNING] Collection '{COLLECTION_NAME}' already exists - deleting")
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE
        )
    )
    print(f"[OK] Collection '{COLLECTION_NAME}' created (vector_size={vector_size})")


# 2. INSERT DATA
def insert_vectors(vectors, chunks):
    """
    Insère les vecteurs dans Qdrant par batches.
    - vectors : liste d'embeddings numpy
    - chunks  : liste de dicts avec text, file_name, chunk_id, section
    """
    points = []
    for i, (vector, chunk) in enumerate(zip(vectors, chunks)):
        points.append(
            PointStruct(
                id=i,
                vector=vector.tolist(),  # numpy → liste Python
                payload={
                    "text": chunk["text"],
                    "file_name": chunk["file_name"],   # ✅ clé harmonisée
                    "chunk_id": chunk["chunk_id"],
                    "section": chunk.get("section", "unknown"),
                    # métadonnées pour les filtres (à enrichir plus tard,
                    # cf. extraction automatique de métadonnées)
                    "bailleur": chunk.get("bailleur", ""),
                    "pays": chunk.get("pays", ""),
                    "domaine": chunk.get("domaine", ""),
                    "annee": chunk.get("annee", "")
                }
            )
        )

    print(f"[INSERTING] {len(points)} points in batches of {BATCH_SIZE}...")

    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i:i + BATCH_SIZE]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )
        print(f"   [OK] {min(i + BATCH_SIZE, len(points))} / {len(points)} inserted")

    print(f"\n[SUCCESS] INSERT DONE: {len(points)} points in Qdrant")