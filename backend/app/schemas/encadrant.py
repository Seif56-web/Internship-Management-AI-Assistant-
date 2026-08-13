from pydantic import BaseModel
from typing import Optional


class EncadrantCreate(BaseModel):
    user_id: int
    nom: str
    prenom: str


class EncadrantCreateByRH(BaseModel):
    nom: str
    prenom: str
    email: Optional[str] = None


class EncadrantOut(BaseModel):
    id: int
    code_encadrant: str
    user_id: int
    nom: str
    prenom: str

    class Config:
        from_attributes = True
