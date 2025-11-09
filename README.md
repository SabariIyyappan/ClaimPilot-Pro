# ClaimPilot Pro — AI-Assisted Medical Coding & Claim Generation

ClaimPilot Pro is an end‑to‑end coding assistant that extracts clinical context from notes, suggests ICD‑10 and CPT codes using retrieval + LLM, and generates professional claims (including CMS‑1500 PDFs). It ships with a FastAPI backend, a modern React/TypeScript frontend, and optional blockchain-style verification via deterministic claim hashing.

This README is hackathon‑ready: it covers setup, run, demo workflow, APIs, and packaging.

## What You Get

- AI coding pipeline: NER ➜ retrieval (FAISS) ➜ Gemini LLM refinement ➜ human review
- Clean React UI: upload, review suggestions, approve, sign, and export
- CMS‑1500 PDF generation and basic claim PDF
- Deterministic hash for claim audit logs (non‑PHI)

## Repository Structure

- `backend/` — FastAPI app and ML pipeline
  - `backend/app/main.py` — API endpoints (upload, suggest, claim, cms1500)
  - `backend/app/llm_refine.py` — Gemini prompts and parsing
  - `backend/app/ner.py`, `backend/app/ocr.py` — lightweight NER/OCR helpers
  - `backend/app/code_index.py`, `backend/app/build_index.py` — embeddings + FAISS
  - `backend/app/cms1500.py`, `backend/app/pdfgen.py` — PDF generation
  - `backend/requirements.txt` — pinned backend deps
- `frontend/` — React + Vite + Tailwind + shadcn/ui app
- `data/` — CSVs for ICD‑10 and CPT (`icd10.csv`, `mock_cpt.csv`)
- `Dockerfile` — container for the backend

## Prerequisites

- Python 3.11
- Node.js 18+ and npm
- Optional (OCR): Tesseract OCR and poppler (Linux/Docker already covered). On macOS: `brew install tesseract poppler`. On Windows, install Tesseract from its official installer.
- LLM access (recommended): Google Gemini API key

## Quick Start (Local)

1) Backend setup

```bash
# From repo root
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
```

2) Build the retrieval index (optional but recommended)

Creates `data/descriptions.npy`, `data/meta.npy`, `data/faiss.index` used for retrieval. If you skip this, the system still works in LLM‑only mode.

```bash
# From repo root (ensure venv is active)
python -m backend.app.build_index --icd_csv data/icd10.csv --cpt_csv data/mock_cpt.csv --out_dir data
```

3) Environment variables

- `GEMINI_API_KEY` — required for LLM refinement
- `GEMINI_MODEL` — default `gemini-2.0-flash-exp`
- `SUGGEST_MODE` — `llm` (default) or `hybrid` (retrieval + LLM)
- `CORS_ORIGINS` — CSV of allowed origins for the frontend
- `LLM_DEBUG` — set to `1` for verbose logs

Example (PowerShell):

```powershell
$env:GEMINI_API_KEY = "your_key_here"
$env:SUGGEST_MODE = "llm"
```

4) Run the backend

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

5) Frontend setup and run

```bash
cd frontend
npm install

# Configure the backend URL
echo VITE_API_URL=http://localhost:8000 > .env

npm run dev
# App at http://localhost:5173 (Vite default)
```

## Demo Workflow (Hackathon)

1) Start services
- Backend: `uvicorn backend.app.main:app --reload --port 8000`
- Frontend: `npm run dev` in `frontend/`

2) Walkthrough
- Upload a clinical PDF/image or paste note text
- Review extracted entities
- Click “Get Suggestions” to fetch AI‑proposed ICD‑10/CPT codes
- Approve/edit codes and add an amount and signature
- Click “Generate Claim”
- Download CMS‑1500 PDF (prefilled via `/cms1500/derive`) or basic claim PDF

3) Bonus talking points
- Retrieval on/off: `SUGGEST_MODE=hybrid` uses FAISS candidates prior to LLM
- Audit trail: claim metadata includes a deterministic hash and is logged to `data/claims.jsonl` (non‑PHI)

## API Overview

Base URL: `http://localhost:8000`

- POST `/upload`
  - Form: `file` (PDF/JPG/PNG) or JSON `{ "text": "..." }`
  - Response: `{ text, entities: [{ text, label, start, end }] }`

- POST `/suggest`
  - JSON: `{ "text": "...", "top_k": 5 }`
  - Response: `{ entities, suggestions: [{ code, system, description, score, reason }] }`

- POST `/generate_claim`
  - JSON: `{ approved: [...], amount?, signed_by?, patient_id? }`
  - Response: `{ claim_id, approved, metadata: { hash, source } }`

- POST `/claim_pdf`
  - JSON: `{ approved: [...] }`
  - Response: PDF stream (application/pdf)

- POST `/cms1500`
  - JSON: `{ approved: [...], text?, patient_name?, patient_id?, provider_name?, date_of_service?, ... }`
  - Response: PDF stream (CMS‑1500)

- POST `/cms1500/derive`
  - JSON: `{ text: "..." }`
  - Response: derived fields for the CMS‑1500 dialog

- GET `/config`, GET `/health`

## Docker (Backend)

Build and run the FastAPI backend in Docker:

```bash
docker build -t claimpilot-backend .
docker run -e GEMINI_API_KEY=your_key -p 8000:8000 claimpilot-backend
```

Note: The Dockerfile installs Tesseract and poppler; mount `data/` if you want to persist FAISS or claims: `-v $(pwd)/data:/app/data`.

## Troubleshooting

- 403/CORS in browser: set `CORS_ORIGINS` to include your frontend origin (e.g., `http://localhost:5173`).
- No suggestions returned: ensure `GEMINI_API_KEY` is set; otherwise the system falls back to a minimal heuristic. For hybrid mode, ensure `data/faiss.index` and `data/meta.npy` exist.
- OCR empty text: install Tesseract; scanned PDFs may require poppler for rasterization.

## Security & PHI

This demo is not production‑ready for PHI. Do not submit real patient information. The claim hash and local audit log are designed to avoid storing PHI.

## License

For hackathon/demo purposes only. Add your preferred license if needed.

