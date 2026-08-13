"""Seed les 3 comptes de démonstration au démarrage si la base est vide."""
import asyncio
from app.database import async_session, init_db
from app.models.user import User, UserRole
from app.models.encadrant import Encadrant
from app.auth.jwt_handler import hash_password
from sqlalchemy import select


async def seed():
    await init_db()

    session = async_session()
    try:
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none():
            return

        users_data = [
            {"nom": "Rania", "prenom": "", "email": "rania@hutchinson.com", "password": "admin123", "role": UserRole.ADMIN},
            {"nom": "Nour", "prenom": "", "email": "nour@hutchinson.com", "password": "rh123", "role": UserRole.RH},
            {"nom": "Moez", "prenom": "", "email": "moez@hutchinson.com", "password": "encadrant123", "role": UserRole.ENCADRANT},
        ]

        for u in users_data:
            user = User(
                nom=u["nom"],
                prenom=u["prenom"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
            )
            session.add(user)
            await session.flush()

            if u["role"] == UserRole.ENCADRANT:
                enc = Encadrant(code_encadrant="ENC001", user_id=user.id, nom=user.nom, prenom=user.prenom)
                session.add(enc)

        await session.commit()
        print("Comptes de démonstration créés")
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(seed())
