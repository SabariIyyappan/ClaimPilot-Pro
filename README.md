# ClaimPilot — Clinical coding assistant (skeleton)

This repository contains a minimal skeleton for a clinical coding agent (NER → semantic match → LLM refinement → human review) built with FastAPI, spaCy, sentence-transformers, FAISS, and OpenAI.

Folder structure (created):

- backend/app — FastAPI app and pipeline modules
- data — sample `icd10.csv` and `mock_cpt.csv`

Quick setup (Windows CMD):

1. Create virtualenv and install deps

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
```

2. Optional: download spaCy model

```cmd
python -m spacy download en_core_web_sm
```

3. Run the app

```cmd
set OPENAI_API_KEY=your_key_here
uvicorn backend.app.main:app --reload --port 8000
```

API endpoints (skeleton):

- POST /upload — form-data: `file` (PDF/image) or `text` field. Returns extracted text and entities.
- POST /suggest — JSON: {"text": "...", "top_k": 5}. Returns entities and suggestions.
- POST /generate_claim — JSON: {approved: [...]}. Returns claim id and metadata.

Testing locally (end-to-end):

Run uvicorn then use curl or HTTP client to POST to `/suggest`:

```cmd
curl -X POST "http://127.0.0.1:8000/suggest" -H "Content-Type: application/json" -d "{\"text\": \"Patient with type 2 diabetes and hypertension.\"}"
```

Prompt template (LLM refinement) is in `backend/app/llm_refine.py`. The code uses `OPENAI_API_KEY` and `OPENAI_MODEL` environment variables.

Next steps (high priority):

- Build embeddings for `data/icd10.csv` and `data/mock_cpt.csv` and write FAISS index files in `data/`.
- Improve NER by installing medSpaCy or clinical spaCy models and mapping entity labels to coding categories.
- Add persistence layer (Supabase/Postgres) for audit logs and human approvals.
