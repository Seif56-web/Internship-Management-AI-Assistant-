from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class EvaluationCreate(BaseModel):
    qualite_travail: Optional[int] = None
    autonomie: Optional[int] = None
    ponctualite: Optional[int] = None
    communication: Optional[int] = None
    esprit_equipe: Optional[int] = None
    capacite_apprentissage: Optional[int] = None
    initiative: Optional[int] = None
    respect_consignes: Optional[int] = None
    recommandation_embauche: Optional[str] = None
    commentaire: Optional[str] = None

    @field_validator("qualite_travail", "autonomie", "ponctualite", "communication",
                     "esprit_equipe", "capacite_apprentissage", "initiative", "respect_consignes",
                     mode="before")
    @classmethod
    def validate_note(cls, v):
        if v is not None and (not isinstance(v, int) or v < 1 or v > 5):
            raise ValueError("La note doit être comprise entre 1 et 5")
        return v

    @field_validator("recommandation_embauche", mode="before")
    @classmethod
    def validate_recommandation(cls, v):
        if v is not None and v not in ("oui", "non", "a_considerer"):
            raise ValueError("La recommandation doit être 'oui', 'non' ou 'a_considerer'")
        return v


class EvaluationOut(BaseModel):
    id: int
    stagiaire_id: int
    encadrant_id: int
    qualite_travail: Optional[int] = None
    autonomie: Optional[int] = None
    ponctualite: Optional[int] = None
    communication: Optional[int] = None
    esprit_equipe: Optional[int] = None
    capacite_apprentissage: Optional[int] = None
    initiative: Optional[int] = None
    respect_consignes: Optional[int] = None
    recommandation_embauche: Optional[str] = None
    commentaire: Optional[str] = None
    date_creation: Optional[datetime] = None
    date_modification: Optional[datetime] = None
    encadrant_nom: Optional[str] = None

    class Config:
        from_attributes = True
