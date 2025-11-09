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
    for ln in lines:
        low = ln.lower()
        if low.startswith("doctor:") or low.startswith("physician:") or low.startswith("provider:"):
            fields["provider_name"] = ln.split(":", 1)[-1].strip()
        elif low.startswith("patient name:"):
            fields["patient_name"] = ln.split(":", 1)[-1].strip()
        elif low.startswith("patient id:") or low.startswith("mrn:"):
            fields["patient_id"] = ln.split(":", 1)[-1].strip()
        elif low.startswith("date of consultation:") or low.startswith("date of service:") or low.startswith("dos:"):
            fields["date_of_service"] = ln.split(":", 1)[-1].strip()
    return fields


def split_codes(approved: List[Dict]) -> Tuple[List[str], List[Dict]]:
    """Return (diagnoses, procedures) where diagnoses is list of ICD-10 codes
    and procedures is list of CPT entries {code, description}.
    """
    icd: List[str] = []
    cpt: List[Dict] = []
    for c in approved:
        sys = str(c.get("system") or c.get("system", "")).upper()
        if sys.startswith("ICD"):
            code = str(c.get("code", "")).strip()
            if code:
                icd.append(code)
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
                          diagnoses: List[str],
                          procedures: List[Dict]) -> bytes:
    """Create a simplified CMS-1500-like PDF with key fields and codes.
    This is not a full red-form layout but a readable structured export.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter

    y = height - 54
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, "CMS-1500 (Simplified)")
    y -= 24
    c.setFont("Helvetica", 10)
    c.drawString(72, y, f"Patient Name: {patient_name or ''}")
    y -= 14
    c.drawString(72, y, f"Patient ID: {patient_id or ''}")
    y -= 14
    c.drawString(72, y, f"Provider: {provider_name or ''}")
    y -= 14
    c.drawString(72, y, f"Date of Service: {date_of_service or ''}")

    # Diagnoses (Box 21)
    y -= 24
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Box 21 — Diagnoses (ICD-10)")
    y -= 16
    c.setFont("Helvetica", 10)
    if not diagnoses:
        c.drawString(72, y, "None")
        y -= 14
    else:
        for i, dx in enumerate(diagnoses[:12], start=1):
            c.drawString(72, y, f"{i}. {dx}")
            y -= 14

    # Procedures (Box 24)
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, y, "Box 24 — Procedures/Services (CPT)")
    y -= 16
    c.setFont("Helvetica", 10)
    if not procedures:
        c.drawString(72, y, "None")
        y -= 14
    else:
        for p in procedures[:10]:
            c.drawString(72, y, f"{p.get('code','')} — {p.get('description','')[:90]}")
            y -= 14

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

