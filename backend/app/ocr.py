from typing import Optional
import io
from PIL import Image
try:
    import pytesseract
except Exception:
    pytesseract = None

# Optional: use pdf2image to OCR scanned PDFs when text extraction fails
try:
    from pdf2image import convert_from_bytes  # type: ignore
except Exception:
    convert_from_bytes = None  # type: ignore


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """Return extracted text from image bytes. If pytesseract not installed, return empty string."""
    if not pytesseract:
        return ""  # fallback empty; pipeline should accept raw text input too
    img = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(img)
    return text


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from a PDF.

    Strategy:
    1) Try pdfminer text extraction (works for text-based PDFs)
    2) If empty/very short and pdf2image + pytesseract are available, rasterize
       pages and OCR each page, then join.
    """
    text = ""
    try:
        from pdfminer.high_level import extract_text
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            path = f.name
        text = extract_text(path) or ""
    except Exception:
        text = ""

    # Fallback to OCR for scanned PDFs
    if (not text or len(text.strip()) < 20) and convert_from_bytes and pytesseract:
        try:
            # Render pages at a reasonable DPI for OCR quality/speed tradeoff
            pages = convert_from_bytes(pdf_bytes, dpi=200)
            ocr_chunks = []
            for pg in pages:
                try:
                    ocr_chunks.append(pytesseract.image_to_string(pg))
                except Exception:
                    continue
            text = "\n".join([t for t in ocr_chunks if t and t.strip()])
        except Exception:
            pass
    return text or ""


def extract_clinical_note_section(text: str) -> str:
    """Heuristically slice out the 'Clinical Note' section only.

    Strategy:
    - Find the first occurrence of 'Clinical Note' (or 'Clinical Notes')
    - Cut until the next known header (e.g., 'Recommendations', 'Follow-Up', 'Assessment', 'Plan', 'Medications', etc.)
    - If not found, return original text.
    """
    if not text:
        return text
    t = text.replace("\r", "")
    low = t.lower()
    # Start header
    start = low.find("clinical note")
    if start == -1:
        start = low.find("clinical notes")
    if start == -1:
        return text

    # Candidate end headers
    headers = [
        "recommendations and follow-up",
        "recommendations",
        "follow-up",
        "assessment",
        "plan",
        "medications",
        "final diagnoses",
        "diagnoses",
        "discharge instructions",
        "department",
        "signature",
    ]
    next_positions = []
    for h in headers:
        idx = low.find(h, start + 1)
        if idx != -1:
            next_positions.append(idx)
    end = min(next_positions) if next_positions else len(t)

    section = t[start:end]
    # Drop the header line itself
    lines = section.splitlines()
    drop_idx = 0
    for i, line in enumerate(lines):
        if "clinical note" in line.lower():
            drop_idx = i + 1
            break
    body = "\n".join(lines[drop_idx:]).strip()
    return body or section.strip()
