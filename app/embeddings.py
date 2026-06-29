from sentence_transformers import SentenceTransformer

# multilingual-e5-small : multilingue (FR/EN/DE), rapide, 384 dimensions
model = SentenceTransformer("intfloat/multilingual-e5-small")


def embed(texts, is_query=False):
    """
    e5 nécessite un préfixe obligatoire :
    - "query: " pour les requêtes de recherche
    - "passage: " pour les documents à indexer
    """
    prefix = "query: " if is_query else "passage: "
    texts = [f"{prefix}{t}" for t in texts]

    return model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
        batch_size=64,
    )