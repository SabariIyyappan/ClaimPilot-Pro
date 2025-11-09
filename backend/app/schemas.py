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
    patient_id: Optional[str] = None
    amount: Optional[float] = None
    signed_by: Optional[str] = None


class ClaimResponse(BaseModel):
    claim_id: str
    approved: List[CodeSuggestion]
    metadata: dict


class CMS1500Request(BaseModel):
    approved: List[CodeSuggestion]
    text: Optional[str] = None
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    provider_name: Optional[str] = None
    date_of_service: Optional[str] = None
    # Extended optional CMS-1500 fields
    patient_dob: Optional[str] = None
    patient_sex: Optional[str] = None
    patient_address: Optional[str] = None
    place_of_service: Optional[str] = None
    referring_npi: Optional[str] = None
    # Optional diagnosis pointers per procedure row (indices starting at 1)
    diag_pointers: Optional[List[List[int]]] = None
