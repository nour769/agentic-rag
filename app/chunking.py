import re

SECTION_PATTERNS = [
    r"contexte", r"context", r"background", r"kontext",
    r"objectifs?", r"objectives?", r"ziel",
    r"profil", r"profile", r"qualifications?", r"required skills",
    r"compétences?", r"competenc(?:e|y|ies)", r"kompetenzen",
    r"missions?", r"tasks?", r"aufgaben", r"termes? de référence",
    r"livrables?", r"deliverables?", r"ergebnisse",
    r"durée", r"duration", r"dauer",
    r"méthodologie", r"methodology",
    r"qualifications? requises?", r"experience required",
    r"experience", r"references", r"references",
]

SECTION_REGEX = re.compile(
    r"(?im)^[ \t]*(?:\d+[\.\)]\s*)?(" + "|".join(SECTION_PATTERNS) + r")[\s:.\-]*$"
)


def split_by_sections(text):
    """Split text into sections based on headers."""
    matches = list(SECTION_REGEX.finditer(text))

    if not matches:
        return [("document", text)]

    sections = []
    for i, m in enumerate(matches):
        title = m.group(1).strip().lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections.append((title, content))

    return sections if sections else [("document", text)]


def clean_text(text):
    """Clean and normalize text for better embeddings."""
    # Supprimer espaces multiples
    text = re.sub(r'\s+', ' ', text)
    # Supprimer caractères spéciaux non pertinents
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
    return text.strip()


def chunk_text(text, chunk_size=512, overlap=100, min_chunk_words=20):
    """
    Chunk text with better context preservation.
    
    Retourne une liste de dicts {text, section}.
    
    Args:
        text: Full document text
        chunk_size: Words per chunk (increased for better context)
        overlap: Overlapping words between chunks (increased)
        min_chunk_words: Minimum words to create a chunk
    """
    # Nettoyage
    text = clean_text(text)
    sections = split_by_sections(text)
    chunks = []

    for section_title, section_text in sections:
        words = section_text.split()

        # Si la section est courte, garder comme un seul chunk
        if len(words) <= chunk_size:
            if len(words) >= min_chunk_words:
                chunks.append({"text": section_text, "section": section_title})
            continue

        # Chunking avec overlap pour préserver la continuité
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            piece = words[start:end]
            
            if len(piece) >= min_chunk_words:
                chunks.append({
                    "text": " ".join(piece),
                    "section": section_title,
                })
            
            # Avancer avec overlap
            start += chunk_size - overlap
            if start >= len(words) - min_chunk_words:
                break

    return chunks