import secrets
import re
import unicodedata
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from app.models.encadrant import Encadrant
from app.models.user import User, UserRole
from app.auth.jwt_handler import hash_password
from fastapi import HTTPException, status


def normalize_encadrant_name(name: str) -> str:
    if not name:
        return ""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\b(mr|mme|mlle|mrs|ms|dr|pr|sir)\b\.?", " ", s, flags=re.IGNORECASE)
    return " ".join(s.replace(",", " ").split()).lower()


def split_nom_prenom(name: str):
    tokens = name.replace(",", " ").split()
    if len(tokens) <= 1:
        return name.strip(), ""
    prenom = tokens[0]
    nom = " ".join(tokens[1:])
    return prenom, nom


async def get_or_create_encadrant(db: AsyncSession, encadrant_nom: str) -> Optional[Encadrant]:
    """Renvoie l'encadrant existant correspondant au nom, ou le crée (User + Encadrant)."""
    if not encadrant_nom or not encadrant_nom.strip():
        return None
    normalized = normalize_encadrant_name(encadrant_nom)
    if not normalized:
        return None

    encadrants = await get_all_encadrants(db)
    for enc in encadrants:
        full_1 = normalize_encadrant_name(f"{enc.prenom} {enc.nom}")
        full_2 = normalize_encadrant_name(f"{enc.nom} {enc.prenom}")
        if normalized and normalized in (full_1, full_2):
            return enc

    prenom, nom = split_nom_prenom(encadrant_nom.strip())
    created = await create_encadrant(db, nom, prenom, None)
    result = await db.execute(select(Encadrant).where(Encadrant.id == created["id"]))
    return result.scalar_one_or_none()


async def _generate_next_code(db: AsyncSession) -> str:
    result = await db.execute(select(func.max(Encadrant.code_encadrant)))
    max_code = result.scalar_one_or_none()
    if max_code:
        num = int(max_code[3:]) + 1
    else:
        num = 1
    return f"ENC{num:03d}"


async def create_encadrant(db: AsyncSession, nom: str, prenom: str, email: str | None = None) -> dict:
    code = await _generate_next_code(db)
    random_pw = secrets.token_urlsafe(16)

    if email:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email déjà utilisé")

        user = User(
            email=email,
            password_hash=hash_password(random_pw),
            nom=nom,
            prenom=prenom,
            role=UserRole.ENCADRANT,
        )
    else:
        placeholder_email = f"enc-{code.lower()}@placeholder.local"
        user = User(
            email=placeholder_email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            nom=nom,
            prenom=prenom,
            role=UserRole.ENCADRANT,
        )

    db.add(user)
    await db.flush()

    enc = Encadrant(code_encadrant=code, user_id=user.id, nom=nom, prenom=prenom)
    db.add(enc)
    await db.flush()
    await db.refresh(enc)

    return {
        "id": enc.id,
        "code_encadrant": enc.code_encadrant,
        "nom": enc.nom,
        "prenom": enc.prenom,
        "email": email,
    }


async def get_all_encadrants(db: AsyncSession) -> List[Encadrant]:
    result = await db.execute(
        select(Encadrant).order_by(Encadrant.code_encadrant)
    )
    return result.scalars().all()


async def search_encadrants(db: AsyncSession, query: str) -> List[Encadrant]:
    stmt = select(Encadrant).where(
        (Encadrant.nom + " " + Encadrant.prenom).ilike(f"%{query}%")
    ).order_by(Encadrant.code_encadrant)
    result = await db.execute(stmt)
    return result.scalars().all()
