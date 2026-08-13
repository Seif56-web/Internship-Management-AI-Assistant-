from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime


class StagiaireCreate(BaseModel):
    nom_complet: Optional[str] = None
    lettre_affectation: Optional[bool] = False
    civilite: Optional[str] = None
    service: Optional[str] = None
    date_naissance: Optional[date] = None
    cin: Optional[str] = None
    country_code: Optional[str] = "+216"
    telephone: Optional[str] = None
    email: Optional[str] = None
    ecole: Optional[str] = None
    taille: Optional[int] = None
    pointure: Optional[int] = None
    date_debut_stage: Optional[date] = None
    date_fin_stage: Optional[date] = None
    periode_stage: Optional[str] = None
    encadrant_nom: Optional[str] = None
    encadrant_id: Optional[int] = None


class StagiaireUpdate(BaseModel):
    nom_complet: Optional[str] = None
    lettre_affectation: Optional[bool] = None
    civilite: Optional[str] = None
    service: Optional[str] = None
    date_naissance: Optional[date] = None
    cin: Optional[str] = None
    country_code: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[EmailStr] = None
    ecole: Optional[str] = None
    taille: Optional[int] = None
    pointure: Optional[int] = None
    date_debut_stage: Optional[date] = None
    date_fin_stage: Optional[date] = None
    periode_stage: Optional[str] = None
    encadrant_nom: Optional[str] = None
    encadrant_id: Optional[int] = None


class StagiaireOut(BaseModel):
    id: int
    nom_complet: Optional[str] = None
    lettre_affectation: bool = False
    civilite: Optional[str] = None
    service: Optional[str] = None
    date_naissance: Optional[date] = None
    cin: Optional[str] = None
    country_code: Optional[str] = None
    telephone: Optional[str] = None
    email: Optional[str] = None
    ecole: Optional[str] = None
    taille: Optional[int] = None
    pointure: Optional[int] = None
    date_debut_stage: Optional[date] = None
    date_fin_stage: Optional[date] = None
    periode_stage: Optional[str] = None
    statut_stage: str
    statut_dossier: Optional[str] = None
    is_extended: bool = False
    old_date_fin_stage: Optional[date] = None
    date_prolongation: Optional[datetime] = None
    suspended_at: Optional[datetime] = None
    resumed_at: Optional[datetime] = None
    encadrant_nom: Optional[str] = None
    encadrant_id: Optional[int] = None
    attestation_id: Optional[int] = None
    attestation_numero: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StagiaireDetail(StagiaireOut):
    rapports: list = []
    validations: list = []
    attestations: list = []
