import re

BAILLEURS = [
    "Banque Mondiale", "World Bank", "BAD", "Banque Africaine de Developpement",
    "PNUD", "UNICEF", "UE", "Union Europeenne", "AFD", "GIZ", "USAID",
    "BID", "FAO", "OMS", "WHO", "FIDA", "BEI", "DGD", "UNFPA"
]

PAYS = [
    "Tunisie", "Tunisia",
    "Sénégal", "Senegal",
    "Mali", "Niger",
    "Burkina Faso",
    "Côte d'Ivoire", "Cote d'Ivoire",
    "Cameroun", "Cameroon",
    "Maroc", "Morocco",
    "Algérie", "Algeria",
    "Madagascar", "RDC", "Congo",
    "Bénin", "Benin", "Togo",
    "Guinée", "Guinea",
    "Rwanda", "Éthiopie", "Ethiopia",
    "Kenya", "Mozambique", "Tanzanie", "Tanzania",
    "Belgique", "Belgium", "France"
]

DOMAINES = [
    "Sante", "Education", "Agriculture", "Environnement", "Gouvernance",
    "Infrastructure", "Finance", "Eau", "Energie", "Numerique", "Social",
    "Securite", "Genre", "Nutrition"
]

def extraire_metadata(text):
    text_lower = text.lower()
    snippet = text[:3000]

    annee = None
    match = re.search(r"\b(20[0-2]\d)\b", snippet)
    if match:
        annee = match.group(1)

    bailleur = None
    for b in BAILLEURS:
        if b.lower() in text_lower[:3000]:
            bailleur = b
            break

    pays = None
    for p in PAYS:
        if p.lower() in text_lower[:3000]:
            pays = p
            break

    domaine = None
    for d in DOMAINES:
        if d.lower() in text_lower[:3000]:
            domaine = d
            break

    return {
        "bailleur": bailleur or "",
        "pays": pays or "",
        "domaine": domaine or "",
        "annee": annee or ""
    }