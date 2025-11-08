# ClaimPilot — Clinical coding assistant (skeleton)

This repository contains a minimal skeleton for a clinical coding agent (NER → semantic match → LLM refinement → human review) built with FastAPI, spaCy, sentence-transformers, FAISS, and OpenAI.

Folder structure (created):

- backend/app — FastAPI app and pipeline modules
- data — sample `icd10.csv` and `mock_cpt.csv`

Quick setup (macOS — zsh)

Prerequisites

- Xcode command-line tools (clang) — required to build some packages:

```bash
xcode-select --install
```

- Homebrew (we use it here to install a compatible Python 3.11):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Create a Python 3.11 virtual environment and install dependencies

The project expects a venv at the repository root named `.venv`. The commands below create that venv using Homebrew's Python 3.11, upgrade pip, and install the pinned requirements in `backend/requirements.txt`.

```bash
# install Python 3.11 via Homebrew (if not already installed)
brew install python@3.11
PY311="$(brew --prefix python@3.11)/bin/python3.11"

# recreate and activate the venv
rm -rf .venv
$PY311 -m venv .venv
source .venv/bin/activate

# upgrade packaging tools and install deps
python -m pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
```

If you'd prefer to use the official python.org installer instead of Homebrew, install Python 3.11 from https://www.python.org/downloads/mac-osx/ and replace `$PY311` above with the path to that interpreter.

Optional: download spaCy model

```bash
python -m spacy download en_core_web_sm
```

Run the app (zsh)

```bash
export OPENAI_API_KEY=your_key_here
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
