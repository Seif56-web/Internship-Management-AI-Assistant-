from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
from app.database import get_db
from app.schemas.rapport import RapportOut
from app.services import rapport_service
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.rapport import Rapport

router = APIRouter(prefix="/api/rapports", tags=["Rapports"])


@router.post("/upload/{stagiaire_id}", response_model=RapportOut)
async def upload_rapport(stagiaire_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await rapport_service.upload_rapport(db, stagiaire_id, file, current_user.id)


@router.get("/download/{rapport_id}")
async def download_rapport(rapport_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Rapport).where(Rapport.id == rapport_id))
    rapport = result.scalar_one_or_none()
    if not rapport:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rapport introuvable")
    if not os.path.exists(rapport.file_pdf):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier introuvable")
    return FileResponse(rapport.file_pdf, media_type="application/pdf", filename=os.path.basename(rapport.file_pdf))


@router.get("/{stagiaire_id}", response_model=List[RapportOut])
async def get_rapports(stagiaire_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await rapport_service.get_rapports_by_stagiaire(db, stagiaire_id)


@router.delete("/{rapport_id}")
async def delete_rapport(rapport_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    deleted = await rapport_service.delete_rapport(db, rapport_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rapport introuvable")
    return {"detail": "Rapport supprime avec succes"}
