import os
import tempfile

TEST_DB = os.path.join(tempfile.gettempdir(), "test_chat_gestion_stagiaires.db")
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

_db_url = "sqlite+aiosqlite:///" + TEST_DB.replace("\\", "/")
os.environ["DATABASE_URL"] = _db_url
os.environ["DATABASE_URL_SYNC"] = "sqlite:///" + TEST_DB.replace("\\", "/")
os.environ["LLM_API_KEY"] = ""
os.environ["CHAT_RATE_LIMIT_MAX"] = "1000"
os.environ["CHAT_RATE_LIMIT_WINDOW_SECONDS"] = "60"

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402

from app.database import async_session, engine, Base  # noqa: E402
from app.auth.jwt_handler import hash_password  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.stagiaire import Stagiaire  # noqa: E402
from app.models.encadrant import Encadrant  # noqa: E402
from app.models.evaluation import Evaluation  # noqa: E402
from app.models.rapport import Rapport  # noqa: E402
from app.models.attestation import Attestation  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _fresh_db():
    from app.utils.rate_limiter import reset_rate_limits

    reset_rate_limits()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def create_user(db, email: str, role: UserRole = UserRole.RH, nom: str = "Test", prenom: str = "User") -> User:
    user = User(
        email=email,
        password_hash=hash_password("test123"),
        nom=nom,
        prenom=prenom,
        role=role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def create_stagiaire(
    db,
    nom_complet: str,
    user_id: int | None = None,
    statut_stage: str = "Stage en cours",
    cin: str | None = None,
) -> Stagiaire:
    stagiaire = Stagiaire(
        nom_complet=nom_complet,
        statut_stage=statut_stage,
        encadrant_id=user_id,
        cin=cin,
    )
    db.add(stagiaire)
    await db.flush()
    await db.refresh(stagiaire)
    return stagiaire