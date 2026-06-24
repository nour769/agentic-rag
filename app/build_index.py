from app.preprocess import load_all_pdfs
from app.chunking import chunk_text
from app.embeddings import embed
from app.vector_db import create_collection, insert_vectors
import os

base_dir = os.path.dirname(__file__)
folder = os.path.abspath(os.path.join(base_dir, "..", "data", "tdrs"))

print("[FOLDER]:", folder)
print("[FILES IN FOLDER]:", os.listdir(folder))

docs = load_all_pdfs(folder)
print("[DOCS LOADED]:", len(docs))

if len(docs) == 0:
    print("[ERROR] NO DOCS FOUND - STOPPING")
    exit()

# CHUNKING (section-aware)
all_chunks = []
for doc in docs:
    chunks = chunk_text(doc["text"])
    for i, chunk in enumerate(chunks):
        all_chunks.append({
            "file_name": doc["file_name"],
            "chunk_id": i,
            "text": chunk["text"],
            "section": chunk["section"],
        })

print("[CHUNKS]:", len(all_chunks))

# EMBEDDINGS
texts = [c["text"] for c in all_chunks]
print("[TYPE CHECK]:", type(texts[0]))

vectors = embed(texts, is_query=False)

print("[VECTORS DONE]:", len(vectors))

# QDRANT
create_collection(vector_size=1024)
insert_vectors(vectors, all_chunks)

print("[SUCCESS] INDEXING DONE")  