from embeddings import embed
from preprocess import load_all_pdfs
from chunking import chunk_text
import os
print("START SCRIPT")
# chemin dataset
base_dir = os.path.dirname(__file__)
folder = os.path.abspath(
    os.path.join(base_dir, "..", "data", "tdrs")
)

# 1. charger docs
docs = load_all_pdfs(folder)

all_chunks = []

# 2. chunking
for doc in docs:
    chunks = chunk_text(doc["text"])

    for i, chunk in enumerate(chunks):
        all_chunks.append({
            "file_name": doc["file_name"],
            "chunk_id": i,
            "text": chunk
        })

print("Chunks:", len(all_chunks))

# 3. extraction texte seulement
texts = [c["text"] for c in all_chunks]

# 4. embeddings
vectors = embed(texts)
print("Embeddings DONE")
print("Embeddings shape:", len(vectors), "x", len(vectors[0]))