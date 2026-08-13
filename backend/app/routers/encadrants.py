from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database import get_db
from app.schemas.encadrant import EncadrantOut, EncadrantCreateByRH
from app.services import encadrant_service
from app.auth.dependencies import get_current_user, require_role
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/encadrants", tags=["Encadrants"])


@router.get("/", response_model=List[EncadrantOut])
async def list_encadrants(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await encadrant_service.get_all_encadrants(db)


@router.get("/search", response_model=List[EncadrantOut])
async def search_encadrants(q: str = "", db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not q:
        return await encadrant_service.get_all_encadrants(db)
    return await encadrant_service.search_encadrants(db, q)


@router.post("/create")
async def create_encadrant(data: EncadrantCreateByRH, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role(UserRole.RH, UserRole.ADMIN))):
    return await encadrant_service.create_encadrant(db, data.nom, data.prenom, data.email)
