import os
import aiofiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile, HTTPException, status
from app.models.rapport import Rapport
from app.models.stagiaire import Stagiaire
from app.models.user import User, UserRole
from app.config import settings


async def upload_rapport(
    db: AsyncSession,
    stagiaire_id: int,
    file: UploadFile,
    user_id: int,
) -> Rapport:
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    if user.role not in (UserRole.ENCADRANT, UserRole.RH, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    stagiaire_result = await db.execute(select(Stagiaire).where(Stagiaire.id == stagiaire_id))
    stagiaire = stagiaire_result.scalar_one_or_none()
    if not stagiaire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stagiaire introuvable")
    if user.role == UserRole.ENCADRANT and stagiaire.encadrant_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous n'êtes pas l'encadrant de ce stagiaire")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seuls les fichiers PDF sont acceptés")
    if file.content_type and file.content_type != "application/pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le fichier doit être un PDF (type MIME invalide)")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filepath = os.path.join(settings.UPLOAD_DIR, f"{stagiaire_id}_{file.filename}")

    content = await file.read()
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    rapport = Rapport(
        stagiaire_id=stagiaire_id,
        file_pdf=filepath,
        uploaded_by=user_id,
    )
    db.add(rapport)
    await db.flush()
    await db.refresh(rapport)
    return rapport


async def get_rapports_by_stagiaire(db: AsyncSession, stagiaire_id: int):
    result = await db.execute(
        select(Rapport).where(Rapport.stagiaire_id == stagiaire_id).order_by(Rapport.created_at.desc())
    )
    return result.scalars().all()


async def delete_rapport(db: AsyncSession, rapport_id: int) -> bool:
    result = await db.execute(select(Rapport).where(Rapport.id == rapport_id))
    rapport = result.scalar_one_or_none()
    if not rapport:
        return False

    if os.path.exists(rapport.file_pdf):
        os.remove(rapport.file_pdf)

    await db.delete(rapport)
    await db.flush()
    return True
