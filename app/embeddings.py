from sentence_transformers import SentenceTransformer

# bge-m3 : multilingue (FR/EN/DE/+100 langues), 1024 dimensions
# Meilleur modèle pour la recherche dense en multilingue
model = SentenceTransformer("BAAI/bge-m3")


def embed(texts, is_query=False):
    """
    Encode texts to embeddings with optional query prefix.
    
    Args:
        texts: List of strings to embed
        is_query: If True, prepend 'query: ' prefix for search queries
        
    Returns:
        List of normalized embedding vectors
    """
    if not texts:
        return []
    
    # Préfixe query pour les requêtes (meilleure performance en recherche)
    if is_query:
        texts = [f"query: {t}" for t in texts]
    
    vectors = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
        batch_size=32,  # Meilleure performance avec batch processing
    )
    
    return vectors