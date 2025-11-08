from typing import List, Optional
from pydantic import BaseModel


class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int


class CodeSuggestion(BaseModel):
    code: str
    system: str  # 'ICD-10' or 'CPT'
    description: str
    score: float
    reason: Optional[str]


class UploadRequest(BaseModel):
    text: Optional[str]


class SuggestRequest(BaseModel):
    text: str
    top_k: int = 5


class SuggestResponse(BaseModel):
    entities: List[Entity]
    suggestions: List[CodeSuggestion]


class ClaimRequest(BaseModel):
    approved: List[CodeSuggestion]
    patient_id: Optional[str]


class ClaimResponse(BaseModel):
    claim_id: str
    approved: List[CodeSuggestion]
    metadata: dict
