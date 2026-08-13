from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.evaluation import EvaluationCreate, EvaluationOut
from app.services import evaluation_service
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/evaluations", tags=["Évaluations"])


@router.get("/{stagiaire_id}", response_model=EvaluationOut)
async def get_evaluation(stagiaire_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    evaluation = await evaluation_service.get_evaluation_by_stagiaire(db, stagiaire_id)
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucune évaluation trouvée")
    encadrant_nom = None
    if evaluation.encadrant:
        encadrant_nom = f"{evaluation.encadrant.prenom} {evaluation.encadrant.nom}".strip() or evaluation.encadrant.nom
    return EvaluationOut(
        id=evaluation.id,
        stagiaire_id=evaluation.stagiaire_id,
        encadrant_id=evaluation.encadrant_id,
        qualite_travail=evaluation.qualite_travail,
        autonomie=evaluation.autonomie,
        ponctualite=evaluation.ponctualite,
        communication=evaluation.communication,
        esprit_equipe=evaluation.esprit_equipe,
        capacite_apprentissage=evaluation.capacite_apprentissage,
        initiative=evaluation.initiative,
        respect_consignes=evaluation.respect_consignes,
        recommandation_embauche=evaluation.recommandation_embauche,
        commentaire=evaluation.commentaire,
        date_creation=evaluation.date_creation,
        date_modification=evaluation.date_modification,
        encadrant_nom=encadrant_nom,
    )


@router.post("/{stagiaire_id}", response_model=EvaluationOut)
async def save_evaluation(
    stagiaire_id: int,
    data: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    eval_data = data.model_dump(exclude_unset=True)
    evaluation = await evaluation_service.create_or_update_evaluation(db, stagiaire_id, current_user, eval_data)
    encadrant_nom = None
    if evaluation.encadrant:
        encadrant_nom = f"{evaluation.encadrant.prenom} {evaluation.encadrant.nom}".strip() or evaluation.encadrant.nom
    return EvaluationOut(
        id=evaluation.id,
        stagiaire_id=evaluation.stagiaire_id,
        encadrant_id=evaluation.encadrant_id,
        qualite_travail=evaluation.qualite_travail,
        autonomie=evaluation.autonomie,
        ponctualite=evaluation.ponctualite,
        communication=evaluation.communication,
        esprit_equipe=evaluation.esprit_equipe,
        capacite_apprentissage=evaluation.capacite_apprentissage,
        initiative=evaluation.initiative,
        respect_consignes=evaluation.respect_consignes,
        recommandation_embauche=evaluation.recommandation_embauche,
        commentaire=evaluation.commentaire,
        date_creation=evaluation.date_creation,
        date_modification=evaluation.date_modification,
        encadrant_nom=encadrant_nom,
    )
