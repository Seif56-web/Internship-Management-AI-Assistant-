from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AttestationOut(BaseModel):
    id: int
    stagiaire_id: int
    numero_attestation: str
    generated_by: int
    pdf_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttestationGenerate(BaseModel):
    confirm: bool = True
