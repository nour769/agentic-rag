from pypdf import PdfReader
import pytesseract
from pdf2image import convert_from_path
import os
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Nour Mrabet\Desktop\2ème année ensi\stage EY\tesseract.exe"
POPPLER_PATH = r"C:\Users\Nour Mrabet\Desktop\2ème année ensi\stage EY\popller\poppler-26.02.0\Library\bin"
NOMS_A_IGNORER = ["report", "progress", "replacement", "slides", "results"]


def est_tdr(file_name, text):
    """
    Verifie si le document est bien un TdR.
    Retourne False si le nom du fichier contient des mots suspects
    ou si le document est anormalement long.
    """
    nom = file_name.lower()
    if any(mot in nom for mot in NOMS_A_IGNORER):
        return False
    if len(text.split()) > 50000:
        return False
    return True


def load_pdf(file_path):
    """
    Lit un PDF normal (avec du vrai texte).
    Retourne le texte brut de toutes les pages, page par page,
    separees par un marqueur clair pour faciliter le diagnostic.
    """
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        print(f"[SKIP CORRUPTED FILE] {file_path} -- {e}")
        return ""


def load_pdf_ocr(file_path):
    """
    Pour les PDFs scannes (images).
    Convertit chaque page en image puis lit avec Tesseract.
    """
    try:
        print(f"   [OCR] en cours: {os.path.basename(file_path)}")
        images = convert_from_path(file_path, dpi=300, poppler_path=POPPLER_PATH)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img, lang="fra+eng") + "\n"
        return text
    except Exception as e:
        print(f"[OCR FAILED] {file_path} -- {e}")
        return ""


def load_all_pdfs(folder_path):
    """
    Charge tous les PDFs d'un dossier.
    Pour chaque PDF :
      1. Essaie de lire le texte normalement
      2. Si trop peu de texte -> active l'OCR
      3. Verifie que c'est bien un TdR
      4. Ajoute au resultat
    """
    documents = []

    if not os.path.exists(folder_path):
        print(f"[ERROR] Dossier introuvable: {folder_path}")
        return documents

    all_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    total = len(all_files)
    print(f"{total} PDFs trouves dans {folder_path}\n")

    for i, file in enumerate(all_files):
        full_path = os.path.join(folder_path, file)
        print(f"[{i+1}/{total}] {file}")

        text = load_pdf(full_path)

        if len(text.split()) < 50:
            print(f"   [INFO] Peu/pas de texte -> OCR active")
            text = load_pdf_ocr(full_path)

        if not text.strip():
            print(f"   [SKIP] Aucun texte extrait (meme apres OCR)")
            continue

        if not est_tdr(file, text):
            print(f"   [SKIP] Hors perimetre TdR (nom suspect ou trop long)")
            continue

        documents.append({
            "file_name": file,
            "text": text
        })
        print(f"   [OK] Charge ({len(text.split())} mots)")

    print(f"\nTOTAL: {len(documents)} / {total} documents charges")
    return documents


# =========================
# OUTIL DE DIAGNOSTIC — pour inspecter l'extraction d'un fichier precis
# =========================
def diagnostic_extraction(file_name, keyword=None, output_file="extraction_test.txt"):
    """
    Extrait le texte brut d'un PDF (sans OCR, sans filtrage) page par page,
    et l'ecrit dans un fichier pour inspection manuelle.
    Si 'keyword' est fourni, n'affiche/ecrit que les pages contenant ce mot
    (insensible a la casse) — utile pour localiser rapidement un tableau
    contenant un terme connu (ex: "evaluation", "budget", "calendrier").
    """
    base_dir = os.path.dirname(__file__)
    folder = os.path.abspath(os.path.join(base_dir, "..", "data", "tdrs"))
    full_path = os.path.join(folder, file_name)

    if not os.path.exists(full_path):
        print(f"[ERROR] Fichier introuvable: {full_path}")
        return

    reader = PdfReader(full_path)
    output_lines = []

    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if keyword and keyword.lower() not in page_text.lower():
            continue
        output_lines.append(f"=== PAGE {i + 1} ===")
        output_lines.append(page_text)
        output_lines.append("")

    result = "\n".join(output_lines)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"[OK] Extraction ecrite dans {output_file}")
    print(f"Apercu (500 premiers caracteres):\n")
    print(result[:500])


if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    folder = os.path.abspath(os.path.join(base_dir, "..", "data", "tdrs"))
    docs = load_all_pdfs(folder)
    if docs:
        print(f"\nSAMPLE: {docs[0]['file_name']}")
        print(docs[0]["text"][:500])