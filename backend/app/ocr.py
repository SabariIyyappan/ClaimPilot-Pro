from typing import Optional
import io
from PIL import Image
try:
    import pytesseract
except Exception:
    pytesseract = None


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """Return extracted text from image bytes. If pytesseract not installed, return empty string."""
    if not pytesseract:
        return ""  # fallback empty; pipeline should accept raw text input too
    img = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(img)
    return text


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    # Minimal stub: in production use pdfminer.six or pypdf to extract text reliably
    try:
        from pdfminer.high_level import extract_text
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            path = f.name
        return extract_text(path)
    except Exception:
        return ""
