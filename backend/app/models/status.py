import enum
from datetime import date


class StatutStage(str, enum.Enum):
    STAGE_NON_DEBUTE = "Stage non débuté"
    STAGE_EN_COURS = "Stage en cours"
    STAGE_SUSPENDU = "Stage suspendu"
    STAGE_TERMINE = "Stage terminé"
    STAGE_VALIDE = "Stage validé"
    STAGE_REFUSE = "Stage refusé"


class StatutDossier(str, enum.Enum):
    ATTESTATION_GENEREE = "Attestation générée"
    ATTESTATION_ENVOYEE = "Attestation envoyée"


DATE_BASED_STATUSES = {
    StatutStage.STAGE_NON_DEBUTE,
    StatutStage.STAGE_EN_COURS,
    StatutStage.STAGE_TERMINE,
}

MANUAL_STATUSES = {
    StatutStage.STAGE_SUSPENDU,
    StatutStage.STAGE_VALIDE,
    StatutStage.STAGE_REFUSE,
}


def compute_statut_stage(date_debut: date, date_fin: date) -> StatutStage:
    today = date.today()
    if today < date_debut:
        return StatutStage.STAGE_NON_DEBUTE
    elif today <= date_fin:
        return StatutStage.STAGE_EN_COURS
    else:
        return StatutStage.STAGE_TERMINE


def is_date_based(statut) -> bool:
    if isinstance(statut, str):
        try:
            statut = StatutStage(statut)
        except ValueError:
            return False
    return statut in DATE_BASED_STATUSES


STAGE_TRANSITIONS = {
    StatutStage.STAGE_NON_DEBUTE: [StatutStage.STAGE_EN_COURS],
    StatutStage.STAGE_EN_COURS: [StatutStage.STAGE_SUSPENDU, StatutStage.STAGE_TERMINE, StatutStage.STAGE_VALIDE, StatutStage.STAGE_REFUSE],
    StatutStage.STAGE_SUSPENDU: [StatutStage.STAGE_EN_COURS],
    StatutStage.STAGE_TERMINE: [StatutStage.STAGE_EN_COURS, StatutStage.STAGE_VALIDE, StatutStage.STAGE_REFUSE],
    StatutStage.STAGE_VALIDE: [],
    StatutStage.STAGE_REFUSE: [],
}

DOSSIER_TRANSITIONS = {
    None: [StatutDossier.ATTESTATION_GENEREE],
    StatutDossier.ATTESTATION_GENEREE: [StatutDossier.ATTESTATION_ENVOYEE, StatutDossier.ATTESTATION_GENEREE],
    StatutDossier.ATTESTATION_ENVOYEE: [StatutDossier.ATTESTATION_GENEREE],
}


def can_transition_stage(current: StatutStage, target: StatutStage) -> bool:
    return target in STAGE_TRANSITIONS.get(current, [])


def can_transition_dossier(current, target: StatutDossier) -> bool:
    return target in DOSSIER_TRANSITIONS.get(current, [])


def get_allowed_stage_transitions(current: StatutStage):
    return STAGE_TRANSITIONS.get(current, [])


def get_allowed_dossier_transitions(current):
    return DOSSIER_TRANSITIONS.get(current, [])


OLD_STATUT_MAP = {
    "Stage non débuté": (StatutStage.STAGE_NON_DEBUTE, None),
    "Stage en cours": (StatutStage.STAGE_EN_COURS, None),
    "Stage suspendu": (StatutStage.STAGE_SUSPENDU, None),
    "Stage terminé": (StatutStage.STAGE_TERMINE, None),
    "Validé": (StatutStage.STAGE_VALIDE, None),
    "Refusé": (StatutStage.STAGE_REFUSE, None),
    "Attestation générée": (StatutStage.STAGE_VALIDE, StatutDossier.ATTESTATION_GENEREE),
    "Attestation envoyée": (StatutStage.STAGE_VALIDE, StatutDossier.ATTESTATION_ENVOYEE),
}
