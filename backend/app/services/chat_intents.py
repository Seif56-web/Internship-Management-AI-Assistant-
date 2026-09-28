"""Détection d'intention et extraction des données métier pour le chatbot.

La base de données reste la source de vérité : les requêtes sont écrites à la main
via SQLAlchemy et les services existants. Le LLM ne reçoit que les données
récupérées ici et ne peut pas les inventer.

Chaque gestionnaire renvoie :
- data_context : données réelles formatées en français (contexte pour le LLM)
- fallback_answer : réponse déterministe en français (utilisée si le LLM est indisponible)

Types d'intention :
- DATABASE : question métier structurée (réponse depuis la base)
- RAG : question documentaire/procédurale (réponse depuis les documents indexés)
- HYBRID : question mêlant données métier et connaissances documentaires
- GENERAL : question générale (salutations, aide, etc.)
"""
import logging
import re
import unicodedata
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select, exists, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.stagiaire import Stagiaire
from app.models.evaluation import Evaluation
from app.models.rapport import Rapport
from app.models.attestation import Attestation
from app.models.encadrant import Encadrant
from app.models.validation import Validation, StatutValidation
from app.services import stagiaire_service
from app.rag.config import rag_settings

logger = logging.getLogger(__name__)

MAX_LIST = 10


def normalize(text: str) -> str:
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9\s]", " ", s.lower()).strip()


def _clean_candidate(raw: str) -> str:
    raw = re.sub(r"[^a-zA-ZÀ-ÿ0-9\s'-]", " ", raw or "")
    raw = re.sub(
        r"^(de|du|des|le|la|les|sur|au|aux|a|l'|d'|concernant|pour|par|avec|s'appelle|appelle|nomme|nommé)\s+",
        "",
        raw.strip(),
        flags=re.IGNORECASE,
    )
    raw = re.sub(r"\s+", " ", raw).strip()
    raw = re.sub(r"\s*'\s*", "'", raw)
    raw = re.sub(r"^(l'|d')", "", raw.strip(), flags=re.IGNORECASE)
    return raw


def _extract_after(message: str, keywords: List[str]) -> str:
    lower = message.lower()
    for kw in keywords:
        idx = lower.find(kw)
        if idx != -1:
            return message[idx + len(kw):]
    return ""


# Ordre important : les formes les plus longues d'abord pour éviter les
# découpes partielles (ex. « encadre » est un sous-mot d'« encadrant »).
_ENCADRANT_KEYWORDS = [
    "encadrants", "encadrant",
    "encadrés par", "encadres par", "encadré par", "encadre par",
    "encadrées", "encadrees", "encadrés", "encadres", "encadrée", "encadree", "encadré", "encadre",
]


def _format_stagiaire(s: Stagiaire) -> str:
    return (
        f"- {s.nom_complet or 'Nom inconnu'} (CIN : {s.cin or 'N/A'}) "
        f"| service : {s.service or 'N/A'} | école : {s.ecole or 'N/A'} "
        f"| stage : {s.date_debut_stage} → {s.date_fin_stage} "
        f"| statut : {s.statut_stage} | encadrant : {s.encadrant_nom or 'N/A'}"
    )


async def _scoped_stagiaires(db: AsyncSession, user: User, **kwargs) -> List[Stagiaire]:
    """Applique la permission : un encadrant ne voit que ses propres stagiaires."""
    if user.role == UserRole.ENCADRANT:
        kwargs["encadrant_ids"] = [user.id]
    return await stagiaire_service.get_stagiaires(db, **kwargs)


async def _stagiaires_without_rapport(db: AsyncSession, user: User) -> List[Stagiaire]:
    stmt = select(Stagiaire).where(
        ~exists(select(Rapport.stagiaire_id).where(Rapport.stagiaire_id == Stagiaire.id))
    ).order_by(Stagiaire.nom_complet)
    if user.role == UserRole.ENCADRANT:
        stmt = stmt.where(Stagiaire.encadrant_id == user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def _stagiaires_without_evaluation(db: AsyncSession, user: User) -> List[Stagiaire]:
    stmt = select(Stagiaire).where(
        ~exists(select(Evaluation.stagiaire_id).where(Evaluation.stagiaire_id == Stagiaire.id))
    ).order_by(Stagiaire.nom_complet)
    if user.role == UserRole.ENCADRANT:
        stmt = stmt.where(Stagiaire.encadrant_id == user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def _stagiaires_with_attestation(db: AsyncSession, user: User) -> List[Stagiaire]:
    stmt = select(Stagiaire).where(
        exists(select(Attestation.stagiaire_id).where(Attestation.stagiaire_id == Stagiaire.id))
    ).order_by(Stagiaire.nom_complet)
    if user.role == UserRole.ENCADRANT:
        stmt = stmt.where(Stagiaire.encadrant_id == user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def _stagiaires_valides(db: AsyncSession, user: User) -> List[Stagiaire]:
    stmt = select(Stagiaire).where(
        exists(
            select(Validation.id).where(
                Validation.stagiaire_id == Stagiaire.id,
                Validation.status == StatutValidation.VALIDE,
            )
        )
    ).order_by(Stagiaire.nom_complet)
    if user.role == UserRole.ENCADRANT:
        stmt = stmt.where(Stagiaire.encadrant_id == user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


async def _stagiaires_en_attente_validation(db: AsyncSession, user: User) -> List[Stagiaire]:
    stmt = select(Stagiaire).where(
        ~exists(
            select(Validation.id).where(
                Validation.stagiaire_id == Stagiaire.id,
                Validation.status == StatutValidation.VALIDE,
            )
        )
    ).order_by(Stagiaire.nom_complet)
    if user.role == UserRole.ENCADRANT:
        stmt = stmt.where(Stagiaire.encadrant_id == user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


def _names_list(stagiaires: List[Stagiaire], limit: int = MAX_LIST) -> str:
    names = [f"- {s.nom_complet}" for s in stagiaires[:limit]]
    joined = "\n".join(names)
    if len(stagiaires) > limit:
        joined += f"\n- ... et {len(stagiaires) - limit} autre(s)"
    return joined


# ---------------------------------------------------------------------------
# Évaluations : la « note » d'un stagiaire est la moyenne des critères
# renseignés (échelle /5), convertie sur /20 (×4) pour les questions usuelles
# (« plus de 15 », ...). Aucune note n'est inventée : tout est calculé ici
# à partir des lignes réelles de la table `evaluations`.
# ---------------------------------------------------------------------------
_EVALUATION_CRITERIA = [
    "qualite_travail",
    "autonomie",
    "ponctualite",
    "communication",
    "esprit_equipe",
    "capacite_apprentissage",
    "initiative",
    "respect_consignes",
]

_CRITERION_LABELS = {
    "qualite_travail": "Qualité du travail",
    "autonomie": "Autonomie",
    "ponctualite": "Ponctualité",
    "communication": "Communication",
    "esprit_equipe": "Esprit d'équipe",
    "capacite_apprentissage": "Capacité d'apprentissage",
    "initiative": "Initiative",
    "respect_consignes": "Respect des consignes",
}


def _evaluation_scores(e: Evaluation) -> Tuple[Optional[float], Optional[float]]:
    """Renvoie (moyenne /5, moyenne /20) de l'évaluation, ou (None, None) si
    aucun critère n'est renseigné."""
    values = [getattr(e, c) for c in _EVALUATION_CRITERIA]
    values = [v for v in values if v is not None]
    if not values:
        return None, None
    score5 = round(sum(values) / len(values), 2)
    score20 = round(score5 * 4, 1)
    return score5, score20


def _fmt_score(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else str(v)


def _threshold_to_20(value: int) -> float:
    """Convertit un seuil sur l'échelle /20 : un seuil <= 5 est interprété
    sur l'échelle /5 des critères, un seuil > 5 sur l'échelle /20."""
    return round(value * 4, 2) if value <= 5 else float(value)


def _extract_threshold(message: str) -> Optional[Tuple[str, int, Optional[int]]]:
    """Extrait (opérateur, seuil, [seuil max]) depuis la question.

    Opérateurs : gt (plus de), gte (au moins), lt (moins de), between.
    """
    m = normalize(message)
    patterns = [
        (re.compile(r"plus de (\d+)"), "gt"),
        (re.compile(r"plus que (\d+)"), "gt"),
        (re.compile(r"superieur a (\d+)"), "gt"),
        (re.compile(r"superieure a (\d+)"), "gt"),
        (re.compile(r"au moins (\d+)"), "gte"),
        (re.compile(r"minimum (\d+)"), "gte"),
        (re.compile(r"inferieur a (\d+)"), "lt"),
        (re.compile(r"inferieure a (\d+)"), "lt"),
        (re.compile(r"moins de (\d+)"), "lt"),
        (re.compile(r"entre (\d+) et (\d+)"), "between"),
    ]
    for pattern, op in patterns:
        match = pattern.search(m)
        if match:
            values = [int(v) for v in match.groups()]
            if op == "between":
                return ("between", values[0], values[1])
            return (op, values[0], None)
    return None


def _threshold_label(threshold: Tuple[str, int, Optional[int]]) -> str:
    op, lo, hi = threshold
    if op == "between":
        return f"entre {lo} et {hi}"
    if op == "gt":
        return f"plus de {lo}"
    if op == "gte":
        return f"au moins {lo}"
    if op == "lt":
        return f"moins de {lo}"
    return f"au plus {lo}"


async def _evaluation_rows(db: AsyncSession, user: User) -> List[Tuple[Stagiaire, Evaluation]]:
    """Stagiaires évalués (et leur évaluation la plus récente), dans le périmètre
    de l'utilisateur. Conforme à la logique de l'app : une seule évaluation par
    stagiaire (l'encadrant écrase l'évaluation existante)."""
    latest = (
        select(Evaluation.stagiaire_id, func.max(Evaluation.id).label("max_id"))
        .group_by(Evaluation.stagiaire_id)
        .subquery()
    )
    stmt = (
        select(Stagiaire, Evaluation)
        .join(latest, latest.c.stagiaire_id == Stagiaire.id)
        .join(Evaluation, Evaluation.id == latest.c.max_id)
        .order_by(Stagiaire.nom_complet)
    )
    if user.role == UserRole.ENCADRANT:
        stmt = stmt.where(Stagiaire.encadrant_id == user.id)
    result = await db.execute(stmt)
    return list(result.all())


def _format_evaluation_line(s: Stagiaire, score5: float, score20: float, scale20: bool = True) -> str:
    if scale20:
        return f"- {s.nom_complet} : {_fmt_score(score20)}/20 (moyenne des critères {_fmt_score(score5)}/5)"
    return f"- {s.nom_complet} : {_fmt_score(score5)}/5 (moyenne des critères)"


async def handle_stagiaire_info(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    candidate = _extract_after(
        message,
        ["stagiaire", "infos", "informations", "info ", "fiche", "détails", "details", "parle-moi de", "parle moi de"],
    )
    candidate = _clean_candidate(candidate)
    stagiaires = []
    if candidate:
        stagiaires = await _scoped_stagiaires(db, user, search=candidate)
    if not stagiaires:
        digits = re.search(r"\d{6,8}", message)
        if digits:
            cin = digits.group(0)
            stmt = select(Stagiaire).where(Stagiaire.cin == cin)
            if user.role == UserRole.ENCADRANT:
                stmt = stmt.where(Stagiaire.encadrant_id == user.id)
            result = await db.execute(stmt)
            stagiaires = list(result.scalars().all())
    if not stagiaires:
        return (
            "",
            "Je n'ai trouvé aucun stagiaire correspondant à votre demande. "
            "Vérifiez le nom ou le CIN, ou demandez « liste des stagiaires ».",
        )
    s = stagiaires[0]
    context = (
        f"Informations sur le stagiaire demandé ({s.nom_complet}) :\n"
        f"{_format_stagiaire(s)}\n"
        f"- email : {s.email or 'N/A'} | téléphone : {s.telephone or 'N/A'}\n"
        f"- date de naissance : {s.date_naissance or 'N/A'} | période : {s.periode_stage or 'N/A'}"
    )
    return context, f"Voici les informations concernant {s.nom_complet} :\n{_format_stagiaire(s)}"


async def handle_stagiaires_par_encadrant(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    candidate = _clean_candidate(_extract_after(message, _ENCADRANT_KEYWORDS))
    encadrant = None
    if candidate:
        result = await db.execute(
            select(Encadrant).where(
                (Encadrant.nom + " " + Encadrant.prenom).ilike(f"%{candidate}%")
                | (Encadrant.prenom + " " + Encadrant.nom).ilike(f"%{candidate}%")
            )
        )
        encadrant = result.scalars().first()
    if not encadrant:
        return (
            "",
            "Précisez le nom de l'encadrant (par exemple : « quels stagiaires sont affectés à l'encadrant X ? »).",
        )
    stagiaires = await _scoped_stagiaires(db, user, encadrant_id=encadrant.user_id)
    if not stagiaires:
        return (
            f"Aucun stagiaire n'est affecté à l'encadrant {encadrant.prenom} {encadrant.nom}.",
            f"Aucun stagiaire n'est actuellement affecté à l'encadrant {encadrant.prenom} {encadrant.nom}.",
        )
    if "combien" in normalize(message) or "nombre" in normalize(message):
        context = (
            f"Nombre de stagiaires affectés à l'encadrant {encadrant.prenom} {encadrant.nom} : "
            f"{len(stagiaires)}.\n{_names_list(stagiaires)}"
        )
        fallback = f"{len(stagiaires)} stagiaire(s) sont affectés à l'encadrant {encadrant.prenom} {encadrant.nom}."
        return context, fallback
    context = (
        f"Stagiaires affectés à l'encadrant {encadrant.prenom} {encadrant.nom} ({len(stagiaires)} au total) :\n"
        f"{_names_list(stagiaires)}"
    )
    fallback = (
        f"{len(stagiaires)} stagiaire(s) sont affectés à l'encadrant {encadrant.prenom} {encadrant.nom} :\n"
        f"{_names_list(stagiaires)}"
    )
    return context, fallback


async def handle_encadrant_info(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    """Informations sur un encadrant (code, nom, nombre de stagiaires autorisés).

    Conforme à l'API de l'application : l'email de l'encadrant n'est pas exposé.
    Le nombre de stagiaires respecte le périmètre de l'utilisateur.
    """
    candidate = _clean_candidate(_extract_after(message, _ENCADRANT_KEYWORDS))
    encadrant = None
    if candidate:
        result = await db.execute(
            select(Encadrant).where(
                (Encadrant.nom + " " + Encadrant.prenom).ilike(f"%{candidate}%")
                | (Encadrant.prenom + " " + Encadrant.nom).ilike(f"%{candidate}%")
            )
        )
        encadrant = result.scalars().first()
    if not encadrant:
        return (
            "",
            "Précisez le nom de l'encadrant (par exemple : « qui est l'encadrant Moez ? »).",
        )
    stagiaires = await _scoped_stagiaires(db, user, encadrant_id=encadrant.user_id)
    context = (
        f"Informations sur l'encadrant {encadrant.prenom} {encadrant.nom} :\n"
        f"- code : {encadrant.code_encadrant}\n"
        f"- nom complet : {encadrant.prenom} {encadrant.nom}\n"
        f"- nombre de stagiaires associés (dans le périmètre autorisé) : {len(stagiaires)}"
    )
    fallback = (
        f"{encadrant.prenom} {encadrant.nom} (code {encadrant.code_encadrant}) "
        f"encadre {len(stagiaires)} stagiaire(s) dans votre périmètre."
    )
    return context, fallback


async def handle_evaluations_en_attente(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    stagiaires = await _stagiaires_without_evaluation(db, user)
    if not stagiaires:
        return (
            "Tous les stagiaires autorisés ont une évaluation.",
            "Tous les stagiaires ont déjà été évalués.",
        )
    context = (
        f"Stagiaires n'ayant pas encore d'évaluation ({len(stagiaires)} au total) :\n"
        f"{_names_list(stagiaires)}"
    )
    fallback = (
        f"{len(stagiaires)} stagiaire(s) n'ont pas encore terminé leur évaluation :\n"
        f"{_names_list(stagiaires)}"
    )
    return context, fallback


async def handle_rapports_manquants(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    stagiaires = await _stagiaires_without_rapport(db, user)
    if not stagiaires:
        return (
            "Tous les stagiaires autorisés ont soumis leur rapport.",
            "Tous les stagiaires ont soumis leur rapport.",
        )
    context = (
        f"Stagiaires n'ayant pas encore soumis leur rapport ({len(stagiaires)} au total) :\n"
        f"{_names_list(stagiaires)}"
    )
    fallback = (
        f"{len(stagiaires)} stagiaire(s) n'ont pas encore soumis leur rapport :\n"
        f"{_names_list(stagiaires)}"
    )
    return context, fallback


async def handle_attestations(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    stagiaires = await _stagiaires_with_attestation(db, user)
    if not stagiaires:
        return (
            "Aucun stagiaire autorisé ne dispose d'une attestation générée.",
            "Aucun stagiaire n'a encore d'attestation générée.",
        )
    context = (
        f"Stagiaires disposant d'une attestation ({len(stagiaires)} au total) :\n"
        f"{_names_list(stagiaires)}"
    )
    fallback = (
        f"{len(stagiaires)} stagiaire(s) ont une attestation générée :\n"
        f"{_names_list(stagiaires)}"
    )
    return context, fallback


async def handle_count_attestations(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    """Compte les attestations réelles en base (toutes ou celles du mois en cours).

    Le chiffre provient toujours de la base : jamais inventé.
    """
    normalized = normalize(message)
    period_label = "au total"
    count_expr = func.count()
    if "stagiaire" in normalized:
        count_expr = func.count(func.distinct(Attestation.stagiaire_id))
    stmt = select(count_expr).select_from(Attestation)
    if "mois" in normalized:
        period_label = "ce mois-ci"
        start_of_month = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        stmt = stmt.where(Attestation.created_at >= start_of_month)

    if user.role == UserRole.ENCADRANT:
        stmt = stmt.where(
            exists(
                select(Stagiaire.id).where(
                    Stagiaire.id == Attestation.stagiaire_id,
                    Stagiaire.encadrant_id == user.id,
                )
            )
        )

    result = await db.execute(stmt)
    count = result.scalar() or 0

    context = f"Nombre d'attestations délivrées {period_label} : {count}."
    if count == 0:
        fallback = f"Il n'y a aucune attestation délivrée {period_label}."
    elif count == 1:
        fallback = f"1 attestation a été délivrée {period_label}."
    else:
        fallback = f"{count} attestations ont été délivrées {period_label}."
    return context, fallback


async def handle_validations_en_attente(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    stagiaires = await _stagiaires_en_attente_validation(db, user)
    if not stagiaires:
        return (
            "Stagiaires en attente de validation : aucun (0). Tous les stagiaires autorisés ont déjà une validation.",
            "Tous les stagiaires ont déjà été validés.",
        )
    context = (
        f"Stagiaires en attente de validation ({len(stagiaires)} au total) :\n"
        f"{_names_list(stagiaires)}"
    )
    fallback = (
        f"{len(stagiaires)} stagiaire(s) sont encore en attente de validation :\n"
        f"{_names_list(stagiaires)}"
    )
    return context, fallback


async def handle_stagiaires_valides(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    stagiaires = await _stagiaires_valides(db, user)
    if not stagiaires:
        return (
            "Stagiaires validés : aucun (0). Aucun stagiaire autorisé n'a de validation.",
            "Aucun stagiaire n'a encore été validé.",
        )
    context = (
        f"Stagiaires validés ({len(stagiaires)} au total) :\n"
        f"{_names_list(stagiaires)}"
    )
    fallback = (
        f"{len(stagiaires)} stagiaire(s) ont été validés :\n"
        f"{_names_list(stagiaires)}"
    )
    return context, fallback


async def handle_count_stagiaires(db: AsyncSession, user: User, message: str, en_stage: bool) -> Tuple[str, str]:
    kwargs = {"statuts_stage": ["Stage en cours"]} if en_stage else {}
    stagiaires = await _scoped_stagiaires(db, user, **kwargs)
    total = len(stagiaires)
    label = "actuellement en stage" if en_stage else "enregistrés au total"
    context = f"Nombre de stagiaires {label} : {total}."
    fallback = f"Actuellement, il y a {total} stagiaire(s) {label}."
    return context, fallback


async def handle_liste_stagiaires(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    normalized = normalize(message)
    kwargs = {}
    if "en stage" in normalized or "en cours" in normalized:
        kwargs["statuts_stage"] = ["Stage en cours"]
    stagiaires = await _scoped_stagiaires(db, user, **kwargs)
    if not stagiaires:
        return (
            "Aucun stagiaire n'est enregistré dans la plateforme.",
            "Aucun stagiaire n'est enregistré dans la plateforme.",
        )
    if kwargs:
        label = "actuellement en stage"
    else:
        label = "enregistrés au total"
    context = (
        f"Liste des stagiaires {label} ({len(stagiaires)} au total) :\n"
        f"{_names_list(stagiaires)}"
    )
    fallback = (
        f"Voici la liste des stagiaires {label} ({len(stagiaires)}) :\n"
        f"{_names_list(stagiaires)}"
    )
    return context, fallback


async def handle_evaluation_threshold(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    """Stagiaires dont la note moyenne vérifie un seuil (comptage ou liste).

    Le seuil est extrait de la question et appliqué sur les notes réelles
    calculées depuis la base. Le LLM ne calcule rien.
    """
    threshold = _extract_threshold(message)
    if not threshold:
        return (
            "",
            "Précisez un seuil (par exemple : « combien de stagiaires ont obtenu plus de 15 ? »).",
        )
    op, lo, hi = threshold
    rows = await _evaluation_rows(db, user)
    if not rows:
        return (
            "Aucune évaluation n'est enregistrée dans la base.",
            "Je ne trouve aucune évaluation enregistrée dans la base pour le moment.",
        )

    if op == "between":
        lo20 = _threshold_to_20(lo)
        hi20 = _threshold_to_20(hi)
        scale20 = hi > 5
    else:
        lo20 = _threshold_to_20(lo)
        hi20 = None
        scale20 = lo > 5

    matched = []
    for s, e in rows:
        score5, score20 = _evaluation_scores(e)
        if score20 is None:
            continue
        if op == "between":
            ok = lo20 <= score20 <= hi20
        elif op == "gt":
            ok = score20 > lo20
        elif op == "gte":
            ok = score20 >= lo20
        elif op == "lt":
            ok = score20 < lo20
        else:
            ok = score20 <= lo20
        if ok:
            matched.append((s, score5, score20))

    label = _threshold_label(threshold)
    scale_label = "sur 20" if scale20 else "sur 5"
    if not matched:
        message_aucun = f"Aucun stagiaire n'a obtenu une note {label} ({scale_label})."
        return message_aucun, message_aucun

    lines = "\n".join(
        _format_evaluation_line(s, s5, s20, scale20=scale20) for s, s5, s20 in matched[:MAX_LIST]
    )
    if len(matched) > MAX_LIST:
        lines += f"\n- ... et {len(matched) - MAX_LIST} autre(s)"

    normalized = normalize(message)
    if "combien" in normalized or "nombre" in normalized:
        context = f"Nombre de stagiaires avec une note {label} ({scale_label}) : {len(matched)}.\n{lines}"
        fallback = f"{len(matched)} stagiaire(s) ont obtenu une note {label} ({scale_label})."
        return context, fallback

    context = (
        f"Stagiaires avec une note {label} ({scale_label}) : {len(matched)} au total :\n{lines}"
    )
    fallback = (
        f"{len(matched)} stagiaire(s) ont obtenu une note {label} ({scale_label}) :\n{lines}"
    )
    return context, fallback


async def _resolve_evaluation_stagiaire(
    db: AsyncSession, user: User, message: str
) -> Tuple[Optional[Stagiaire], str]:
    """Résout le stagiaire cité dans la question (avec gestion des ambiguïtés)."""
    candidate = _clean_candidate(
        _extract_after(message, ["moyenne de", "note de", "moyenne", "note"])
    )
    if not candidate:
        return None, "Précisez le nom du stagiaire (par exemple : « quelle est la note de Seif ? »)."
    stagiaires = await _scoped_stagiaires(db, user, search=candidate)
    if not stagiaires:
        return None, (
            f"Je n'ai trouvé aucun stagiaire correspondant à « {candidate} ». "
            "Vérifiez le nom ou le CIN."
        )
    if len(stagiaires) > 1:
        names = "\n".join(f"- {s.nom_complet}" for s in stagiaires[:MAX_LIST])
        return None, (
            f"Plusieurs stagiaires correspondent à « {candidate} » :\n{names}\n"
            "Précisez le nom complet pour obtenir la note exacte."
        )
    return stagiaires[0], ""


async def _handle_evaluation_of(db: AsyncSession, user: User, message: str, moyenne: bool) -> Tuple[str, str]:
    stagiaire, error = await _resolve_evaluation_stagiaire(db, user, message)
    if not stagiaire:
        return "", error
    result = await db.execute(select(Evaluation).where(Evaluation.stagiaire_id == stagiaire.id))
    evaluation = result.scalar_one_or_none()
    if not evaluation:
        message_absent = f"Je ne trouve aucune évaluation enregistrée pour {stagiaire.nom_complet}."
        return message_absent, message_absent
    score5, score20 = _evaluation_scores(evaluation)
    if score5 is None:
        message_vide = (
            f"Une évaluation existe pour {stagiaire.nom_complet} mais aucun critère n'a été noté."
        )
        return message_vide, message_vide
    breakdown = "\n".join(
        f"- {_CRITERION_LABELS[c]} : {getattr(evaluation, c)}/5"
        for c in _EVALUATION_CRITERIA
        if getattr(evaluation, c) is not None
    )
    context = (
        f"Évaluation de {stagiaire.nom_complet} :\n{breakdown}\n"
        f"Moyenne des critères : {_fmt_score(score5)}/5, soit {_fmt_score(score20)}/20."
    )
    if moyenne:
        fallback = f"La moyenne de {stagiaire.nom_complet} est de {_fmt_score(score5)}/5, soit {_fmt_score(score20)}/20."
    else:
        fallback = f"La note de {stagiaire.nom_complet} est de {_fmt_score(score20)}/20 (moyenne des critères : {_fmt_score(score5)}/5)."
    return context, fallback


async def handle_evaluation_note(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    return await _handle_evaluation_of(db, user, message, moyenne=False)


async def handle_evaluation_moyenne(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    return await _handle_evaluation_of(db, user, message, moyenne=True)


async def handle_evaluation_best(db: AsyncSession, user: User, message: str) -> Tuple[str, str]:
    """Stagiaire(s) ayant obtenu la meilleure note (calculée depuis la base)."""
    rows = await _evaluation_rows(db, user)
    if not rows:
        return (
            "Aucune évaluation n'est enregistrée dans la base.",
            "Je ne trouve aucune évaluation enregistrée dans la base pour le moment.",
        )
    scored = []
    for s, e in rows:
        score5, score20 = _evaluation_scores(e)
        if score20 is not None:
            scored.append((s, score5, score20))
    if not scored:
        return (
            "Aucune évaluation ne contient de note de critère renseignée.",
            "Je ne trouve aucune évaluation notée dans la base pour le moment.",
        )
    best = max(scored, key=lambda x: x[2])
    winners = [x for x in scored if x[2] == best[2]]
    lines = "\n".join(_format_evaluation_line(s, s5, s20) for s, s5, s20 in winners)
    context = f"Meilleure note ({_fmt_score(best[2])}/20) :\n{lines}"
    if len(winners) == 1:
        s, s5, s20 = winners[0]
        fallback = (
            f"Le stagiaire ayant obtenu la meilleure note est {s.nom_complet} "
            f"avec {_fmt_score(s20)}/20 (moyenne des critères {_fmt_score(s5)}/5)."
        )
    else:
        fallback = (
            f"Plusieurs stagiaires partagent la meilleure note de {_fmt_score(best[2])}/20 :\n{lines}"
        )
    return context, fallback


# Types de requête pour le routage hybride
class QueryType:
    DATABASE = "database"
    RAG = "rag"
    HYBRID = "hybrid"
    GENERAL = "general"


# Mots-clés pour détecter les questions documentaires/procédurales (RAG)
#
# Important : les noms d'entités métier (« attestation », « rapport »,
# « évaluation », « validation » au sens du nom) ne sont volontairement PAS
# répétés ici, alors qu'ils sont présents dans _DATABASE_KEYWORDS. Ces mots
# désignent l'objet dont on parle, pas l'intention de consulter un document
# à son sujet — une question purement métier comme « Combien d'attestations
# ont été délivrées ? » ne doit pas être classée HYBRID simplement parce que
# « attestation » apparaît aussi dans une liste RAG. La véritable intention
# documentaire (« que dit le document sur les attestations ? ») est captée
# séparément par _DOCUMENT_INTENT_PATTERNS, qui a la priorité sur ces
# mots-clés. Les formes verbales/procédurales (« valider », « évaluer »)
# restent ici : elles n'apparaissent pas dans les questions DATABASE
# habituelles (qui utilisent les noms « validation(s) », « évaluation(s) »).
_RAG_KEYWORDS = [
    "procédure", "procedure", "processus", "comment", "comment faire",
    "étape", "etapes", "modalité", "modalites", "règle", "regle",
    "critère", "criteres", "condition", "conditions",
    "document", "documents", "documentation", "proposition",
    "pièce", "pieces", "justificatif", "justificatifs",
    "valider", "soumission", "soumettre", "dépôt", "depot",
    "fin de stage", "fin stage", "clôture", "cloture",
    "certificat", "diplôme", "diplome",
    "evaluer", "noter", "notation", "grille",
    "compte rendu", "compte-rendu",
    "encadrement", "encadrer", "tuteur", "maître de stage", "maitre de stage",
    "convention", "conventions", "accord", "charte",
    "règlement", "reglement", "politique", "directive",
    "exemple", "modèle", "modele", "template",
    "prérequis", "prerequis", "éligibilité", "eligibilite",
    "délai", "delai", "date limite", "échéance", "echeance",
]

# Mots-clés pour les questions métier structurées (DATABASE)
_DATABASE_KEYWORDS = [
    "combien", "nombre", "quantité", "quantite",
    "liste", "lister", "qui sont", "quels sont",
    "note de", "moyenne de", "note ", "moyenne ",
    "meilleur", "meilleure", "maximum", "minimum",
    "plus de", "moins de", "au moins", "supérieur", "supérieure", "inférieur", "inférieure",
    "encadrant", "encadre", "affecté", "affectes",
    "stagiaire", "stagiaires", "étudiant", "etudiants",
    "attestation", "attestations",
    "validation", "validations", "valides",
    # Note : « validé » (singulier) est volontairement exclu ici. Une fois
    # normalisé (accents retirés), il devient la sous-chaîne "valide", qui
    # matcherait aussi à tort des mots sans rapport comme « invalide » /
    # « invalidée ». Les questions sur un stagiaire "validé" au singulier
    # sont déjà couvertes par detect_intent() (voir has_valide_word, qui
    # utilise une frontière de mot) via le repli en fin de detect_query_type.
    "évaluation", "evaluations", "évalué", "evalues",
    "rapport", "rapports", "soumis", "déposé", "depose",
    "en attente", "en cours", "manquant", "manquants",
]

# Mots-clés pour les salutations/généralités (GENERAL)
_GENERAL_KEYWORDS = [
    "bonjour", "salut", "hello", "bonsoir", "coucou", "hi",
    "merci", "super", "parfait", "génial", "genial", "cool", "excellent",
    "au revoir", "bye", "bientôt", "bientot", "adieu",
    "aide", "help", "quoi", "qui es", "qui êtes", "presentation", "présentation",
]


# `m` (le message analysé) est produit par normalize(), qui retire les accents.
# Les listes de mots-clés ci-dessus contiennent des formes accentuées (pour la
# lisibilité) : sans normalisation, un mot-clé comme « évaluation » ou
# « supérieur » ne matcherait jamais puisque m ne contient plus d'accents.
# On pré-normalise donc les mots-clés une seule fois au chargement du module.
_GENERAL_KEYWORDS_N = tuple(sorted({normalize(k) for k in _GENERAL_KEYWORDS}))
_DATABASE_KEYWORDS_N = tuple(sorted({normalize(k) for k in _DATABASE_KEYWORDS}))
_RAG_KEYWORDS_N = tuple(sorted({normalize(k) for k in _RAG_KEYWORDS}))


# Expressions indiquant une demande explicite sur le CONTENU d'un document
# (proposition, documentation, procédure décrite dans un texte, etc.).
# Quand l'une de ces expressions est présente, la requête est routée en
# priorité vers le RAG, même si elle contient par ailleurs des mots-clés
# DATABASE (« attestation », « stagiaire », « évaluation », « rapport »,
# « validation », « encadrant »...). La présence d'un tel mot ne signifie pas
# que l'utilisateur veut une donnée chiffrée de la base : il veut ce qu'un
# document dit à ce sujet. Cette règle a la priorité sur la classification
# par mots-clés DATABASE/RAG ci-dessous (elle ne la remplace pas : les
# mots-clés DATABASE/RAG continuent de fonctionner normalement pour toutes
# les autres formulations).
_DOCUMENT_INTENT_PATTERNS = tuple(
    re.compile(p)
    for p in (
        r"\bque\s+(dit|contient|prevoit|precise|indique)\s+(le\s+|la\s+|les\s+)?(document|documentation|proposition)\b",
        r"\bselon\s+(le\s+|la\s+|les\s+)?(document|documentation|proposition)s?\b",
        r"\bd\s*apres\s+(le\s+|la\s+|les\s+)?(document|documentation|proposition)s?\b",
        r"\bdans\s+(le\s+|la\s+|les\s+)?(document|documentation|proposition)s?\b",
        r"\binformations?\s+(sont\s+)?contenues?\s+dans\b",
        r"\bprocedure\s+decrite\s+dans\b",
        r"\bregles?\s+decrites?\s+dans\b",
    )
)


def _has_document_intent(m: str) -> bool:
    """True si le message demande explicitement le contenu d'un document."""
    return any(p.search(m) for p in _DOCUMENT_INTENT_PATTERNS)


def detect_query_type(message: str) -> str:
    """Détermine le type de requête pour le routage hybride.

    Returns:
        QueryType.DATABASE, QueryType.RAG, QueryType.HYBRID, ou QueryType.GENERAL
    """
    if not rag_settings.RAG_ENABLED:
        # Si RAG désactivé, tout passe par DATABASE ou GENERAL
        m = normalize(message)
        if any(k in m for k in _GENERAL_KEYWORDS_N):
            return QueryType.GENERAL
        return QueryType.DATABASE

    m = normalize(message)

    # Priorité : une demande explicite sur le contenu d'un document est
    # toujours RAG, avant même la détection des salutations ou des
    # mots-clés DATABASE/RAG (voir _DOCUMENT_INTENT_PATTERNS ci-dessus).
    if _has_document_intent(m):
        return QueryType.RAG

    # Détection salutation/général -> GENERAL
    if any(k in m for k in _GENERAL_KEYWORDS_N):
        return QueryType.GENERAL

    # Détection mots-clés DATABASE
    has_database_keywords = any(k in m for k in _DATABASE_KEYWORDS_N)

    # Détection mots-clés RAG
    has_rag_keywords = any(k in m for k in _RAG_KEYWORDS_N)

    # Logique de décision
    if has_database_keywords and has_rag_keywords:
        return QueryType.HYBRID
    elif has_database_keywords:
        return QueryType.DATABASE
    elif has_rag_keywords:
        return QueryType.RAG
    else:
        # Par défaut, si intention métier détectée -> DATABASE, sinon RAG
        intent = detect_intent(message)
        if intent:
            return QueryType.DATABASE
        return QueryType.RAG


async def handle_rag_query(message: str) -> Tuple[str, str]:
    """Gère une question purement documentaire (RAG).

    Renvoie (rag_context, fallback_answer).
    Le fallback indique que l'info n'est pas dans les docs.
    """
    if not rag_settings.RAG_ENABLED:
        return "", "Le module de recherche documentaire n'est pas activé."

    unavailable_fallback = (
        "La recherche documentaire est momentanément indisponible "
        "(dépendances ou index non chargés). "
        "Vous pouvez poser une question sur les données de la plateforme "
        "(stagiaires, notes, attestations, etc.)."
    )

    try:
        # Import local pour éviter les imports circulaires. Cet import déclenche
        # aussi le chargement de sentence-transformers/FAISS (app.rag.embeddings,
        # app.rag.vector_store) : si ces dépendances sont absentes, mal installées,
        # ou si le modèle/l'index ne peuvent pas être chargés, l'exception est
        # levée ici et ne doit jamais faire planter la requête de chat (HTTP 500).
        from app.rag.service import get_rag_service

        service = get_rag_service()
        initialized = await service.initialize()
        if not initialized:
            logger.warning("RAG : service non initialisé, réponse dégradée renvoyée.")
            return "", unavailable_fallback

        result = service.query(message)
    except Exception as e:
        logger.error("RAG : erreur inattendue lors du traitement de la question : %s", e, exc_info=True)
        return "", unavailable_fallback

    if not result["enabled"] or result["chunks_found"] == 0:
        fallback = (
            "Je ne trouve pas cette information dans les documents disponibles "
            "(procédures, rapports, conventions, etc.). "
            "Essayez de reformuler ou posez une question sur les données de la plateforme "
            "(stagiaires, notes, attestations, etc.)."
        )
        return "", fallback

    rag_context = result["context"]
    fallback = (
        f"D'après les documents indexés ({result['chunks_found']} extrait(s) pertinent(s)) :\n\n"
        f"{result['sources']}\n\n"
        f"Note : Cette réponse est basée sur la documentation. "
        f"Pour des données temps réel (notes, statuts, comptes), consultez la base."
    )
    return rag_context, fallback


def detect_intent(message: str) -> Optional[str]:
    """Renvoie l'intention données détectée (ou None).

    L'ordre est important : les intentions les plus spécifiques sont testées
    avant les plus générales pour éviter les faux positifs (par exemple
    « donne-moi le nombre de stagiaires » ne doit pas être classé comme
    une demande d'informations sur un stagiaire précis).
    """
    m = normalize(message)

    if "stagiaire" in m and ("encadrant" in m or "encadre" in m or "encadres" in m):
        return "stagiaires_par_encadrant"

    # Informations sur un encadrant (sans mention de stagiaire précis).
    if ("encadrant" in m or "encadre" in m or "encadres" in m) and any(
        k in m for k in ("infos", "informations", "details", "qui est", "fiche")
    ):
        if "stagiaire" not in m:
            return "encadrant_info"

    # Évaluations / notes : avant les intentions génériques pour éviter les
    # faux positifs (« donne-moi les étudiants qui ont plus de 15 » ne doit
    # pas être classé comme une demande d'infos sur un stagiaire).
    threshold = _extract_threshold(m)
    if threshold and any(
        k in m for k in ("note", "score", "moyenne", "stagiaire", "etudiant",
                         "eleve", "obtenu", "eu", "ont", "combien", "nombre", "qui", "liste")
    ):
        return "evaluation_threshold"

    if "moyenne" in m:
        return "evaluation_moyenne"

    if "meilleur" in m and any(k in m for k in ("note", "score", "evaluation")):
        return "evaluation_best"

    if "note" in m:
        return "evaluation_note"

    # Informations sur un stagiaire précis : exclure les demandes de
    # comptage / liste (le mot générique « donne moi » ne suffit pas).
    if any(k in m for k in ("infos", "informations", "fiche", "details", "parle moi", "donne moi")):
        if "encadrant" not in m and not any(c in m for c in ("nombre", "combien", "liste")):
            return "stagiaire_info"

    # Validations (avant les intentions « rapport »/« évaluation » pour
    # intercepter « rapport ... en attente de validation »).
    # Note : on utilise une frontière de mot (\b) pour « valide » afin d'éviter
    # les faux positifs sur des mots qui le contiennent comme sous-chaîne sans
    # rapport avec les validations de stage (ex. « invalide », « invalider »).
    has_valide_word = re.search(r"\bvalide", m) is not None
    if "validation" in m and any(k in m for k in ("attente", "pas", "sans", "manqu", "encore", "non")):
        return "validations_en_attente"
    if has_valide_word and any(k in m for k in ("pas", "sans", "encore", "non", "attente", "manqu")):
        return "validations_en_attente"
    if "validation" in m and any(k in m for k in ("qui", "recu", "tous", "quels", "ont", "liste", "montre")):
        return "stagiaires_valides"
    if has_valide_word:
        return "stagiaires_valides"

    if "evaluation" in m and any(k in m for k in ("pas", "attente", "sans", "manqu", "encore", "terminer", "non", "qui")):
        return "evaluations_en_attente"

    if "rapport" in m and any(k in m for k in ("pas", "attente", "sans", "manqu", "encore", "soumis", "depose", "non", "qui")):
        return "rapports_manquants"

    if "attestation" in m and ("combien" in m or "nombre" in m):
      return "count_attestations"

    if "attestation" in m and not any(k in m for k in ("combien", "nombre")):
      return "attestations"

    if ("combien" in m or "nombre" in m) and "stagiaire" in m:
        return "count_stagiaires"

    if "stagiaire" in m and any(k in m for k in ("liste", "quels", "qui", "tous", "montre", "affiche", "voir", "sont")):
        return "liste_stagiaires"

    return None


async def handle_intent(
    db: AsyncSession, user: User, message: str, intent: str
) -> Tuple[str, str]:
    """Exécute l'intention et renvoie (data_context, fallback_answer)."""
    if intent == "stagiaire_info":
        return await handle_stagiaire_info(db, user, message)
    if intent == "stagiaires_par_encadrant":
        return await handle_stagiaires_par_encadrant(db, user, message)
    if intent == "encadrant_info":
        return await handle_encadrant_info(db, user, message)
    if intent == "evaluations_en_attente":
        return await handle_evaluations_en_attente(db, user, message)
    if intent == "rapports_manquants":
        return await handle_rapports_manquants(db, user, message)
    if intent == "attestations":
        return await handle_attestations(db, user, message)
    if intent == "count_attestations":
        return await handle_count_attestations(db, user, message)
    if intent == "validations_en_attente":
        return await handle_validations_en_attente(db, user, message)
    if intent == "stagiaires_valides":
        return await handle_stagiaires_valides(db, user, message)
    if intent == "count_stagiaires":
        normalized = normalize(message)
        return await handle_count_stagiaires(
            db, user, message,
            en_stage="en stage" in normalized or "en cours" in normalized,
        )
    if intent == "liste_stagiaires":
        return await handle_liste_stagiaires(db, user, message)
    if intent == "evaluation_threshold":
        return await handle_evaluation_threshold(db, user, message)
    if intent == "evaluation_note":
        return await handle_evaluation_note(db, user, message)
    if intent == "evaluation_moyenne":
        return await handle_evaluation_moyenne(db, user, message)
    if intent == "evaluation_best":
        return await handle_evaluation_best(db, user, message)
    if intent == "rag_query":
        return await handle_rag_query(message)
    return "", "Je n'ai pas compris votre demande. Pouvez-vous reformuler ?"