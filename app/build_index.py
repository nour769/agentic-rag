from preprocess import load_all_pdfs
from chunking import chunk_text
from embeddings import embed
from vector_db import create_collection, insert_vectors
from metadata_extractor import extraire_metadata
import os

# ─── CHEMINS ───────────────────────────────────────────────
base_dir = os.path.dirname(__file__)
folder = os.path.abspath(os.path.join(base_dir, "..", "data", "tdrs"))

print("📁 FOLDER:", folder)
print("📄 FILES IN FOLDER:", os.listdir(folder))

# ─── CHARGEMENT DES PDFs ───────────────────────────────────
docs = load_all_pdfs(folder)
print(f"✅ DOCS LOADED: {len(docs)}")

if len(docs) == 0:
    print("❌ NO DOCS FOUND - STOP HERE")
    exit()

# ─── CHUNKING + METADATA ───────────────────────────────────
# ✅ Bug corrigé — tu avais déclaré all_chunks = [] deux fois
all_chunks = []

for i, doc in enumerate(docs):
    print(f"[{i+1}/{len(docs)}] ✂️  Chunking : {doc['file_name']}")

    # Extraire les métadonnées du document
    metadata = extraire_metadata(doc["text"])

    # Découper en chunks
    chunks = chunk_text(doc["text"])

    for j, chunk in enumerate(chunks):
        all_chunks.append({
            "file_name": doc["file_name"],
            "chunk_id": j,
            "text": chunk["text"],
            "section": chunk["section"],
            # Métadonnées pour les filtres Qdrant
            "bailleur": metadata.get("bailleur", ""),
            "pays":     metadata.get("pays", ""),
            "domaine":  metadata.get("domaine", ""),
            "annee":    metadata.get("annee", "")
        })

print(f"✅ CHUNKS: {len(all_chunks)}")

# ─── EMBEDDINGS ────────────────────────────────────────────
print("⏳ Création des embeddings...")
texts = [c["text"] for c in all_chunks]
vectors = embed(texts, is_query=False)
print(f"✅ VECTORS DONE: {len(vectors)}")

# Vérification cohérence
if len(vectors) != len(all_chunks):
    print(f"❌ ERREUR : {len(vectors)} vecteurs pour {len(all_chunks)} chunks !")
    exit()

# ─── INDEXATION QDRANT ─────────────────────────────────────
print("⏳ Indexation dans Qdrant...")
create_collection(vector_size=384)
insert_vectors(vectors, all_chunks)

print("\n🎉 INDEXING DONE")
print(f"   → {len(all_chunks)} chunks indexés")
print(f"   → {len(docs)} documents traités")
