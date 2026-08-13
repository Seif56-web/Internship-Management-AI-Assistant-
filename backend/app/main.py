from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, engine, async_session
from app.routers import auth, stagiaires, rapports, validations, attestations, encadrants, users, evaluations, chat
from seed import seed
import logging
import os
import sqlalchemy as sa

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


app = FastAPI(
    title="Gestion des Stagiaires - Hutchinson",
    description="API de gestion des stagiaires et generation d'attestations de stage",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(stagiaires.router)
app.include_router(rapports.router)
app.include_router(validations.router)
app.include_router(attestations.router)
app.include_router(encadrants.router)
app.include_router(users.router)
app.include_router(evaluations.router)
app.include_router(chat.router)


async def migrate_to_dual_statut():
    from app.models.status import OLD_STATUT_MAP

    async with engine.begin() as conn:
        try:
            result = await conn.execute(sa.text("SELECT COUNT(*) FROM stagiaires"))
            count = result.scalar()
            if count == 0:
                return
        except Exception:
            return

        try:
            await conn.execute(sa.text("ALTER TABLE stagiaires ADD COLUMN statut_stage VARCHAR(50) DEFAULT 'Stage non débuté'"))
        except Exception:
            pass

        try:
            await conn.execute(sa.text("ALTER TABLE stagiaires ADD COLUMN statut_dossier VARCHAR(50)"))
        except Exception:
            pass

        try:
            await conn.execute(sa.text("ALTER TABLE stagiaires ADD COLUMN is_extended BOOLEAN DEFAULT 0 NOT NULL"))
        except Exception:
            pass

        try:
            await conn.execute(sa.text("ALTER TABLE stagiaires ADD COLUMN old_date_fin_stage DATE"))
        except Exception:
            pass

        try:
            await conn.execute(sa.text("ALTER TABLE stagiaires ADD COLUMN date_prolongation DATETIME"))
        except Exception:
            pass

        try:
            await conn.execute(sa.text("ALTER TABLE stagiaires ADD COLUMN suspended_at DATETIME"))
        except Exception:
            pass

        try:
            await conn.execute(sa.text("ALTER TABLE stagiaires ADD COLUMN resumed_at DATETIME"))
        except Exception:
            pass

        try:
            rows = await conn.execute(sa.text("SELECT id, statut FROM stagiaires WHERE statut_stage IS NULL OR statut_stage = ''"))
            for row in rows:
                old_statut = row[1]
                if old_statut and old_statut in OLD_STATUT_MAP:
                    new_stage, new_dossier = OLD_STATUT_MAP[old_statut]
                    params = {"stage": new_stage.value, "id": row[0]}
                    sql = "UPDATE stagiaires SET statut_stage = :stage"
                    if new_dossier:
                        sql += ", statut_dossier = :dossier"
                        params["dossier"] = new_dossier.value
                    else:
                        sql += ", statut_dossier = NULL"
                    sql += " WHERE id = :id"
                    await conn.execute(sa.text(sql), params)
                else:
                    await conn.execute(
                        sa.text("UPDATE stagiaires SET statut_stage = 'Stage non débuté', statut_dossier = NULL WHERE id = :id"),
                        {"id": row[0]},
                    )
        except Exception:
            pass

        try:
            rows_all = await conn.execute(sa.text("SELECT id, statut_stage FROM stagiaires"))
            for row in rows_all:
                if not row[1]:
                    await conn.execute(
                        sa.text("UPDATE stagiaires SET statut_stage = 'Stage non débuté' WHERE id = :id"),
                        {"id": row[0]},
                    )
        except Exception:
            pass


async def migrate_stagiaires_nullable():
    """Recrée la table stagiaires sans NOT NULL / CHECK / UNIQUE (schéma souple)."""
    async with engine.begin() as conn:
        try:
            result = await conn.execute(sa.text("PRAGMA table_info(stagiaires)"))
            cols = {row[1]: row for row in result}
        except Exception:
            return

        date_naissance_col = cols.get("date_naissance")
        if date_naissance_col is None or date_naissance_col[3] == 0:
            return

        await conn.execute(sa.text("""
            CREATE TABLE stagiaires_new (
                id INTEGER NOT NULL PRIMARY KEY,
                nom VARCHAR(100),
                prenom VARCHAR(100),
                date_naissance DATE,
                cin VARCHAR(8),
                country_code VARCHAR(5) DEFAULT '+216',
                telephone VARCHAR(20),
                email VARCHAR(255),
                civilite VARCHAR(4),
                service VARCHAR(255),
                ecole VARCHAR(255),
                taille INTEGER,
                pointure INTEGER,
                date_debut_stage DATE,
                date_fin_stage DATE,
                periode_stage VARCHAR(20),
                statut_stage VARCHAR(50) DEFAULT 'Stage non débuté',
                statut_dossier VARCHAR(50),
                is_extended BOOLEAN DEFAULT 0,
                old_date_fin_stage DATE,
                date_prolongation DATETIME,
                suspended_at DATETIME,
                resumed_at DATETIME,
                encadrant_nom VARCHAR(255),
                encadrant_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (encadrant_id) REFERENCES users (id)
            )
        """))
        await conn.execute(sa.text("""
            INSERT INTO stagiaires_new (id, nom, prenom, date_naissance, cin, country_code, telephone, email, civilite, service, ecole, taille, pointure, date_debut_stage, date_fin_stage, periode_stage, statut_stage, statut_dossier, is_extended, old_date_fin_stage, date_prolongation, suspended_at, resumed_at, encadrant_nom, encadrant_id, created_at, updated_at)
            SELECT id, nom, prenom, date_naissance, cin, country_code, telephone, email, civilite, service, ecole, taille, pointure, date_debut_stage, date_fin_stage, periode_stage, statut_stage, statut_dossier, is_extended, old_date_fin_stage, date_prolongation, suspended_at, resumed_at, encadrant_nom, encadrant_id, created_at, updated_at
            FROM stagiaires
        """))
        await conn.execute(sa.text("DROP TABLE stagiaires"))
        await conn.execute(sa.text("ALTER TABLE stagiaires_new RENAME TO stagiaires"))
        await conn.execute(sa.text("CREATE INDEX ix_stagiaires_nom ON stagiaires (nom)"))
        await conn.execute(sa.text("CREATE INDEX ix_stagiaires_cin ON stagiaires (cin)"))
        print("Migration : table stagiaires recréée (contraintes supprimées)")


async def migrate_stagiaires_nom_complet():
    """Fusionne nom+prenom en nom_complet et ajoute lettre_affectation."""
    async with engine.begin() as conn:
        try:
            result = await conn.execute(sa.text("PRAGMA table_info(stagiaires)"))
            cols = {row[1]: row for row in result}
        except Exception:
            return

        if "nom_complet" in cols:
            return

        await conn.execute(sa.text("""
            CREATE TABLE stagiaires_new (
                id INTEGER NOT NULL PRIMARY KEY,
                nom_complet VARCHAR(255),
                lettre_affectation BOOLEAN DEFAULT 0,
                date_naissance DATE,
                cin VARCHAR(8),
                country_code VARCHAR(5) DEFAULT '+216',
                telephone VARCHAR(20),
                email VARCHAR(255),
                civilite VARCHAR(4),
                service VARCHAR(255),
                ecole VARCHAR(255),
                taille INTEGER,
                pointure INTEGER,
                date_debut_stage DATE,
                date_fin_stage DATE,
                periode_stage VARCHAR(20),
                statut_stage VARCHAR(50) DEFAULT 'Stage non débuté',
                statut_dossier VARCHAR(50),
                is_extended BOOLEAN DEFAULT 0,
                old_date_fin_stage DATE,
                date_prolongation DATETIME,
                suspended_at DATETIME,
                resumed_at DATETIME,
                encadrant_nom VARCHAR(255),
                encadrant_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (encadrant_id) REFERENCES users (id)
            )
        """))
        await conn.execute(sa.text("""
            INSERT INTO stagiaires_new (id, nom_complet, lettre_affectation, date_naissance, cin, country_code, telephone, email, civilite, service, ecole, taille, pointure, date_debut_stage, date_fin_stage, periode_stage, statut_stage, statut_dossier, is_extended, old_date_fin_stage, date_prolongation, suspended_at, resumed_at, encadrant_nom, encadrant_id, created_at, updated_at)
            SELECT id, TRIM(COALESCE(nom, '') || ' ' || COALESCE(prenom, '')), 0, date_naissance, cin, country_code, telephone, email, civilite, service, ecole, taille, pointure, date_debut_stage, date_fin_stage, periode_stage, statut_stage, statut_dossier, is_extended, old_date_fin_stage, date_prolongation, suspended_at, resumed_at, encadrant_nom, encadrant_id, created_at, updated_at
            FROM stagiaires
        """))
        await conn.execute(sa.text("DROP TABLE stagiaires"))
        await conn.execute(sa.text("ALTER TABLE stagiaires_new RENAME TO stagiaires"))
        await conn.execute(sa.text("CREATE INDEX ix_stagiaires_nom_complet ON stagiaires (nom_complet)"))
        await conn.execute(sa.text("CREATE INDEX ix_stagiaires_cin ON stagiaires (cin)"))
        print("Migration : nom/prenom fusionnés en nom_complet + lettre_affectation ajoutée")


async def backfill_encadrant_ids():
    """Lie les stagiaires ayant un encadrant_nom mais aucun encadrant_id à un encadrant existant (ou le crée)."""
    from app.models.stagiaire import Stagiaire
    from app.services import encadrant_service

    async with async_session() as session:
        result = await session.execute(
            sa.select(Stagiaire).where(Stagiaire.encadrant_nom.isnot(None), Stagiaire.encadrant_id.is_(None))
        )
        stagiaires = result.scalars().all()
        linked = 0
        for stagiaire in stagiaires:
            try:
                enc = await encadrant_service.get_or_create_encadrant(session, stagiaire.encadrant_nom)
                if enc:
                    stagiaire.encadrant_id = enc.user_id
                    linked += 1
            except Exception as e:
                print(f"Backfill encadrant échoué pour '{stagiaire.encadrant_nom}' : {e}")
        if linked:
            await session.commit()
            print(f"Backfill : {linked} stagiaire(s) lié(s) à un encadrant")


@app.on_event("startup")
async def startup():
    os.makedirs("uploads/rapports", exist_ok=True)
    os.makedirs("uploads/attestations", exist_ok=True)
    await init_db()
    await migrate_to_dual_statut()
    await migrate_stagiaires_nullable()
    await migrate_stagiaires_nom_complet()
    await seed()
    await backfill_encadrant_ids()


@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "API operationnelle"}
