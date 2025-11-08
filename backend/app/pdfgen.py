from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io


def generate_claim_pdf(claim_id: str, approved_codes: list) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(72, 720, f"Claim ID: {claim_id}")
    y = 700
    for code in approved_codes:
        c.drawString(72, y, f"{code.get('code')} - {code.get('description')}")
        y -= 18
    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
