#!/usr/bin/env python
"""Quick test to verify the RAG system works with a small subset."""

import sys
sys.path.insert(0, '.')

from app.preprocess import load_all_pdfs
from app.chunking import chunk_text
from app.embeddings import embed
from app.vector_db import create_collection, insert_vectors
import os

# Test with just 3 PDFs
base_dir = os.path.dirname(__file__)
folder = os.path.abspath(os.path.join(base_dir, "data", "tdrs"))

print("[TEST] Loading PDFs...")
docs = load_all_pdfs(folder)[:3]  # Just first 3 PDFs
print(f"[TEST] Loaded {len(docs)} docs")

# Chunk
all_chunks = []
for doc in docs:
    chunks = chunk_text(doc["text"])
    for i, chunk in enumerate(chunks):
        all_chunks.append({
            "file_name": doc["file_name"],
            "chunk_id": i,
            "text": chunk["text"],
            "section": chunk.get("section", ""),
        })

print(f"[TEST] Created {len(all_chunks)} chunks")

# Embed (small batch)
texts = [c["text"] for c in all_chunks]
print("[TEST] Embedding texts...")
vectors = embed(texts, is_query=False)
print(f"[TEST] Created {len(vectors)} embeddings")

# Insert
print("[TEST] Creating collection...")
create_collection(vector_size=1024)
print("[TEST] Inserting vectors...")
insert_vectors(vectors, all_chunks)

print("[TEST] SUCCESS - System works!")

# Test search
print("[TEST] Testing search...")
from app.search import ask
ask("TDR")
