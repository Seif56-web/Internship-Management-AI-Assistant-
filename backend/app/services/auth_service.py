from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User, UserRole
from app.models.encadrant import Encadrant
from app.schemas.auth import LoginRequest
from app.schemas.user import AccountUpdate
from app.auth.jwt_handler import verify_password, create_access_token, hash_password
from fastapi import HTTPException, status


async def _generate_next_encadrant_code(db: AsyncSession) -> str:
    result = await db.execute(select(func.max(Encadrant.code_encadrant)))
    max_code = result.scalar_one_or_none()
    if max_code:
        num = int(max_code[3:]) + 1
    else:
        num = 1
    return f"ENC{num:03d}"


async def authenticate_user(db: AsyncSession, request: LoginRequest):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    token = create_access_token({"user_id": user.id, "role": user.role.value if hasattr(user.role, 'value') else user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "nom": user.nom,
            "prenom": user.prenom,
            "role": user.role.value if hasattr(user.role, 'value') else user.role,
        },
    }


async def register_user(db: AsyncSession, user_data: dict):
    existing = await db.execute(select(User).where(User.email == user_data["email"]))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email déjà utilisé")

    role = user_data.get("role", "RH")

    user = User(
        email=user_data["email"],
        password_hash=hash_password(user_data["password"]),
        nom=user_data["nom"],
        prenom=user_data["prenom"],
        role=role,
    )
    db.add(user)
    await db.flush()

    if role == UserRole.ENCADRANT:
        code = await _generate_next_encadrant_code(db)
        enc = Encadrant(code_encadrant=code, user_id=user.id, nom=user.nom, prenom=user.prenom)
        db.add(enc)

    await db.refresh(user)
    return user


async def activer_compte(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucun compte trouvé avec cet email")
    if user.role != UserRole.ENCADRANT:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seuls les comptes encadrants peuvent être activés")

    user.password_hash = hash_password(password)
    await db.flush()
    await db.refresh(user)
    return user


async def update_account(db: AsyncSession, user: User, data: AccountUpdate):
    if data.email is not None and data.email != user.email:
        existing = await db.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email déjà utilisé")
        user.email = data.email

    if data.nom is not None:
        user.nom = data.nom

    if data.new_password:
        if not data.current_password:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe actuel requis")
        if not verify_password(data.current_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe actuel incorrect")
        user.password_hash = hash_password(data.new_password)

    await db.flush()
    await db.refresh(user)
    return user
