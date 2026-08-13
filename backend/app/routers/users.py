from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.database import get_db
from app.models.user import User, UserRole
from app.models.encadrant import Encadrant
from app.auth.dependencies import get_current_user, require_role
from pydantic import BaseModel, EmailStr
from datetime import datetime

router = APIRouter(prefix="/api/users", tags=["Users"])


class UserOut(BaseModel):
    id: int
    email: str
    nom: str
    prenom: str
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr


class EncadrantUserOut(BaseModel):
    id: int
    email: str
    nom: str
    prenom: str
    code_encadrant: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role(UserRole.ADMIN))):
    result = await db.execute(select(User))
    users = result.scalars().all()
    role_order = {UserRole.ADMIN: 0, UserRole.RH: 1, UserRole.ENCADRANT: 2}
    users.sort(key=lambda u: (role_order.get(u.role, 9), u.nom, u.prenom))
    return users


@router.put("/{user_id}")
async def update_user(user_id: int, data: UserUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role(UserRole.ADMIN))):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    email_check = await db.execute(select(User).where(User.email == data.email, User.id != user_id))
    if email_check.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email déjà utilisé")

    user.nom = data.nom
    user.prenom = data.prenom
    user.email = data.email
    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role(UserRole.ADMIN))):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vous ne pouvez pas supprimer votre propre compte")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")

    enc_result = await db.execute(select(Encadrant).where(Encadrant.user_id == user_id))
    enc = enc_result.scalar_one_or_none()
    if enc:
        await db.delete(enc)

    await db.delete(user)
    await db.flush()
    return {"detail": "Utilisateur supprimé avec succès"}


@router.get("/encadrants", response_model=List[EncadrantUserOut])
async def list_encadrants(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(User, Encadrant.code_encadrant)
        .join(Encadrant, User.id == Encadrant.user_id)
        .where(User.role == UserRole.ENCADRANT)
        .order_by(User.nom, User.prenom)
    )
    rows = result.all()
    return [
        {"id": u.id, "email": u.email, "nom": u.nom, "prenom": u.prenom, "code_encadrant": code}
        for u, code in rows
    ]
