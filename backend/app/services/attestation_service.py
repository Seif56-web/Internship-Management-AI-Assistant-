import os
import json
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.stagiaire import Stagiaire
from app.models.status import StatutStage, StatutDossier
from app.models.attestation import Attestation
from app.utils.pdf_generator import generer_attestation_pdf
from app.config import settings
from fastapi import HTTPException, status


async def generer_attestation(
    db: AsyncSession,
    stagiaire_id: int,
    current_user,
) -> Attestation:
    result = await db.execute(select(Stagiaire).where(Stagiaire.id == stagiaire_id))
    stagiaire = result.scalar_one_or_none()

    if not stagiaire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stagiaire introuvable")

    snapshot = json.dumps({
        "civilite": stagiaire.civilite,
        "nom_complet": stagiaire.nom_complet,
        "cin": stagiaire.cin,
        "date_debut_stage": str(stagiaire.date_debut_stage) if stagiaire.date_debut_stage else None,
        "date_fin_stage": str(stagiaire.date_fin_stage) if stagiaire.date_fin_stage else None,
        "service": stagiaire.service,
        "encadrant_nom": stagiaire.encadrant_nom,
    })

    max_result = await db.execute(select(Attestation.numero_attestation).order_by(Attestation.id.desc()).limit(1))
    last_numero = max_result.scalar_one_or_none()
    if last_numero:
        try:
            num = int(last_numero.split("-")[-1]) + 1
        except (ValueError, IndexError):
            num = 1
        prefix = last_numero.rsplit("-", 1)[0]
        numero = f"{prefix}-{num:04d}"
    else:
        numero = f"ATT-{datetime.now(timezone.utc).strftime('%Y%m')}-0001"

    old_result = await db.execute(select(Attestation).where(Attestation.stagiaire_id == stagiaire_id).order_by(Attestation.created_at.desc()).limit(1))
    old_attestation = old_result.scalar_one_or_none()

    if old_attestation and old_attestation.pdf_url and os.path.exists(old_attestation.pdf_url):
        os.remove(old_attestation.pdf_url)
    if old_attestation:
        await db.delete(old_attestation)
        await db.flush()

    os.makedirs(settings.ATTESTATION_DIR, exist_ok=True)
    filepath = os.path.join(settings.ATTESTATION_DIR, f"attestation_{stagiaire_id}_{numero}.pdf")
    await asyncio.to_thread(generer_attestation_pdf, stagiaire, numero, filepath, current_user={"nom": current_user.nom, "prenom": current_user.prenom})

    attestation = Attestation(
        stagiaire_id=stagiaire_id,
        numero_attestation=numero,
        generated_by=current_user.id,
        pdf_url=filepath,
        data_snapshot=snapshot,
    )
    db.add(attestation)

    stagiaire.statut_dossier = StatutDossier.ATTESTATION_GENEREE.value
    await db.flush()
    await db.refresh(attestation)
    return attestation


async def get_attestations_by_stagiaire(db: AsyncSession, stagiaire_id: int):
    result = await db.execute(
        select(Attestation).where(Attestation.stagiaire_id == stagiaire_id)
    )
    return result.scalars().all()
