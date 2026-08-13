from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.validation import ValidationCreate, ValidationOut
from app.services import validation_service
from app.auth.dependencies import get_current_user, require_role
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/validations", tags=["Validations"])


@router.post("/{stagiaire_id}", response_model=ValidationOut)
async def valider_stage(stagiaire_id: int, data: ValidationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role(UserRole.ENCADRANT, UserRole.RH, UserRole.ADMIN))):
    validation = await validation_service.valider_stage(db, stagiaire_id, current_user, data.status, data.commentaire)
    return {
        "id": validation.id,
        "stagiaire_id": validation.stagiaire_id,
        "encadrant_id": validation.encadrant_id,
        "status": validation.status.value if hasattr(validation.status, 'value') else validation.status,
        "commentaire": validation.commentaire,
        "created_at": validation.created_at,
        "encadrant_nom": f"{current_user.prenom} {current_user.nom}",
    }


@router.get("/{stagiaire_id}", response_model=List[ValidationOut])
async def get_validations(stagiaire_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await validation_service.get_validations_by_stagiaire(db, stagiaire_id)
