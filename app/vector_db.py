from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import os

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", 6333))
client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=60)

COLLECTION_NAME = "tdr_chunks"
BATCH_SIZE = 200

def create_collection(vector_size=384):
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME in existing:
        print(f"[WARNING] Collection '{COLLECTION_NAME}' already exists - deleting")
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
    print(f"[OK] Collection '{COLLECTION_NAME}' created (vector_size={vector_size})")

def insert_vectors(vectors, chunks):
    import time
    points = []
    for i, (vector, chunk) in enumerate(zip(vectors, chunks)):
        points.append(
            PointStruct(
                id=i,
                vector=vector.tolist(),
                payload={
                    "text": chunk["text"],
                    "file_name": chunk["file_name"],
                    "chunk_id": chunk["chunk_id"],
                    "section": chunk.get("section", "unknown"),
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
        client.upsert(collection_name=COLLECTION_NAME, points=batch)
        print(f"   [OK] {min(i + BATCH_SIZE, len(points))} / {len(points)} inserted")
    print(f"\n[SUCCESS] INSERT DONE: {len(points)} points in Qdrant")
