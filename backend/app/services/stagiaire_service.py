from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, exists
from typing import Optional, List
from datetime import date, datetime, timezone
from app.models.stagiaire import Stagiaire
from datetime import timedelta
from app.models.status import (
    StatutStage, StatutDossier,
    compute_statut_stage, is_date_based,
    can_transition_stage, get_allowed_stage_transitions,
)
from app.models.user import User
from app.models.validation import Validation
from app.models.rapport import Rapport
from app.models.attestation import Attestation
from app.schemas.stagiaire import StagiaireCreate, StagiaireUpdate
from fastapi import HTTPException, status


async def _resolve_encadrant_nom(db: AsyncSession, encadrant_id: Optional[int]) -> Optional[str]:
    if not encadrant_id:
        return None
    result = await db.execute(select(User).where(User.id == encadrant_id))
    user = result.scalar_one_or_none()
    if user:
        return f"{user.prenom} {user.nom}".strip() or user.nom
    return None


def _apply_date_statut(stagiaire: Stagiaire):
    current = stagiaire.statut_stage
    if isinstance(current, str):
        try:
            current = StatutStage(current)
        except ValueError:
            return
    if current in MANUAL_STATUSES:
        return
    if stagiaire.date_debut_stage and stagiaire.date_fin_stage:
        result = compute_statut_stage(stagiaire.date_debut_stage, stagiaire.date_fin_stage)
        stagiaire.statut_stage = result.value


MANUAL_STATUSES = {
    StatutStage.STAGE_SUSPENDU.value,
    StatutStage.STAGE_VALIDE.value,
    StatutStage.STAGE_REFUSE.value,
}


async def _populate_attestation(db: AsyncSession, stagiaire: Stagiaire):
    result = await db.execute(
        select(Attestation).where(Attestation.stagiaire_id == stagiaire.id).order_by(Attestation.created_at.desc()).limit(1)
    )
    att = result.scalar_one_or_none()
    if att:
        stagiaire.attestation_id = att.id
        stagiaire.attestation_numero = att.numero_attestation
    else:
        stagiaire.attestation_id = None
        stagiaire.attestation_numero = None


async def get_stagiaires(
    db: AsyncSession,
    search: Optional[str] = None,
    statuts_stage: Optional[List[str]] = None,
    statuts_dossier: Optional[List[str]] = None,
    statuts_rapport: Optional[List[str]] = None,
    encadrant_id: Optional[int] = None,
    has_attestation: Optional[bool] = None,
    periodes: Optional[List[str]] = None,
    encadrant_ids: Optional[List[int]] = None,
    date_min: Optional[date] = None,
    date_max: Optional[date] = None,
) -> List[Stagiaire]:
    query = select(Stagiaire).order_by(Stagiaire.created_at.desc())

    if search:
        query = query.where(
            or_(
                Stagiaire.nom_complet.ilike(f"%{search}%"),
                Stagiaire.email.ilike(f"%{search}%"),
            )
        )

    if statuts_stage:
        query = query.where(Stagiaire.statut_stage.in_(statuts_stage))

    if statuts_dossier:
        query = query.where(Stagiaire.statut_dossier.in_(statuts_dossier))

    if encadrant_id is not None:
        query = query.where(Stagiaire.encadrant_id == encadrant_id)

    if encadrant_ids:
        query = query.where(Stagiaire.encadrant_id.in_(encadrant_ids))

    if periodes:
        query = query.where(Stagiaire.periode_stage.in_(periodes))

    if date_min:
        query = query.where(Stagiaire.date_debut_stage >= date_min)
    if date_max:
        query = query.where(Stagiaire.date_fin_stage <= date_max)

    if statuts_rapport:
        subq = select(Rapport.stagiaire_id).where(Rapport.stagiaire_id == Stagiaire.id)
        if "Rapport déposé" in statuts_rapport and "Rapport non déposé" not in statuts_rapport:
            query = query.where(exists(subq))
        elif "Rapport non déposé" in statuts_rapport and "Rapport déposé" not in statuts_rapport:
            query = query.where(~exists(subq))

    if has_attestation:
        subq = select(Attestation.stagiaire_id).where(Attestation.stagiaire_id == Stagiaire.id)
        query = query.where(exists(subq))

    result = await db.execute(query)
    stagiaires = result.scalars().all()
    modified = []
    for s in stagiaires:
        if not s.encadrant_nom and s.encadrant_id:
            s.encadrant_nom = await _resolve_encadrant_nom(db, s.encadrant_id)
        old_statut = s.statut_stage
        _apply_date_statut(s)
        if s.statut_stage != old_statut:
            modified.append(s)
        await _populate_attestation(db, s)
    if modified:
        await db.flush()
        for s in modified:
            await db.refresh(s)
    return stagiaires


async def get_stagiaire_by_id(db: AsyncSession, stagiaire_id: int) -> Optional[Stagiaire]:
    result = await db.execute(select(Stagiaire).where(Stagiaire.id == stagiaire_id))
    return result.scalar_one_or_none()


async def get_stagiaire_detail(db: AsyncSession, stagiaire_id: int) -> Optional[dict]:
    stagiaire = await get_stagiaire_by_id(db, stagiaire_id)
    if not stagiaire:
        return None

    old_statut = stagiaire.statut_stage
    _apply_date_statut(stagiaire)
    if stagiaire.statut_stage != old_statut:
        await db.flush()
        await db.refresh(stagiaire)

    validations_result = await db.execute(
        select(Validation).where(Validation.stagiaire_id == stagiaire_id)
    )
    rapports_result = await db.execute(
        select(Rapport).where(Rapport.stagiaire_id == stagiaire_id)
    )
    attestations_result = await db.execute(
        select(Attestation).where(Attestation.stagiaire_id == stagiaire_id)
    )

    data = {c.name: getattr(stagiaire, c.name) for c in stagiaire.__table__.columns}
    if not data.get("encadrant_nom") and data.get("encadrant_id"):
        data["encadrant_nom"] = await _resolve_encadrant_nom(db, data["encadrant_id"])

    await _populate_attestation(db, stagiaire)
    data["attestation_id"] = stagiaire.attestation_id
    data["attestation_numero"] = stagiaire.attestation_numero

    return {
        **data,
        "validations": [
            {
                "id": v.id,
                "status": v.status.value if hasattr(v.status, 'value') else v.status,
                "commentaire": v.commentaire,
                "created_at": v.created_at,
                "encadrant_id": v.encadrant_id,
            }
            for v in validations_result.scalars().all()
        ],
        "rapports": [
            {"id": r.id, "file_pdf": r.file_pdf, "created_at": r.created_at}
            for r in rapports_result.scalars().all()
        ],
        "attestations": [
            {"id": a.id, "numero_attestation": a.numero_attestation, "created_at": a.created_at}
            for a in attestations_result.scalars().all()
        ],
    }


DEFAULTS = {
    "nom_complet": "",
    "lettre_affectation": False,
    "date_naissance": date.today(),
    "cin": "00000000",
    "telephone": "",
    "email": "",
    "date_debut_stage": date.today(),
    "date_fin_stage": date.today() + timedelta(days=30),
}

async def create_stagiaire(db: AsyncSession, data: StagiaireCreate) -> Stagiaire:
    dump = data.model_dump(exclude={"encadrant_nom"})
    for field, default in DEFAULTS.items():
        if not dump.get(field):
            dump[field] = default
    if data.cin and data.cin != "00000000":
        existing = await db.execute(select(Stagiaire).where(Stagiaire.cin == data.cin))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Le CIN '{data.cin}' existe déjà")
    if data.email:
        existing_email = await db.execute(select(Stagiaire).where(Stagiaire.email == data.email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"L'email '{data.email}' existe déjà")
    stagiaire = Stagiaire(**dump)
    if data.encadrant_id and not data.encadrant_nom:
        stagiaire.encadrant_nom = await _resolve_encadrant_nom(db, data.encadrant_id)
    elif data.encadrant_nom:
        stagiaire.encadrant_nom = data.encadrant_nom
    if stagiaire.date_debut_stage and stagiaire.date_fin_stage:
        stagiaire.statut_stage = compute_statut_stage(stagiaire.date_debut_stage, stagiaire.date_fin_stage).value
    else:
        stagiaire.statut_stage = StatutStage.STAGE_NON_DEBUTE.value
    stagiaire.statut_dossier = None
    db.add(stagiaire)
    await db.flush()
    await db.refresh(stagiaire)
    await _populate_attestation(db, stagiaire)
    return stagiaire


async def update_stagiaire(db: AsyncSession, stagiaire_id: int, data: StagiaireUpdate) -> Optional[Stagiaire]:
    stagiaire = await get_stagiaire_by_id(db, stagiaire_id)
    if not stagiaire:
        return None

    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("encadrant_nom", None)

    if "encadrant_id" in update_data:
        nom = await _resolve_encadrant_nom(db, update_data["encadrant_id"])
        if nom:
            update_data["encadrant_nom"] = nom

    old_date_fin = stagiaire.date_fin_stage
    for key, value in update_data.items():
        setattr(stagiaire, key, value)

    current_statut = stagiaire.statut_stage
    if isinstance(current_statut, str):
        try:
            current_statut = StatutStage(current_statut)
        except ValueError:
            current_statut = None

    if current_statut in MANUAL_STATUSES:
        pass
    else:
        _apply_date_statut(stagiaire)

    if "date_fin_stage" in update_data:
        new_date_fin = update_data["date_fin_stage"]
        if current_statut == StatutStage.STAGE_TERMINE and new_date_fin and new_date_fin > date.today():
            stagiaire.statut_stage = StatutStage.STAGE_EN_COURS.value
            if not stagiaire.is_extended:
                stagiaire.old_date_fin_stage = old_date_fin
            stagiaire.is_extended = True
            stagiaire.date_prolongation = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(stagiaire)
    await _populate_attestation(db, stagiaire)
    return stagiaire


async def change_statut_stage(db: AsyncSession, stagiaire_id: int, new_statut_value: str, current_user=None) -> Stagiaire:
    stagiaire = await get_stagiaire_by_id(db, stagiaire_id)
    if not stagiaire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stagiaire introuvable")

    try:
        new_statut = StatutStage(new_statut_value)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Statut invalide : {new_statut_value}")

    current_statut = stagiaire.statut_stage
    if isinstance(current_statut, str):
        try:
            current_statut = StatutStage(current_statut)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Le statut actuel du stagiaire est inconnu.")

    if not can_transition_stage(current_statut, new_statut):
        allowed = get_allowed_stage_transitions(current_statut)
        allowed_labels = [s.value for s in allowed]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transition de '{current_statut.value}' vers '{new_statut.value}' non autorisée. Transitions possibles : {', '.join(allowed_labels) if allowed_labels else 'aucune'}",
        )

    stagiaire.statut_stage = new_statut.value
    now = datetime.now(timezone.utc)

    if new_statut == StatutStage.STAGE_SUSPENDU:
        stagiaire.suspended_at = now
        stagiaire.resumed_at = None
    elif new_statut == StatutStage.STAGE_EN_COURS and current_statut == StatutStage.STAGE_SUSPENDU:
        stagiaire.resumed_at = now

    if current_user and new_statut in (StatutStage.STAGE_SUSPENDU, StatutStage.STAGE_EN_COURS):
        from app.models.validation import Validation, StatutValidation
        validation = Validation(
            stagiaire_id=stagiaire_id,
            encadrant_id=current_user.id,
            status=StatutValidation.SUSPENDU,
            commentaire="Stage suspendu" if new_statut == StatutStage.STAGE_SUSPENDU else "Stage repris",
        )
        db.add(validation)

    await db.flush()
    await db.refresh(stagiaire)
    return stagiaire


async def change_statut_dossier(db: AsyncSession, stagiaire_id: int, new_statut_value: str) -> Stagiaire:
    stagiaire = await get_stagiaire_by_id(db, stagiaire_id)
    if not stagiaire:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stagiaire introuvable")

    try:
        new_statut = StatutDossier(new_statut_value)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Statut de dossier invalide : {new_statut_value}")

    stagiaire.statut_dossier = new_statut.value
    await db.flush()
    await db.refresh(stagiaire)
    return stagiaire


async def delete_stagiaire(db: AsyncSession, stagiaire_id: int) -> bool:
    stagiaire = await get_stagiaire_by_id(db, stagiaire_id)
    if not stagiaire:
        return False
    await db.delete(stagiaire)
    await db.flush()
    return True


async def delete_stagiaires(db: AsyncSession, stagiaire_ids: List[int]) -> int:
    count = 0
    for stagiaire_id in stagiaire_ids:
        stagiaire = await get_stagiaire_by_id(db, stagiaire_id)
        if stagiaire:
            await db.delete(stagiaire)
            count += 1
    if count:
        await db.flush()
    return count
