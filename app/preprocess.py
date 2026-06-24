import os
import re
from pypdf import PdfReader


# =========================
# CLEAN TEXT
# =========================
def clean_text(text):
    text = text.replace("\n", " ")
    text = re.sub(r"\bpage\s*\d+\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"[.\-_]{4,}", " ", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    return " ".join(text.split())


def is_noise_line(line, min_words=4):
    """
    Détecte les lignes probablement non sémantiques :
    tableaux de chiffres, en-têtes répétitifs.
    """
    words = line.split()
    if len(words) < min_words:
        return True
    digit_ratio = sum(c.isdigit() for c in line) / max(len(line), 1)
    if digit_ratio > 0.4:
        return True
    return False


# =========================
# LOAD ONE PDF
# =========================
def load_pdf(file_path):
    reader = PdfReader(file_path)
    lines = []

    for page in reader.pages:
        page_text = page.extract_text()
        if not page_text:
            continue

        for raw_line in page_text.split("\n"):
            line = clean_text(raw_line)
            if line and not is_noise_line(line):
                lines.append(line)

    return " ".join(lines)


# =========================
# LOAD ALL PDFs
# =========================
def load_all_pdfs(folder_path):
    docs = []

    for file in os.listdir(folder_path):
        if file.endswith(".pdf"):
            full_path = os.path.join(folder_path, file)
            try:
                print(f"[LOADING] {file}")
                text = load_pdf(full_path)
                if not text.strip():
                    print(f"[WARNING] EMPTY TEXT (possibly scanned PDF, needs OCR): {file}")
                    continue
                docs.append({"file_name": file, "text": text})
            except Exception as e:
                print(f"[SKIP] {file}")
                print(f"Reason: {e}")

    print(f"\n[LOADED] Total docs: {len(docs)}")
    return docs