from pypdf import PdfReader
from pypdf.errors import PdfStreamError
import os


# -----------------------------
# 1. Lire un seul PDF
# -----------------------------
def load_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        return text

    except Exception as e:
        print(f"[SKIP] CORRUPTED FILE: {file_path}")
        print(f"   Reason: {e}")
        return ""


# -----------------------------
# 2. Lire tous les PDFs d'un dossier
# -----------------------------
def load_all_pdfs(folder_path):
    documents = []

    if not os.path.exists(folder_path):
        print(f"[ERROR] Folder not found: {folder_path}")
        return documents

    for file in os.listdir(folder_path):

        if file.endswith(".pdf"):
            full_path = os.path.join(folder_path, file)

            print(f"[LOADING] {file}")

            text = load_pdf(full_path)

            # ignorer fichiers vides ou cassés
            if not text.strip():
                continue

            documents.append({
                "file_name": file,
                "text": text
            })

    return documents


# -----------------------------
# 3. MAIN
# -----------------------------
if __name__ == "__main__":

    # chemin robuste (important)
    base_dir = os.path.dirname(__file__)
    folder = os.path.abspath(os.path.join(base_dir, "..", "data", "tdrs"))

    docs = load_all_pdfs(folder)

    print("\n========================")
    print("[OK] TOTAL DOCUMENTS:", len(docs))
    print("========================\n")

    if len(docs) > 0:
        print("[INFO] SAMPLE FILE:", docs[0]["file_name"])
        print("\n--- TEXT PREVIEW ---\n")
        print(docs[0]["text"][:1000])