import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
from app.database import get_db
from app.schemas.attestation import AttestationOut
from app.services import attestation_service
from app.services.email_service import send_attestation_email
from app.auth.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.attestation import Attestation
from app.models.stagiaire import Stagiaire
from app.models.status import StatutDossier

router = APIRouter(prefix="/api/attestations", tags=["Attestations"])


@router.get("/{stagiaire_id}/outdated", response_model=bool)
async def is_attestation_outdated(stagiaire_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Stagiaire).where(Stagiaire.id == stagiaire_id))
    stagiaire = result.scalar_one_or_none()
    if not stagiaire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stagiaire introuvable")

    att_result = await db.execute(select(Attestation).where(Attestation.stagiaire_id == stagiaire_id).order_by(Attestation.created_at.desc()).limit(1))
    att = att_result.scalar_one_or_none()
    if not att or not att.data_snapshot:
        return False

    try:
        snapshot = json.loads(att.data_snapshot)
    except (json.JSONDecodeError, TypeError):
        return False

    current = {
        "civilite": stagiaire.civilite,
        "nom_complet": stagiaire.nom_complet,
        "cin": stagiaire.cin,
        "date_debut_stage": str(stagiaire.date_debut_stage) if stagiaire.date_debut_stage else None,
        "date_fin_stage": str(stagiaire.date_fin_stage) if stagiaire.date_fin_stage else None,
        "service": stagiaire.service,
        "encadrant_nom": stagiaire.encadrant_nom,
    }

    return snapshot != current


@router.post("/generate/{stagiaire_id}", response_model=AttestationOut)
async def generate_attestation(stagiaire_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role(UserRole.RH, UserRole.ADMIN))):
    return await attestation_service.generer_attestation(db, stagiaire_id, current_user)


@router.get("/{stagiaire_id}", response_model=List[AttestationOut])
async def get_attestations(stagiaire_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await attestation_service.get_attestations_by_stagiaire(db, stagiaire_id)


@router.get("/download/{attestation_id}")
async def download_attestation(attestation_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Attestation).where(Attestation.id == attestation_id))
    attestation = result.scalar_one_or_none()
    if not attestation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attestation introuvable")
    if not attestation.pdf_url or not os.path.exists(attestation.pdf_url):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier introuvable")
    return FileResponse(attestation.pdf_url, media_type="application/pdf", filename=f"attestation_{attestation.numero_attestation}.pdf")


@router.delete("/{attestation_id}")
async def delete_attestation(attestation_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role(UserRole.RH, UserRole.ADMIN))):
    result = await db.execute(select(Attestation).where(Attestation.id == attestation_id))
    attestation = result.scalar_one_or_none()
    if not attestation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attestation introuvable")
    if attestation.pdf_url and os.path.exists(attestation.pdf_url):
        os.remove(attestation.pdf_url)
    stag_result = await db.execute(select(Stagiaire).where(Stagiaire.id == attestation.stagiaire_id))
    stagiaire = stag_result.scalar_one_or_none()
    if stagiaire and stagiaire.statut_dossier == StatutDossier.ATTESTATION_GENEREE.value:
        stagiaire.statut_dossier = None
    await db.delete(attestation)
    await db.flush()
    return {"detail": "Attestation supprimée avec succès"}


@router.post("/send/{attestation_id}")
async def send_attestation(attestation_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role(UserRole.RH, UserRole.ADMIN))):
    result = await db.execute(select(Attestation).where(Attestation.id == attestation_id))
    attestation = result.scalar_one_or_none()
    if not attestation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attestation introuvable")

    stag_result = await db.execute(select(Stagiaire).where(Stagiaire.id == attestation.stagiaire_id))
    stagiaire = stag_result.scalar_one_or_none()
    if not stagiaire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stagiaire introuvable")

    if not attestation.pdf_url or not os.path.exists(attestation.pdf_url):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Fichier PDF introuvable")

    try:
        await send_attestation_email(
            to_email=stagiaire.email,
            stagiaire_nom_complet=stagiaire.nom_complet,
            attestation_path=attestation.pdf_url,
            attestation_numero=attestation.numero_attestation,
        )
        stagiaire.statut_dossier = StatutDossier.ATTESTATION_ENVOYEE.value
        await db.flush()
        return {"detail": "Attestation envoyée avec succès à l'adresse email du stagiaire."}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erreur lors de l'envoi : {str(e)}")
