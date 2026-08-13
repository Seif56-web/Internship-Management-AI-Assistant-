from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RapportOut(BaseModel):
    id: int
    stagiaire_id: int
    file_pdf: str
    uploaded_by: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
