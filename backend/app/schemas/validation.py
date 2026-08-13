from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ValidationCreate(BaseModel):
    status: str
    commentaire: Optional[str] = None


class ValidationOut(BaseModel):
    id: int
    stagiaire_id: int
    encadrant_id: int
    status: str
    commentaire: Optional[str] = None
    created_at: Optional[datetime] = None
    encadrant_nom: Optional[str] = None

    class Config:
        from_attributes = True
