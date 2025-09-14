import pdfplumber
import docx
import os

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text.strip()

def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text.strip()

def save_clean_text(file_path: str, output_dir: str = "../data/clean/") -> str:
    """
    Extracts text from PDF/DOCX and saves it to the clean folder.
    Returns the path of the saved text file.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext == ".docx":
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Save with same filename but .txt
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    clean_path = os.path.join(output_dir, f"{base_name}.txt")

    with open(clean_path, "w", encoding="utf-8") as f:
        f.write(text)

    return clean_path
