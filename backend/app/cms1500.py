from typing import List, Dict, Tuple
import io
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def parse_header_info(text: str) -> Dict[str, str]:
    """Parse simple header fields from the document text.
    Looks for lines like:
      Doctor: <name>
      Patient Name: <name>
      Patient ID: <id>
      Date of Consultation: <date>
      Date of Service: <date>
    Returns dict with keys: provider_name, patient_name, patient_id, date_of_service
    """
    fields = {
        "provider_name": "",
        "patient_name": "",
        "patient_id": "",
        "date_of_service": "",
    }
    if not text:
        return fields
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for i, ln in enumerate(lines):
        low = ln.lower()
        # Free-text style
        if low.startswith("doctor:") or low.startswith("physician:") or low.startswith("provider:"):
            fields["provider_name"] = ln.split(":", 1)[-1].strip()
        elif low.startswith("patient name:") or "patient's name" in low:
            # Either after colon or next non-empty line
            if ":" in ln:
                fields["patient_name"] = ln.split(":", 1)[-1].strip()
            elif i + 1 < len(lines):
                fields["patient_name"] = lines[i + 1].strip()
        elif low.startswith("patient id:") or low.startswith("mrn:") or "patient id" in low:
            if ":" in ln:
                fields["patient_id"] = ln.split(":", 1)[-1].strip()
            elif i + 1 < len(lines):
                fields["patient_id"] = lines[i + 1].strip()
        elif any(k in low for k in ["date of consultation", "date of service", "dos", "date(s) of service"]):
            if ":" in ln:
                fields["date_of_service"] = ln.split(":", 1)[-1].strip()
            elif i + 1 < len(lines):
                # Attempt to capture a date-like token on the next line
                nxt = lines[i + 1].strip()
                m = re.search(r"\b(\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}|\d{4}-\d{2}-\d{2})\b", nxt)
                fields["date_of_service"] = m.group(0) if m else nxt
        # CMS-1500 specific cues that may have value in the following line
        elif low.startswith("rendering provider") or "provider name" in low:
            if ":" in ln:
                fields["provider_name"] = ln.split(":", 1)[-1].strip()
            elif i + 1 < len(lines):
                fields["provider_name"] = lines[i + 1].strip()
    return fields


def split_codes(approved: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Return (diagnoses, procedures)
    - diagnoses: list of {code, description}
    - procedures: list of {code, description}
    """
    icd: List[Dict] = []
    cpt: List[Dict] = []
    for c in approved:
        sys = str(c.get("system") or c.get("system", "")).upper()
        if sys.startswith("ICD"):
            code = str(c.get("code", "")).strip()
            desc = str(c.get("description", "")).strip()
            if code:
                icd.append({"code": code, "description": desc})
        elif sys.startswith("CPT"):
            cpt.append({
                "code": str(c.get("code", "")).strip(),
                "description": str(c.get("description", "")).strip(),
            })
    return icd, cpt


def generate_cms1500_pdf(patient_name: str,
                          patient_id: str,
                          provider_name: str,
                          date_of_service: str,
                          diagnoses: List[Dict],
                          procedures: List[Dict]) -> bytes:
    """Create a CMS-1500-style PDF with boxed layout and neat presentation.
    This is not the official red-ink OCR form, but closely mirrors its structure
    with labeled boxes and a table for services.
    """
    from reportlab.lib import colors

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter

    # Colors and metrics
    form_red = colors.Color(0.75, 0.0, 0.0)  # soft red lines similar to CMS-1500
    black = colors.black
    left = 36
    right = width - 36
    top = height - 36

    def box(x1, y1, x2, y2, label: str = ""):
        c.setStrokeColor(form_red)
        c.rect(x1, y1, x2 - x1, y2 - y1, stroke=1, fill=0)
        if label:
            c.setFont("Helvetica-Bold", 7)
            c.setFillColor(form_red)
            c.drawString(x1 + 3, y2 - 9, label)
            c.setFillColor(black)

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(black)
    c.drawString(left, top, "CMS-1500 Health Insurance Claim (Preview)")

    y = top - 18
    row_h = 44
    # Row 1: Patient / Patient ID
    box(left, y - row_h, left + (right - left) * 0.62, y, "1. PATIENT'S NAME (Last, First)")
    box(left + (right - left) * 0.62, y - row_h, right, y, "2. PATIENT ID")
    c.setFont("Helvetica", 10)
    c.drawString(left + 6, y - 24, patient_name or "")
    c.drawString(left + (right - left) * 0.62 + 6, y - 24, patient_id or "")

    # Row 2: Provider / DOS
    y -= row_h + 8
    box(left, y - row_h, left + (right - left) * 0.62, y, "3. RENDERING PROVIDER NAME")
    box(left + (right - left) * 0.62, y - row_h, right, y, "4. DATE OF SERVICE (DOS)")
    c.drawString(left + 6, y - 24, provider_name or "")
    c.drawString(left + (right - left) * 0.62 + 6, y - 24, date_of_service or "")

    # Box 21: Diagnoses grid (up to 12)
    y -= row_h + 14
    diag_height = 152
    box(left, y - diag_height, right, y, "21. DIAGNOSES (ICD-10)")
    c.setFont("Helvetica", 9)
    cols = 2
    col_w = (right - left - 12) / cols
    diag = diagnoses[:12] if diagnoses else []
    if diag:
        for i, item in enumerate(diag):
            code = str(item.get("code", ""))
            dsc = str(item.get("description", ""))
            r = i // cols
            col = i % cols
            xp = left + 6 + col * col_w
            yp = y - 18 - r * 16
            label = f"{i+1}. {code}"
            if dsc:
                label += f" – {dsc[:70]}"
            c.drawString(xp, yp, label)
    else:
        c.drawString(left + 6, y - 18, "No diagnoses provided")

    # Box 24: Procedures/Services table
    y -= diag_height + 14
    table_h = 238
    box(left, y - table_h, right, y, "24. PROCEDURES/SERVICES (CPT)")
    # Column layout approximating CMS-1500
    headers = [
        ("DATE(S) OF SERVICE", 0.18),
        ("CPT/HCPCS", 0.16),
        ("DESCRIPTION", 0.46),
        ("CHARGES", 0.10),
        ("UNITS", 0.10),
    ]
    c.setFont("Helvetica-Bold", 8)
    x = left + 6
    for title, frac in headers:
        c.setFillColor(form_red)
        c.drawString(x, y - 14, title)
        c.setFillColor(black)
        x += (right - left - 12) * frac

    # Draw row lines
    c.setStrokeColor(form_red)
    row_y = y - 22
    row_h_px = 18
    max_rows = 10
    for i in range(max_rows):
        c.line(left, row_y - i * row_h_px, right, row_y - i * row_h_px)

    # Fill rows with procedures
    c.setFont("Helvetica", 9)
    def col_x(idx: int) -> float:
        xp = left + 6
        for j in range(idx):
            xp += (right - left - 12) * headers[j][1]
        return xp

    for i, p in enumerate(procedures[:max_rows]):
        ry = row_y - i * row_h_px - 12
        c.drawString(col_x(0), ry, date_of_service or "")
        c.drawString(col_x(1), ry, str(p.get("code", "")))
        c.drawString(col_x(2), ry, (p.get("description", "") or "")[:85])
        c.drawString(col_x(3), ry, "")  # charges left blank for payer
        c.drawString(col_x(4), ry, "1")

    # Footer note
    c.setFont("Helvetica", 7)
    c.setFillColor(form_red)
    c.drawString(left, 42, "This generated document mirrors CMS-1500 structure for preview/print. Not an official red-ink form.")
    c.setFillColor(black)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

