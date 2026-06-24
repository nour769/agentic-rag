import os
from dotenv import load_dotenv
from groq import Groq
from app.search import search

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.3-70b-versatile"  # bon équilibre qualité/vitesse, multilingue


def call_llm(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


# =========================
# ÉTAPE 1 : Reformulation de la requête (query expansion)
# =========================
def expand_query(user_query):
    """
    Génère 2-3 reformulations de la requête utilisateur pour améliorer le rappel
    (synonymes métier, variante FR/EN, termes techniques du secteur).
    """
    prompt = f"""Tu es un assistant qui aide à reformuler des requêtes de recherche
pour un moteur de recherche de Termes de Référence (TdR) d'appels d'offres internationaux
(développement, coopération, ONG, bailleurs de fonds).

Requête utilisateur : "{user_query}"

Génère exactement 3 reformulations alternatives de cette requête, qui captent le même besoin
mais avec des synonymes métier, une variante en anglais si la requête est en français (ou vice versa),
et des termes techniques du secteur (santé, agriculture, gouvernance, évaluation de projet, etc.).

Réponds UNIQUEMENT avec les 3 reformulations, une par ligne, sans numérotation, sans préambule."""

    text = call_llm(prompt)
    variants = [line.strip() for line in text.strip().split("\n") if line.strip()]

    return [user_query] + variants[:3]


# =========================
# ÉTAPE 2 : Recherche multi-requêtes + fusion + déduplication
# =========================
def multi_search(user_query, top_k=10, score_threshold=0.45, **filters):
    """
    Lance la recherche avec la requête originale + les reformulations,
    fusionne les résultats, déduplique par (file, chunk_id), garde le meilleur score.
    """
    queries = expand_query(user_query)
    print(f"🔍 Requêtes utilisées : {queries}")

    merged = {}
    for q in queries:
        results = search(q, top_k=top_k, score_threshold=score_threshold, **filters)
        for r in results:
            key = (r["file"], r["chunk_id"])
            if key not in merged or r["score"] > merged[key]["score"]:
                merged[key] = r

    final_results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
    return final_results[:top_k]


# =========================
# ÉTAPE 3 : Synthèse finale avec citations
# =========================
def generate_answer(user_query, results, max_context_chunks=6):
    """
    Construit une réponse synthétique à partir des meilleurs chunks trouvés,
    avec citation explicite des fichiers sources.
    """
    if not results:
        return "Aucun résultat pertinent trouvé pour cette requête dans la base de TdR."

    context_blocks = []
    for r in results[:max_context_chunks]:
        context_blocks.append(f"[Source: {r['file']}]\n{r['text']}")

    context = "\n\n---\n\n".join(context_blocks)

    prompt = f"""Tu es un assistant spécialisé dans l'analyse de Termes de Référence (TdR)
d'appels d'offres internationaux (développement, coopération, ONG).

Question de l'utilisateur : "{user_query}"

Voici des extraits de TdR pertinents trouvés dans la base documentaire :

{context}

Réponds à la question de l'utilisateur en te basant UNIQUEMENT sur ces extraits.
Si la question porte sur des missions, profils ou compétences recherchées, mets-les en évidence clairement.
Cite le nom du fichier source entre parenthèses après chaque affirmation.
Si les extraits ne permettent pas de répondre complètement, dis-le clairement.
Réponds dans la même langue que la question de l'utilisateur."""

    return call_llm(prompt)


# =========================
# FONCTION PRINCIPALE DE L'AGENT
# =========================
def agentic_search(user_query, top_k=10, score_threshold=0.45, **filters):
    """
    Pipeline agentic complet :
    1. Expansion de requête (reformulations)
    2. Recherche multi-requêtes + fusion
    3. Génération d'une réponse synthétique avec citations
    """
    results = multi_search(user_query, top_k=top_k, score_threshold=score_threshold, **filters)
    answer = generate_answer(user_query, results)

    return {
        "query": user_query,
        "answer": answer,
        "sources": results,
    }


# =========================
# DEBUG
# =========================
def ask_agent(query, **filters):
    result = agentic_search(query, **filters)

    print("\n🤖 RÉPONSE DE L'AGENT\n")
    print(result["answer"])

    print("\n📚 SOURCES UTILISÉES\n")
    for r in result["sources"][:5]:
        print(f"  - {r['file']} (score: {r['score']}, section: {r['section']})")

    return result