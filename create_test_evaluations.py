"""Create test evaluation data for chatbot testing."""
import asyncio
from sqlalchemy import select
from app.database import async_session, init_db
from app.models.evaluation import Evaluation
from app.models.stagiaire import Stagiaire
from app.models.user import User


async def create_test_evaluations():
    await init_db()
    session = async_session()
    try:
        # Get encadrant user (id=3)
        result = await session.execute(select(User).where(User.id == 3))
        encadrant = result.scalar_one_or_none()
        if not encadrant:
            print("Encadrant user not found")
            return

        print(f"Using encadrant: {encadrant.email} (id={encadrant.id})")

        # Get stagiaires assigned to this encadrant
        result = await session.execute(
            select(Stagiaire).where(Stagiaire.encadrant_id == encadrant.id).limit(10)
        )
        stagiaires = list(result.scalars().all())
        print(f"Found {len(stagiaires)} stagiaires for this encadrant")

        if not stagiaires:
            print("No stagiaires found for this encadrant")
            return

        # Create evaluations with varying scores
        test_scores = [
            # (stagiaire_index, score_value) - score_value is 1-5 for all criteria
            (0, 5),  # Excellent - 20/20
            (1, 4),  # Good - 16/20
            (2, 3),  # Average - 12/20
            (3, 2),  # Below average - 8/20
            (4, 4),  # Good - 16/20
            (5, 3),  # Average - 12/20
            (6, 5),  # Excellent - 20/20
            (7, 2),  # Below average - 8/20
            (8, 4),  # Good - 16/20
            (9, 3),  # Average - 12/20
        ]

        for idx, score in test_scores:
            if idx >= len(stagiaires):
                break
            stagiaire = stagiaires[idx]
            
            # Check if evaluation already exists
            result = await session.execute(
                select(Evaluation).where(Evaluation.stagiaire_id == stagiaire.id)
            )
            existing = result.scalar_one_or_none()
            if existing:
                print(f"Evaluation already exists for {stagiaire.nom_complet}, skipping")
                continue

            eval_obj = Evaluation(
                stagiaire_id=stagiaire.id,
                encadrant_id=encadrant.id,
                qualite_travail=score,
                autonomie=score,
                ponctualite=score,
                communication=score,
                esprit_equipe=score,
                capacite_apprentissage=score,
                initiative=score,
                respect_consignes=score,
                recommandation_embauche="oui" if score >= 4 else "a_considerer" if score >= 3 else "non",
                commentaire=f"Évaluation de test pour {stagiaire.nom_complet}",
            )
            session.add(eval_obj)
            print(f"Created evaluation for {stagiaire.nom_complet}: {score}/5 ({score*4}/20)")

        await session.commit()
        print("Done! Test evaluations created.")

        # Verify
        result = await session.execute(select(Evaluation))
        all_evals = list(result.scalars().all())
        print(f"Total evaluations in database: {len(all_evals)}")

    except Exception as e:
        await session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(create_test_evaluations())