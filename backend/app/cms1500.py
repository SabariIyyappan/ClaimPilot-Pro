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
        "patient_dob": "",
        "patient_sex": "",
        "patient_address": "",
        "place_of_service": "",
        "referring_npi": "",
    }
    if not text:
        return fields
    lines = [l.rstrip() for l in text.splitlines()]

    def _find_after_colon(patterns):
        pat = re.compile(r"^(?:\s*(?:" + "|".join(patterns) + r"))\s*:\s*(.+)$", re.IGNORECASE)
        for ln in lines:
            m = pat.match(ln)
            if m:
                return m.group(1).strip()
        return ""

    # Patient name / id / provider commonly appear as "Label: Value"
    fields["patient_name"] = fields["patient_name"] or _find_after_colon(["patient name", "patient's name"]).strip()
    fields["patient_id"] = fields["patient_id"] or _find_after_colon(["patient id", "mrn"]).strip()
    fields["provider_name"] = fields["provider_name"] or _find_after_colon(["doctor", "physician", "provider", "rendering provider name"]).strip()
    fields["referring_npi"] = fields["referring_npi"] or _find_after_colon(["npi", "referring provider npi", "rendering provider npi"]).strip()
    fields["patient_dob"] = fields["patient_dob"] or _find_after_colon(["dob", "date of birth"]).strip()
    fields["patient_sex"] = fields["patient_sex"] or _find_after_colon(["sex", "gender"]).strip()
    # Capture address as a free line after "address:" if present
    fields["patient_address"] = fields["patient_address"] or _find_after_colon(["address", "patient address"]).strip()

    # Date of service – prefer a date token on the same line; fallback to next line
    dos_line = ""
    dos_pat = re.compile(r"^(.*(?:date\(s\) of service|date of service|dos).*)$", re.IGNORECASE)
    for idx, ln in enumerate(lines):
        if dos_pat.search(ln or ""):
            dos_line = ln
            # If no date on this line, try next non-empty line
            nxt = ""
            j = idx + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                nxt = lines[j]
            # Prefer a date token if present
            date_regex = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})\b")
            m = date_regex.search(ln)
            if not m:
                m = date_regex.search(nxt)
            if m:
                fields["date_of_service"] = m.group(0)
            elif nxt:
                # Only accept a next-line value when it looks like a short date-like token
                m2 = date_regex.search(nxt)
                if m2:
                    fields["date_of_service"] = m2.group(0)
            break

    # Place of service
    m_pos = re.search(r"\bPOS\s*(\d{2})\b|place of service\s*:?\s*(\d{2})", text, flags=re.IGNORECASE)
    if m_pos:
        fields["place_of_service"] = (m_pos.group(1) or m_pos.group(2) or "").strip()

    # Final cleanup: drop obviously long paragraphs accidentally captured
    for k in ("patient_name", "patient_id", "provider_name", "date_of_service"):
        v = fields.get(k, "")
        if len(v) > 64:
            fields[k] = v[:64]

    # If patient name not found by label, try to guess "Last, First" or "First Last"
    if not fields["patient_name"]:
        # Common pattern: DOE, JOHN or John A. Doe
        m = re.search(r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
        if m:
            guess = m.group(1).strip()
            # Basic sanitization: letters, spaces, hyphen, apostrophe, comma, period
            guess = re.sub(r"[^A-Za-z\s\-\.',]", "", guess)
            fields["patient_name"] = guess[:64]

    # Ensure DOS is strictly a date token; otherwise leave blank
    if fields["date_of_service"] and not re.match(r"^(\d{4}-\d{2}-\d{2}|\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})$", fields["date_of_service"]):
        fields["date_of_service"] = ""

    # SECOND PASS: scan entire text with regexes for common tokens when labels are missing
    full = text or ""
    # MRN / Patient ID
    m = re.search(r"\b(?:MRN|Patient\s*ID|PID|ID)\s*[:#]?\s*([A-Za-z0-9\-]+)\b", full, flags=re.IGNORECASE)
    if m and not fields["patient_id"]:
        fields["patient_id"] = m.group(1)[:64]
    # DOB
    m = re.search(r"\b(?:DOB|Date\s*of\s*Birth)\s*[:#]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4})\b", full, flags=re.IGNORECASE)
    if m and not fields["patient_dob"]:
        fields["patient_dob"] = m.group(1)
    # Sex / Gender
    m = re.search(r"\b(?:Sex|Gender)\s*[:#]?\s*(Male|Female|M|F)\b", full, flags=re.IGNORECASE)
    if m and not fields["patient_sex"]:
        sx = m.group(1).upper()
        fields["patient_sex"] = "M" if sx.startswith("M") else ("F" if sx.startswith("F") else sx)
    # NPI
    m = re.search(r"\bNPI\s*[:#]?\s*(\d{10})\b", full, flags=re.IGNORECASE)
    if m and not fields["referring_npi"]:
        fields["referring_npi"] = m.group(1)
    # POS
    m = re.search(r"\b(?:POS|Place\s*of\s*Service)\s*[:#]?\s*(\d{2})\b", full, flags=re.IGNORECASE)
    if m and not fields["place_of_service"]:
        fields["place_of_service"] = m.group(1)
    # Provider guess: look for 'Dr. <Name>' when provider_name is empty
    m = re.search(r"\bDr\.\s+([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", full)
    if m and not fields["provider_name"]:
        fields["provider_name"] = f"Dr. {m.group(1)}"[:64]
    # Address heuristic: first line with a street suffix + optional next line with City, ST ZIP
    if not fields["patient_address"]:
        street_re = re.compile(r"\b\d{1,5}\s+.+\b(St|Street|Ave|Avenue|Road|Rd|Blvd|Lane|Ln|Dr|Drive)\b.*", re.IGNORECASE)
        city_re = re.compile(r"^[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b")
        for i, ln in enumerate(lines):
            if street_re.search(ln or ""):
                addr = ln.strip()
                if i + 1 < len(lines) and city_re.search(lines[i + 1] or ""):
                    addr = addr + ", " + lines[i + 1].strip()
                fields["patient_address"] = addr[:128]
                break
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
                          patient_dob: str = "",
                          patient_sex: str = "",
                          patient_address: str = "",
                          place_of_service: str = "",
                          referring_npi: str = "",
                          diagnoses: List[Dict] = None,
                          procedures: List[Dict] = None,
                          diag_pointers: List[List[int]] | None = None) -> bytes:
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

    def wrap_lines(text: str, max_width: float, font: str = "Helvetica", size: int = 10) -> list:
        if not text:
            return []
        c.setFont(font, size)
        words = str(text).split()
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip()
            if c.stringWidth(test, fontName=font, fontSize=size) <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def draw_value_in_box(x1: float, y1: float, x2: float, y2: float, value: str, font: str = "Helvetica", size: int = 10, pad: float = 6.0, max_lines: int = 2):
        if not value:
            return
        avail_w = (x2 - x1) - pad * 2
        lines = wrap_lines(value, avail_w, font, size)[:max_lines]
        c.setFont(font, size)
        ty = y2 - 20
        for ln in lines:
            c.drawString(x1 + pad, ty, ln)
            ty -= (size + 2)

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
    draw_value_in_box(left, y - row_h, left + (right - left) * 0.62, y, patient_name or "")
    draw_value_in_box(left + (right - left) * 0.62, y - row_h, right, y, patient_id or "")

    # Row 2: Provider / DOS / Referring NPI
    y -= row_h + 8
    third = (right - left) / 3
    box(left, y - row_h, left + third * 1.6, y, "3. RENDERING PROVIDER NAME")
    box(left + third * 1.6, y - row_h, left + third * 2.4, y, "4. DATE OF SERVICE (DOS)")
    box(left + third * 2.4, y - row_h, right, y, "17b. REFERRING PROVIDER NPI")
    draw_value_in_box(left, y - row_h, left + third * 1.6, y, provider_name or "")
    draw_value_in_box(left + third * 1.6, y - row_h, left + third * 2.4, y, date_of_service or "", max_lines=1)
    draw_value_in_box(left + third * 2.4, y - row_h, right, y, referring_npi or "", max_lines=1)

    # Row 3: Patient DOB / Sex / Address
    y -= row_h + 8
    box(left, y - row_h, left + third, y, "5. PATIENT DOB")
    box(left + third, y - row_h, left + third * 1.5, y, "6. SEX")
    box(left + third * 1.5, y - row_h, right, y, "7. PATIENT ADDRESS")
    draw_value_in_box(left, y - row_h, left + third, y, patient_dob or "", max_lines=1)
    draw_value_in_box(left + third, y - row_h, left + third * 1.5, y, patient_sex or "", max_lines=1)
    draw_value_in_box(left + third * 1.5, y - row_h, right, y, patient_address or "")

    # Box 21: Diagnoses grid (up to 12)
    y -= row_h + 14
    diag_height = 152
    box(left, y - diag_height, right, y, "21. DIAGNOSES (ICD-10)")
    c.setFont("Helvetica", 9)
    cols = 2
    col_w = (right - left - 12) / cols
    diag = diagnoses[:12] if diagnoses else []
    if diag:
        # Helper to clip a single line to available width
        def clip_text(text: str, width: float) -> str:
            if not text:
                return ""
            if c.stringWidth(text, fontName="Helvetica", fontSize=9) <= width:
                return text
            ell = "…"
            ell_w = c.stringWidth(ell, fontName="Helvetica", fontSize=9)
            out = ""
            for ch in text:
                if c.stringWidth(out + ch, fontName="Helvetica", fontSize=9) + ell_w > width:
                    break
                out += ch
            return out + ell
        for i, item in enumerate(diag):
            code = str(item.get("code", ""))
            dsc = str(item.get("description", ""))
            r = i // cols
            col = i % cols
            xp = left + 6 + col * col_w
            yp = y - 18 - r * 18  # a little more vertical spacing for readability
            label = f"{i+1}. {code}"
            if dsc:
                label += f" – {dsc[:70]}"
            # Clip to the column width to avoid overlapping the next column
            avail = col_w - 10
            c.drawString(xp, yp, clip_text(label, avail))
    else:
        c.drawString(left + 6, y - 18, "No diagnoses provided")

    # Box 24: Procedures/Services table
    y -= diag_height + 14
    table_h = 238
    box(left, y - table_h, right, y, "24. PROCEDURES/SERVICES (CPT)")
    # Column layout approximating CMS-1500 with vertical grid lines
    # Add a touch more inner padding so text doesn't hug borders
    inner_left = left + 8
    inner_right = right - 8
    inner_width = inner_right - inner_left
    headers = [
        ("DATE(S) OF SERVICE", 0.16),
        ("CPT/HCPCS", 0.14),
        ("POS", 0.08),
        ("DESCRIPTION", 0.38),
        ("DIAG PTRS", 0.10),
        ("CHARGES", 0.07),
        ("UNITS", 0.07),
    ]
    # Compute column x positions
    col_edges = [inner_left]
    acc = inner_left
    for _, frac in headers:
        acc += inner_width * frac
        col_edges.append(acc)

    # Header labels
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(form_red)
    for i, (title, _) in enumerate(headers):
        c.drawString(col_edges[i] + 2, y - 14, title)
    c.setFillColor(black)

    # Vertical grid lines
    c.setStrokeColor(form_red)
    grid_top = y - 20  # slightly larger header band
    grid_bottom = y - table_h + 6
    for x in col_edges:
        c.line(x, grid_top, x, grid_bottom)
    c.line(inner_right, grid_top, inner_right, grid_bottom)

    # Horizontal row lines
    row_h_px = 22  # more vertical spacing per service row
    max_rows = 10
    for i in range(max_rows + 1):
        yy = grid_top - i * row_h_px
        c.line(inner_left, yy, inner_right, yy)

    # Fill rows with procedures
    c.setFont("Helvetica", 9)
    def col_x(idx: int) -> float:
        return col_edges[idx] + 2

    def col_w(idx: int) -> float:
        return (col_edges[idx + 1] - col_edges[idx]) - 4

    for i, p in enumerate(procedures[:max_rows]):
        # Baseline for text center-ish within row
        ry = grid_top - i * row_h_px - 12
        # single-line, clipped to each column width
        def clip(text: str, width: float) -> str:
            if not text:
                return ""
            c.setFont("Helvetica", 9)
            if c.stringWidth(text) <= width:
                return text
            ell = "…"
            w = c.stringWidth(ell)
            out = ""
            for ch in text:
                if c.stringWidth(out + ch) + w > width:
                    break
                out += ch
            return out + ell

        c.drawString(col_x(0), ry, clip(date_of_service or "", col_w(0)))
        c.drawString(col_x(1), ry, clip(str(p.get("code", "")), col_w(1)))
        c.drawString(col_x(2), ry, clip(place_of_service or "", col_w(2)))
        c.drawString(col_x(3), ry, clip((p.get("description", "") or ""), col_w(3)))
        # Diagnosis pointers: if provided, use indices like "1,3"; otherwise default to "1"
        ptrs = "1"
        if diag_pointers and i < len(diag_pointers):
            try:
                ptrs = ",".join(str(int(x)) for x in diag_pointers[i] if int(x) >= 1) or "1"
            except Exception:
                ptrs = "1"
        c.drawString(col_x(4), ry, clip(ptrs, col_w(4)))
        # Charges left blank; could be populated when amount per line is provided
        c.drawString(col_x(5), ry, "")
        # Units default to 1
        c.drawString(col_x(6), ry, "1")

    # Footer note
    c.setFont("Helvetica", 7)
    c.setFillColor(form_red)
    c.drawString(left, 42, "This generated document mirrors CMS-1500 structure for preview/print. Not an official red-ink form.")
    c.setFillColor(black)

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

