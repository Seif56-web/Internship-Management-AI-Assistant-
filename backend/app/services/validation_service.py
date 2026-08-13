from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.stagiaire import Stagiaire
from app.models.status import StatutStage
from app.models.validation import Validation, StatutValidation
from app.models.user import User
from fastapi import HTTPException, status


async def valider_stage(
    db: AsyncSession,
    stagiaire_id: int,
    current_user,
    validation_status: str,
    commentaire: Optional[str] = None,
) -> Validation:
    stagiaire_result = await db.execute(select(Stagiaire).where(Stagiaire.id == stagiaire_id))
    stagiaire = stagiaire_result.scalar_one_or_none()
    if not stagiaire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stagiaire introuvable")

    current_statut = stagiaire.statut_stage
    if isinstance(current_statut, str):
        try:
            current_statut = StatutStage(current_statut)
        except ValueError:
            pass

    if validation_status == "valide":
        if current_statut not in (StatutStage.STAGE_EN_COURS, StatutStage.STAGE_SUSPENDU):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La validation du stage ne peut être effectuée que si le stage est en cours ou suspendu. Statut actuel : {stagiaire.statut_stage}",
            )
        stagiaire.statut_stage = StatutStage.STAGE_VALIDE.value
        validation = Validation(
            stagiaire_id=stagiaire_id,
            encadrant_id=current_user.id,
            status=validation_status,
            commentaire=commentaire,
        )
        db.add(validation)

    elif validation_status == "refuse":
        if current_statut not in (StatutStage.STAGE_EN_COURS, StatutStage.STAGE_SUSPENDU):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Le refus du stage ne peut être effectué que si le stage est en cours ou suspendu. Statut actuel : {stagiaire.statut_stage}",
            )
        stagiaire.statut_stage = StatutStage.STAGE_REFUSE.value
        validation = Validation(
            stagiaire_id=stagiaire_id,
            encadrant_id=current_user.id,
            status=validation_status,
            commentaire=commentaire,
        )
        db.add(validation)

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Statut de validation invalide. Valeurs autorisées : 'valide', 'refuse'")

    await db.flush()
    await db.refresh(validation)
    return validation


async def get_validations_by_stagiaire(db: AsyncSession, stagiaire_id: int):
    result = await db.execute(
        select(Validation)
        .where(Validation.stagiaire_id == stagiaire_id)
        .order_by(Validation.created_at.desc())
    )
    validations = result.scalars().all()

    output = []
    for v in validations:
        enc_result = await db.execute(select(User).where(User.id == v.encadrant_id))
        enc = enc_result.scalar_one_or_none()
        output.append({
            "id": v.id,
            "stagiaire_id": v.stagiaire_id,
            "encadrant_id": v.encadrant_id,
            "status": v.status.value if hasattr(v.status, 'value') else v.status,
            "commentaire": v.commentaire,
            "created_at": v.created_at,
            "encadrant_nom": f"{enc.prenom} {enc.nom}" if enc else None,
        })
    return output
