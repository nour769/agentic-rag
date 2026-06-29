import os
from dotenv import load_dotenv
from groq import Groq
from app.search import search, match_file_in_query, get_all_chunks_for_file, multi_search

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.3-70b-versatile"


def call_llm(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    return response.choices[0].message.content


def generate_answer(user_query, results, max_context_chunks=8):
    """
    Genere une reponse synthetique courte et factuelle.
    """
    if not results:
        return "Cette information n'est pas mentionnee dans le document."

    context_blocks = []
    for r in results[:max_context_chunks]:
        context_blocks.append(r["text"])

    context = "\n\n---\n\n".join(context_blocks)

    prompt = f"""Tu es un assistant qui repond a des questions sur des Termes de Reference (TdR).

Question : "{user_query}"

Extraits du TdR :

{context}

REGLES STRICTES :
- Reponds UNIQUEMENT avec les faits presents dans les extraits ci-dessus.
- Sois direct et factuel. Pas de phrase d'introduction ni de conclusion.
- Si la question porte sur un bareme, des criteres, ou une liste -> utilise une liste a puces claire avec les points/valeurs exacts.
- Si l'information demandee n'est PAS dans les extraits, reponds exactement : "Cette information n'est pas mentionnee dans le document."
- Ne fais AUCUNE supposition, AUCUNE deduction, AUCUNE hypothese.
- Reponds dans la meme langue que la question.

Reponse :"""

    return call_llm(prompt)


def agentic_search(user_query, top_k=5, score_threshold=0.55, **filters):
    """
    Si un fichier est nomme dans la question : recupere TOUS ses chunks,
    genere UNE reponse synthetique, et retourne UNE seule "carte document"
    avec ses metadonnees (pas une liste de chunks numerotes).

    Sinon : recherche semantique classique, deduplique par fichier
    (un seul resultat par document, le meilleur score), limite a top_k documents distincts.
    """
    targeted_file = match_file_in_query(user_query)

    if targeted_file:
        print(f"Fichier cible detecte: {targeted_file}")
        all_chunks = get_all_chunks_for_file(targeted_file)
        answer = generate_answer(user_query, all_chunks)

        best_chunk = all_chunks[0] if all_chunks else {}
        sources = [{
            "file": targeted_file,
            "score": 1.0,
            "domaine": best_chunk.get("domaine"),
            "bailleur": best_chunk.get("bailleur"),
            "pays": best_chunk.get("pays"),
            "region": best_chunk.get("region"),
            "annee": best_chunk.get("annee"),
            "sections_count": len(all_chunks),
        }]

    else:
        raw_results = multi_search(user_query, top_k=top_k * 4, score_threshold=score_threshold, **filters)
        answer = generate_answer(user_query, raw_results)

        # deduplication stricte : un seul resultat par fichier (le meilleur score)
        seen_files = {}
        for r in raw_results:
            f = r["file"]
            if f not in seen_files or r["score"] > seen_files[f]["score"]:
                seen_files[f] = r

        deduped = sorted(seen_files.values(), key=lambda x: x["score"], reverse=True)[:top_k]

        sources = [{
            "file": r["file"],
            "score": r["score"],
            "domaine": r.get("domaine"),
            "bailleur": r.get("bailleur"),
            "pays": r.get("pays"),
            "region": r.get("region"),
            "annee": r.get("annee"),
            "sections_count": 1,
        } for r in deduped]

    return {
        "query": user_query,
        "answer": answer,
        "sources": sources,
        "targeted_file": targeted_file,
    }


def ask_agent(query, **filters):
    result = agentic_search(query, **filters)
    print("\nREPONSE\n")
    print(result["answer"])
    print("\nSOURCES\n")
    for s in result["sources"]:
        print(f"  - {s['file']} ({s['score']})")
    return result