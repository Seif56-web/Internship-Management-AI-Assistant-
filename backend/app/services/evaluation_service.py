from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.evaluation import Evaluation
from app.models.stagiaire import Stagiaire
from app.models.user import User


async def get_evaluation_by_stagiaire(db: AsyncSession, stagiaire_id: int) -> Evaluation | None:
    result = await db.execute(
        select(Evaluation).where(Evaluation.stagiaire_id == stagiaire_id)
    )
    return result.scalar_one_or_none()


async def create_or_update_evaluation(
    db: AsyncSession,
    stagiaire_id: int,
    current_user: User,
    data: dict,
) -> Evaluation:
    result = await db.execute(select(Stagiaire).where(Stagiaire.id == stagiaire_id))
    stagiaire = result.scalar_one_or_none()
    if not stagiaire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stagiaire introuvable")

    if stagiaire.encadrant_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul l'encadrant affecté à ce stagiaire peut créer ou modifier une évaluation",
        )

    existing = await get_evaluation_by_stagiaire(db, stagiaire_id)

    if existing:
        for key, value in data.items():
            if value is not None:
                setattr(existing, key, value)
        await db.flush()
        await db.refresh(existing)
        return existing
    else:
        evaluation = Evaluation(
            stagiaire_id=stagiaire_id,
            encadrant_id=current_user.id,
            **{k: v for k, v in data.items() if v is not None},
        )
        db.add(evaluation)
        await db.flush()
        await db.refresh(evaluation)
        return evaluation
