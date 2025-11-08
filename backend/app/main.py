from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.schemas import UploadRequest, SuggestRequest, SuggestResponse, ClaimRequest, ClaimResponse, Entity, CodeSuggestion
from app.ocr import extract_text_from_image_bytes, extract_text_from_pdf_bytes
from app.ner import extract_entities
from app.code_index import load_codes_from_csv, build_and_save_embeddings
from app.embeddings import embed_texts
from app.retrieval import FaissIndexWrapper
from app.llm_refine import refine
import os
import uuid

app = FastAPI(title="ClaimPilot Coding Agent - Skeleton")


@app.post("/upload")
async def upload(file: UploadFile = File(None), text: str = Form(None)):
    """Accept a file (PDF/image) or plain text. Return extracted text and entities."""
    extracted = ""
    if file is not None:
        content = await file.read()
        if file.filename.lower().endswith('.pdf'):
            extracted = extract_text_from_pdf_bytes(content)
        else:
            extracted = extract_text_from_image_bytes(content)
    if text:
        # prefer provided text if present
        extracted = text

    ents = extract_entities(extracted)
    return {"text": extracted, "entities": ents}


@app.post("/suggest", response_model=SuggestResponse)
def suggest(req: SuggestRequest):
    # 1) extract entities
    ents = extract_entities(req.text)

    # 2) produce embedding for the full text to search codes
    q_emb = embed_texts([req.text])

    # 3) load FAISS index (assumes prebuilt at data/faiss_index.ivf)
    idx = FaissIndexWrapper(index_path="data/faiss.index", desc_path="data/descriptions.npy", meta_path="data/meta.npy")
    try:
        candidates = idx.search(q_emb, top_k=req.top_k)
    except Exception:
        candidates = []

    # 4) call LLM refine
    refined = refine(ents, candidates, top_k=req.top_k)

    # map to response models
    ents_models = [Entity(text=e.get('text',''), label=e.get('label',''), start=e.get('start',0), end=e.get('end',0)) for e in ents]
    suggestions = []
    for r in refined:
        suggestions.append(CodeSuggestion(code=r.get('code',''), system=r.get('system','ICD-10'), description=r.get('description',''), score=float(r.get('score',0.0)), reason=r.get('reason','')))

    return SuggestResponse(entities=ents_models, suggestions=suggestions)


@app.post("/generate_claim", response_model=ClaimResponse)
def generate_claim(req: ClaimRequest):
    # In production we would persist claim metadata to Supabase/Postgres and return an id
    claim_id = str(uuid.uuid4())
    metadata = {"source": "local-skeleton"}
    return ClaimResponse(claim_id=claim_id, approved=req.approved, metadata=metadata)


@app.get("/health")
def health():
    return {"status": "ok"}
