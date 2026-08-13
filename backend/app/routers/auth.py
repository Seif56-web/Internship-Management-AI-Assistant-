from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, AccountUpdate
from app.services import auth_service
from app.auth.dependencies import get_current_user
from app.models.user import User


class ActiverCompteRequest(BaseModel):
    email: EmailStr
    password: str

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.authenticate_user(db, request)


@router.post("/register")
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(db, user_data.model_dump())
    return {"id": user.id, "email": user.email, "nom": user.nom, "prenom": user.prenom, "role": user.role.value if hasattr(user.role, 'value') else user.role}


@router.post("/activer")
async def activer_compte(data: ActiverCompteRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.activer_compte(db, data.email, data.password)
    return {"detail": "Compte activé avec succès"}


@router.put("/account")
async def update_account(data: AccountUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = await auth_service.update_account(db, current_user, data)
    return {
        "id": user.id,
        "email": user.email,
        "nom": user.nom,
        "prenom": user.prenom,
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
    }
