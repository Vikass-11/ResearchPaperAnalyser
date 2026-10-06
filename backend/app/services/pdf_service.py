import pymupdf
import os

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts raw text from a PDF file using PyMuPDF."""
    text = ""
    try:
        doc = pymupdf.open(file_path)
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""
