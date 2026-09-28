import pytest
from sqlalchemy import select

from app.database import async_session
from app.models.encadrant import Encadrant
from app.models.user import UserRole
from app.models.stagiaire import Stagiaire
from app.models.evaluation import Evaluation
from app.models.rapport import Rapport
from app.models.attestation import Attestation
from app.models.validation import Validation
from app.services import chat_intents
from tests.conftest import create_user, create_stagiaire

INTENT_CASES = [
    ("Combien de stagiaires sont actuellement en stage ?", "count_stagiaires"),
    ("Quel est le nombre de stagiaires au total ?", "count_stagiaires"),
    ("Donne-moi le nombre de stagiaires.", "count_stagiaires"),
    ("Combien avons-nous de stagiaires ?", "count_stagiaires"),
    ("Quels stagiaires sont affectés à cet encadrant ?", "stagiaires_par_encadrant"),
    ("Quels stagiaires sont encadrés par Moez ?", "stagiaires_par_encadrant"),
    ("Quels stagiaires sont encadres par Moez ?", "stagiaires_par_encadrant"),
    ("Combien de stagiaires sont associés à l'encadrant Moez ?", "stagiaires_par_encadrant"),
    ("Qui est l'encadrant Moez ?", "encadrant_info"),
    ("Donne-moi les informations sur l'encadrant Moez", "encadrant_info"),
    ("Quels stagiaires n'ont pas encore terminé leur évaluation ?", "evaluations_en_attente"),
    ("Quelles évaluations sont actuellement en attente ?", "evaluations_en_attente"),
    ("Quels stagiaires n'ont pas encore soumis leur rapport ?", "rapports_manquants"),
    ("Quels rapports sont encore en attente de validation ?", "validations_en_attente"),
    ("Quels stagiaires n'ont pas encore été validés ?", "validations_en_attente"),
    ("Quels stagiaires ont été validés ?", "stagiaires_valides"),
    ("Qui a reçu sa validation ?", "stagiaires_valides"),
    ("Quels stagiaires sont validés ?", "stagiaires_valides"),
    ("Qui a reçu son attestation ?", "attestations"),
    ("Combien d'attestations ont été délivrées ce mois-ci ?", "count_attestations"),
    ("Combien d'attestations ont été délivrées ce mois ?", "count_attestations"),
    ("Combien d'attestations ont été générées ce mois-ci ?", "count_attestations"),
    ("Quel est le nombre d'attestations délivrées ce mois-ci ?", "count_attestations"),
    ("Combien d'attestations ont été délivrées au total ?", "count_attestations"),
    ("Donne-moi les informations concernant le stagiaire Jean Dupont", "stagiaire_info"),
    ("Quels sont les stagiaires enregistrés ?", "liste_stagiaires"),
    ("Quels sont les stagiaires actuellement en stage ?", "liste_stagiaires"),
    ("Donne-moi la liste des stagiaires.", "liste_stagiaires"),
    ("Combien de stagiaires ont obtenu plus de 15 ?", "evaluation_threshold"),
    ("Quels stagiaires ont obtenu plus de 15 ?", "evaluation_threshold"),
    ("Qui a eu plus de 15 ?", "evaluation_threshold"),
    ("Combien ont eu plus de 15 ?", "evaluation_threshold"),
    ("Les stagiaires avec une note supérieure à 15", "evaluation_threshold"),
    ("Donne-moi les étudiants qui ont plus de 15", "evaluation_threshold"),
    ("Combien de stagiaires ont obtenu au moins 4 ?", "evaluation_threshold"),
    ("Combien de stagiaires ont une note inférieure à 10 ?", "evaluation_threshold"),
    ("Quels stagiaires ont une note entre 10 et 15 ?", "evaluation_threshold"),
    ("Quelle est la note de Seif ?", "evaluation_note"),
    ("Quelle est la note d'Anizi Seif Eddine ?", "evaluation_note"),
    ("Quelle est la moyenne de Seif ?", "evaluation_moyenne"),
    ("Qui a eu la meilleure note ?", "evaluation_best"),
    ("Quel stagiaire a obtenu la meilleure note ?", "evaluation_best"),
    ("Quel est le meilleur score ?", "evaluation_best"),
    ("Bonjour, comment vas-tu ?", None),
    ("Merci beaucoup !", None),
    # Régression : « invalide » contient la sous-chaîne « valide » mais ne doit
    # pas déclencher l'intention "stagiaires_valides" (bug de routage corrigé).
    ("Le formulaire soumis est invalide.", None),
    ("Cette demande a été invalidée par erreur.", None),
    # Les vraies variantes de « valide » doivent toujours déclencher l'intention.
    ("Le stagiaire est-il valide ?", "stagiaires_valides"),
]


def test_detect_intent():
    for message, expected in INTENT_CASES:
        assert chat_intents.detect_intent(message) == expected, message


def test_normalize():
    assert chat_intents.normalize("Évaluation déjà déposée ?") == "evaluation deja deposee"


def test_extract_threshold():
    cases = [
        ("plus de 15", ("gt", 15, None)),
        ("supérieure à 14", ("gt", 14, None)),
        ("au moins 15", ("gte", 15, None)),
        ("inférieure à 10", ("lt", 10, None)),
        ("moins de 8", ("lt", 8, None)),
        ("entre 10 et 15", ("between", 10, 15)),
        ("plus que 12", ("gt", 12, None)),
        ("rien de numérique ici", None),
    ]
    for message, expected in cases:
        assert chat_intents._extract_threshold(message) == expected, message


def test_threshold_to_20():
    assert chat_intents._threshold_to_20(15) == 15.0
    assert chat_intents._threshold_to_20(4) == 16.0
    assert chat_intents._threshold_to_20(3) == 12.0


async def _add_evaluation(db, stagiaire, encadrant_id, **criteria):
    db.add(
        Evaluation(
            stagiaire_id=stagiaire.id,
            encadrant_id=encadrant_id,
            **criteria,
        )
    )


async def _seed_evaluations(db):
    user = await create_user(db, "rh_eval@test.tn")
    fort = await create_stagiaire(db, "Eleve Fort")
    moyen = await create_stagiaire(db, "Eleve Moyen")
    limite = await create_stagiaire(db, "Eleve Limite")
    faible = await create_stagiaire(db, "Eleve Faible")
    for stagiaire, val in [(fort, 5), (moyen, 3), (limite, 4), (faible, 1)]:
        await _add_evaluation(
            db, stagiaire, user.id,
            qualite_travail=val, autonomie=val, ponctualite=val, communication=val,
            esprit_equipe=val, capacite_apprentissage=val, initiative=val, respect_consignes=val,
        )
    await db.commit()
    return user, fort, moyen, limite, faible


async def test_evaluation_threshold_count_and_list():
    async with async_session() as db:
        user, fort, moyen, limite, faible = await _seed_evaluations(db)

        context, fallback = await chat_intents.handle_evaluation_threshold(
            db, user, "combien de stagiaires ont obtenu plus de 15 ?"
        )
        assert "2" in fallback
        assert "Eleve Fort" in context
        assert "Eleve Limite" in context

        _, fallback_list = await chat_intents.handle_evaluation_threshold(
            db, user, "quels stagiaires ont obtenu plus de 15 ?"
        )
        assert "Eleve Fort" in fallback_list
        assert "Eleve Limite" in fallback_list
        assert "Eleve Moyen" not in fallback_list

        _, fallback_min = await chat_intents.handle_evaluation_threshold(
            db, user, "combien de stagiaires ont obtenu au moins 4 ?"
        )
        assert "2" in fallback_min

        context_bas, fallback_bas = await chat_intents.handle_evaluation_threshold(
            db, user, "combien de stagiaires ont une note inférieure à 10 ?"
        )
        assert "1" in fallback_bas
        assert "Eleve Faible" in context_bas

        _, fallback_entre = await chat_intents.handle_evaluation_threshold(
            db, user, "quels stagiaires ont une note entre 10 et 15 ?"
        )
        assert "Eleve Moyen" in fallback_entre
        assert "Eleve Fort" not in fallback_entre


async def test_evaluation_note_and_moyenne():
    async with async_session() as db:
        user = await create_user(db, "rh_note@test.tn")
        s = await create_stagiaire(db, "Anizi Seif Eddine")
        await _add_evaluation(
            db, s, user.id,
            qualite_travail=4, autonomie=4, ponctualite=4, communication=4,
            esprit_equipe=4, capacite_apprentissage=4, initiative=4, respect_consignes=3,
        )
        await db.commit()

        _, fallback = await chat_intents.handle_evaluation_note(
            db, user, "quelle est la note d'Anizi Seif Eddine ?"
        )
        assert "15.5" in fallback  # (4*7 + 3)/8 = 3.88 -> 15.5/20
        assert "3.88" in fallback

        _, fallback_moyenne = await chat_intents.handle_evaluation_moyenne(
            db, user, "quelle est la moyenne de Seif ?"
        )
        assert "3.88" in fallback_moyenne
        assert "15.5" in fallback_moyenne

        _, absent = await chat_intents.handle_evaluation_note(
            db, user, "quelle est la note de stagiaire inconnu ?"
        )
        assert "aucun stagiaire" in absent


async def test_evaluation_note_no_data():
    async with async_session() as db:
        user = await create_user(db, "rh_vide@test.tn")
        await create_stagiaire(db, "Sans évaluation")
        await db.commit()

        _, fallback = await chat_intents.handle_evaluation_note(
            db, user, "quelle est la note de Sans évaluation ?"
        )
        assert "aucune évaluation" in fallback


async def test_evaluation_partial_criteria():
    """Test evaluation score with only some criteria filled (NULL handling)."""
    async with async_session() as db:
        user = await create_user(db, "rh_partial@test.tn")
        s = await create_stagiaire(db, "Partiel Test")
        # Only 4 criteria filled, all 5/5 -> average 5/5 = 20/20
        await _add_evaluation(
            db, s, user.id,
            qualite_travail=5, autonomie=5, ponctualite=5, communication=5,
            # esprit_equipe, capacite_apprentissage, initiative, respect_consignes = NULL
        )
        await db.commit()

        _, fallback = await chat_intents.handle_evaluation_note(
            db, user, "quelle est la note de Partiel Test ?"
        )
        assert "20" in fallback
        assert "5" in fallback


async def test_evaluation_all_null_criteria():
    """Test evaluation with all criteria NULL -> no score."""
    async with async_session() as db:
        user = await create_user(db, "rh_null@test.tn")
        s = await create_stagiaire(db, "Null Test")
        # Evaluation row exists but all criteria NULL
        db.add(Evaluation(stagiaire_id=s.id, encadrant_id=user.id, commentaire="En attente"))
        await db.commit()

        _, fallback = await chat_intents.handle_evaluation_note(
            db, user, "quelle est la note de Null Test ?"
        )
        assert "aucun critère" in fallback


async def test_evaluation_threshold_no_data():
    async with async_session() as db:
        user = await create_user(db, "rh_vide2@test.tn")
        await create_stagiaire(db, "Sans évaluation")
        await db.commit()

        _, fallback = await chat_intents.handle_evaluation_threshold(
            db, user, "combien de stagiaires ont obtenu plus de 15 ?"
        )
        assert "aucune évaluation" in fallback


async def test_evaluation_best():
    async with async_session() as db:
        user, fort, moyen, limite, faible = await _seed_evaluations(db)

        _, fallback = await chat_intents.handle_evaluation_best(
            db, user, "qui a eu la meilleure note ?"
        )
        assert "Eleve Fort" in fallback
        assert "20" in fallback

        await _add_evaluation(
            db, limite, user.id,
            qualite_travail=5, autonomie=5, ponctualite=5, communication=5,
            esprit_equipe=5, capacite_apprentissage=5, initiative=5, respect_consignes=5,
        )
        await db.flush()
        _, fallback_tie = await chat_intents.handle_evaluation_best(
            db, user, "quel est le meilleur score ?"
        )
        assert "Plusieurs stagiaires" in fallback_tie


async def test_evaluation_ambiguous_name():
    async with async_session() as db:
        user = await create_user(db, "rh_ambig@test.tn")
        await create_stagiaire(db, "Seif Premier")
        await create_stagiaire(db, "Seif Second")
        await db.commit()

        _, fallback = await chat_intents.handle_evaluation_note(
            db, user, "quelle est la note de Seif ?"
        )
        assert "Plusieurs stagiaires" in fallback


async def test_evaluation_encadrant_scope():
    async with async_session() as db:
        encadrant = await create_user(db, "enc_eval@test.tn", role=UserRole.ENCADRANT, nom="Moez")
        other = await create_user(db, "rh_other@test.tn")
        own = await create_stagiaire(db, "Mon évalué", user_id=encadrant.id)
        theirs = await create_stagiaire(db, "Évalué des autres", user_id=other.id)
        for stagiaire in (own, theirs):
            await _add_evaluation(
                db, stagiaire, other.id,
                qualite_travail=5, autonomie=5, ponctualite=5, communication=5,
                esprit_equipe=5, capacite_apprentissage=5, initiative=5, respect_consignes=5,
            )
        await db.commit()

        _, fallback = await chat_intents.handle_evaluation_threshold(
            db, encadrant, "quels stagiaires ont obtenu plus de 15 ?"
        )
        assert "Mon évalué" in fallback
        assert "Évalué des autres" not in fallback

        _, note = await chat_intents.handle_evaluation_note(
            db, encadrant, "quelle est la note de Évalué des autres ?"
        )
        assert "aucun stagiaire" in note


async def test_count_stagiaires():
    async with async_session() as db:
        user = await create_user(db, "rh@test.tn")
        await create_stagiaire(db, "Alice Test", statut_stage="Stage en cours")
        await create_stagiaire(db, "Bob Test", statut_stage="Stage en cours")
        await create_stagiaire(db, "Claire Test", statut_stage="Stage terminé")
        await db.commit()

        context, fallback = await chat_intents.handle_count_stagiaires(
            db, user, "combien de stagiaires en stage ?", en_stage=True
        )
        assert "2" in fallback
        assert "2" in context

        _, fallback_total = await chat_intents.handle_count_stagiaires(
            db, user, "combien de stagiaires au total ?", en_stage=False
        )
        assert "3" in fallback_total


async def test_stagiaire_info_by_name_and_cin():
    async with async_session() as db:
        user = await create_user(db, "rh2@test.tn")
        await create_stagiaire(db, "Jean Dupont", statut_stage="Stage en cours", cin="12345678")
        await db.commit()

        context, fallback = await chat_intents.handle_stagiaire_info(
            db, user, "donne moi les informations concernant le stagiaire jean"
        )
        assert "Jean Dupont" in fallback

        _, fallback_cin = await chat_intents.handle_stagiaire_info(
            db, user, "quelles sont les infos du stagiaire 12345678"
        )
        assert "Jean Dupont" in fallback_cin

        _, fallback_absent = await chat_intents.handle_stagiaire_info(
            db, user, "les infos du stagiaire inconnu xyz"
        )
        assert "aucun" in fallback_absent


async def test_stagiaires_par_encadrant():
    async with async_session() as db:
        encadrant = await create_user(db, "enc@test.tn", role=UserRole.ENCADRANT, nom="Moez")
        db.add(Encadrant(code_encadrant="ENC001", user_id=encadrant.id, nom="Moez", prenom="User"))
        await create_stagiaire(db, "Alice Enc", user_id=encadrant.id)
        await create_stagiaire(db, "Bob Enc", user_id=encadrant.id)
        await db.commit()

        _, fallback = await chat_intents.handle_stagiaires_par_encadrant(
            db, encadrant, "quels stagiaires sont affectés à l'encadrant Moez"
        )
        assert "Alice Enc" in fallback
        assert "Bob Enc" in fallback

        _, fallback_encadres = await chat_intents.handle_stagiaires_par_encadrant(
            db, encadrant, "quels stagiaires sont encadrés par Moez ?"
        )
        assert "Alice Enc" in fallback_encadres
        assert "Bob Enc" in fallback_encadres

        _, fallback_count = await chat_intents.handle_stagiaires_par_encadrant(
            db, encadrant, "combien de stagiaires sont associés à l'encadrant Moez ?"
        )
        assert "2 stagiaire(s)" in fallback_count
        assert "Alice Enc" not in fallback_count


async def test_liste_stagiaires_filtre_en_stage():
    async with async_session() as db:
        user = await create_user(db, "rh_list@test.tn")
        await create_stagiaire(db, "En cours A", statut_stage="Stage en cours")
        await create_stagiaire(db, "Terminé B", statut_stage="Stage terminé")
        await db.commit()

        _, fallback = await chat_intents.handle_liste_stagiaires(
            db, user, "quels sont les stagiaires actuellement en stage ?"
        )
        assert "En cours A" in fallback
        assert "Terminé B" not in fallback

        _, fallback_total = await chat_intents.handle_liste_stagiaires(
            db, user, "donne-moi la liste des stagiaires"
        )
        assert "En cours A" in fallback_total
        assert "Terminé B" in fallback_total


async def test_encadrant_info():
    async with async_session() as db:
        encadrant = await create_user(db, "enc_info@test.tn", role=UserRole.ENCADRANT, nom="Moez", prenom="Ali")
        db.add(Encadrant(code_encadrant="ENC042", user_id=encadrant.id, nom="Moez", prenom="Ali"))
        await create_stagiaire(db, "Stagiaire de Moez", user_id=encadrant.id)
        await db.commit()

        context, fallback = await chat_intents.handle_encadrant_info(
            db, encadrant, "qui est l'encadrant Moez ?"
        )
        assert "ENC042" in fallback
        assert "Ali Moez" in fallback
        assert "1 stagiaire" in fallback
        assert "enc_info@test.tn" not in fallback
        assert "enc_info@test.tn" not in context

        _, absent = await chat_intents.handle_encadrant_info(
            db, encadrant, "qui est l'encadrant inconnu xyz ?"
        )
        assert "Précisez" in absent


async def test_evaluations_en_attente():
    async with async_session() as db:
        user = await create_user(db, "rh3@test.tn")
        evaluated = await create_stagiaire(db, "Évalué Test")
        pending = await create_stagiaire(db, "En attente Test")
        db.add(Evaluation(stagiaire_id=evaluated.id, encadrant_id=user.id, commentaire="ok"))
        await db.commit()

        _, fallback = await chat_intents.handle_evaluations_en_attente(db, user, "evaluations en attente")
        assert "En attente Test" in fallback
        assert "Évalué Test" not in fallback


async def test_rapports_manquants():
    async with async_session() as db:
        user = await create_user(db, "rh4@test.tn")
        submitted = await create_stagiaire(db, "Rapport OK")
        missing = await create_stagiaire(db, "Rapport manquant")
        db.add(Rapport(stagiaire_id=submitted.id, file_pdf="x.pdf", uploaded_by=user.id))
        await db.commit()

        _, fallback = await chat_intents.handle_rapports_manquants(db, user, "rapports en attente")
        assert "Rapport manquant" in fallback
        assert "Rapport OK" not in fallback


async def test_attestations():
    async with async_session() as db:
        user = await create_user(db, "rh5@test.tn")
        attested = await create_stagiaire(db, "Avec attestation")
        plain = await create_stagiaire(db, "Sans attestation")
        db.add(Attestation(stagiaire_id=attested.id, numero_attestation="ATT-001", generated_by=user.id))
        await db.commit()

        _, fallback = await chat_intents.handle_attestations(db, user, "qui a reçu son attestation")
        assert "Avec attestation" in fallback
        assert "Sans attestation" not in fallback


async def test_count_attestations_this_month():
    from datetime import datetime, timedelta, timezone

    async with async_session() as db:
        user = await create_user(db, "rh_count@test.tn")
        s1 = await create_stagiaire(db, "Count Un")
        s2 = await create_stagiaire(db, "Count Deux")
        s3 = await create_stagiaire(db, "Count Trois")
        now = datetime.now(timezone.utc)
        last_month = now - timedelta(days=40)
        db.add(Attestation(stagiaire_id=s1.id, numero_attestation="ATT-C1", generated_by=user.id, created_at=now))
        db.add(Attestation(stagiaire_id=s2.id, numero_attestation="ATT-C2", generated_by=user.id, created_at=now))
        db.add(Attestation(stagiaire_id=s3.id, numero_attestation="ATT-C3", generated_by=user.id, created_at=last_month))
        await db.commit()

        ctx, fallback = await chat_intents.handle_count_attestations(
            db, user, "combien d'attestations ont été délivrées ce mois-ci ?"
        )
        assert "2" in ctx
        assert "2" in fallback
        assert "Count Un" not in fallback

        ctx_total, fallback_total = await chat_intents.handle_count_attestations(
            db, user, "combien d'attestations au total ?"
        )
        assert "3" in ctx_total
        assert "3" in fallback_total


async def test_count_attestations_zero():
    async with async_session() as db:
        user = await create_user(db, "rh_zero@test.tn")
        await db.commit()

        _, fallback = await chat_intents.handle_count_attestations(
            db, user, "combien d'attestations ont été délivrées ce mois-ci ?"
        )
        assert "aucune" in fallback


async def test_count_attestations_encadrant_scope():
    from datetime import datetime, timezone

    async with async_session() as db:
        encadrant = await create_user(db, "enc_count@test.tn", role=UserRole.ENCADRANT, nom="Fares")
        other = await create_user(db, "rh_count2@test.tn")
        own = await create_stagiaire(db, "Attest moi", user_id=encadrant.id)
        theirs = await create_stagiaire(db, "Attest autre", user_id=other.id)
        now = datetime.now(timezone.utc)
        db.add(Attestation(stagiaire_id=own.id, numero_attestation="ATT-E1", generated_by=encadrant.id, created_at=now))
        db.add(Attestation(stagiaire_id=theirs.id, numero_attestation="ATT-E2", generated_by=other.id, created_at=now))
        await db.commit()

        ctx, fallback = await chat_intents.handle_count_attestations(
            db, encadrant, "combien d'attestations ont été délivrées ce mois-ci ?"
        )
        assert "1" in ctx
        assert "Attest autre" not in fallback


async def test_encadrant_scope_limits_data():
    """Un encadrant ne voit que ses propres stagiaires."""
    async with async_session() as db:
        encadrant = await create_user(db, "enc2@test.tn", role=UserRole.ENCADRANT, nom="Sami")
        other_rh = await create_user(db, "rh6@test.tn")
        await create_stagiaire(db, "Mon stagiaire", user_id=encadrant.id)
        await create_stagiaire(db, "Stagiaire des autres", user_id=other_rh.id)
        await db.commit()

        _, fallback = await chat_intents.handle_liste_stagiaires(db, encadrant, "liste des stagiaires")
        assert "Mon stagiaire" in fallback
        assert "Stagiaire des autres" not in fallback

        rh_all = await chat_intents.handle_liste_stagiaires(db, other_rh, "liste des stagiaires")
        assert "Stagiaire des autres" in rh_all[1]
        assert "Mon stagiaire" in rh_all[1]


async def test_validations_en_attente():
    async with async_session() as db:
        user = await create_user(db, "rh7@test.tn")
        valide = await create_stagiaire(db, "Déjà validé")
        attente = await create_stagiaire(db, "En attente validation")
        db.add(Validation(stagiaire_id=valide.id, encadrant_id=user.id, status="valide"))
        await db.commit()

        _, fallback = await chat_intents.handle_validations_en_attente(
            db, user, "quels rapports sont encore en attente de validation ?"
        )
        assert "En attente validation" in fallback
        assert "Déjà validé" not in fallback


async def test_stagiaires_valides():
    async with async_session() as db:
        user = await create_user(db, "rh8@test.tn")
        valide = await create_stagiaire(db, "Stage validé Test")
        non_valide = await create_stagiaire(db, "Non validé Test")
        db.add(Validation(stagiaire_id=valide.id, encadrant_id=user.id, status="valide"))
        db.add(Validation(stagiaire_id=non_valide.id, encadrant_id=user.id, status="refuse"))
        await db.commit()

        _, fallback = await chat_intents.handle_stagiaires_valides(
            db, user, "quels stagiaires ont été validés ?"
        )
        assert "Stage validé Test" in fallback
        assert "Non validé Test" not in fallback


async def test_validations_encadrant_scope():
    """Un encadrant ne voit les validations que de ses propres stagiaires."""
    async with async_session() as db:
        encadrant = await create_user(db, "enc3@test.tn", role=UserRole.ENCADRANT, nom="Karim")
        other_rh = await create_user(db, "rh9@test.tn")
        own = await create_stagiaire(db, "Mon validé", user_id=encadrant.id)
        other = await create_stagiaire(db, "Validé des autres", user_id=other_rh.id)
        db.add(Validation(stagiaire_id=own.id, encadrant_id=encadrant.id, status="valide"))
        db.add(Validation(stagiaire_id=other.id, encadrant_id=other_rh.id, status="valide"))
        await db.commit()

        _, fallback = await chat_intents.handle_stagiaires_valides(
            db, encadrant, "quels stagiaires sont validés ?"
        )
        assert "Mon validé" in fallback
        assert "Validé des autres" not in fallback

        _, attente = await chat_intents.handle_validations_en_attente(
            db, encadrant, "quels stagiaires n'ont pas été validés ?"
        )
        assert "Validé des autres" not in attente


# ---------------------------------------------------------------------------
# Régression : routage du type de requête (DATABASE / RAG / HYBRID / GENERAL)
# ---------------------------------------------------------------------------

def test_accented_keywords_normalized_for_matching():
    """Régression : les mots-clés accentués (« évaluation », « supérieure », ...)
    doivent être présents sous leur forme normalisée (sans accent) dans les
    ensembles utilisés pour le routage. Sans cela, un mot-clé accentué ne
    peut jamais matcher un message normalisé (accents retirés) et est donc
    silencieusement ignoré."""
    assert "evaluation" in chat_intents._DATABASE_KEYWORDS_N
    assert "superieure" in chat_intents._DATABASE_KEYWORDS_N
    assert "superieur" in chat_intents._DATABASE_KEYWORDS_N
    assert "inferieure" in chat_intents._DATABASE_KEYWORDS_N
    # ... mais pas la racine ambiguë "valide" (voir test suivant).
    assert "valide" not in chat_intents._DATABASE_KEYWORDS_N


def test_query_type_invalide_is_not_misrouted():
    """« invalide » ne doit pas être confondu avec les mots-clés de
    validation lors du routage DATABASE/RAG."""
    query_type = chat_intents.detect_query_type("Ce document semble invalide, que faire ?")
    assert query_type != chat_intents.QueryType.DATABASE


# Questions documentaires (« que dit/contient/prévoit... le document/la
# documentation/la proposition ») : doivent être routées RAG en priorité,
# même si elles contiennent des mots-clés DATABASE (attestation, rapport,
# évaluation, validation...).
_DOCUMENT_INTENT_CASES = [
    "Que contient le document concernant les attestations de stage ?",
    "Que dit la documentation concernant les attestations de stage ?",
    "Selon les documents, quelles sont les informations contenues dans une attestation de stage ?",
    "Que prévoit la proposition concernant la génération des attestations ?",
    "Que dit le document concernant les rapports de stage ?",
    "Que dit le document concernant les évaluations ?",
    "Que dit le document concernant les validations ?",
    "Que prévoit la proposition concernant l'architecture de l'assistant conversationnel ?",
]

# Questions métier structurées équivalentes, sans indicateur documentaire :
# doivent rester DATABASE (pas HYBRID, pas RAG), y compris pour les mêmes
# entités (attestation, rapport, évaluation) que ci-dessus.
_DATABASE_ONLY_CASES = [
    "Combien de stagiaires ont une attestation ?",
    "Quels stagiaires ont une attestation ?",
    "Liste les stagiaires ayant une attestation.",
    "Combien d'attestations ont été délivrées ?",
    "Donne-moi les attestations générées ce mois-ci.",
    "Combien de rapports ont été soumis ?",
    "Quels stagiaires n'ont pas encore d'évaluation ?",
    "Quels rapports sont en attente de validation ?",
]


@pytest.mark.parametrize("message", _DOCUMENT_INTENT_CASES)
def test_document_reference_questions_are_routed_to_rag(message):
    """Une question qui demande explicitement le contenu d'un document doit
    être classée RAG, même si elle mentionne une entité métier (attestation,
    rapport, évaluation, validation) qui existe aussi dans la base."""
    assert chat_intents.detect_query_type(message) == chat_intents.QueryType.RAG


@pytest.mark.parametrize("message", _DATABASE_ONLY_CASES)
def test_plain_business_questions_stay_database(message):
    """Une question métier structurée sans indicateur documentaire doit
    rester DATABASE (ne doit pas basculer en RAG ou HYBRID)."""
    assert chat_intents.detect_query_type(message) == chat_intents.QueryType.DATABASE


# ---------------------------------------------------------------------------
# Régression : handle_rag_query ne doit jamais laisser fuiter une exception
# (dépendances RAG absentes, index corrompu, etc.) -> réponse dégradée, pas
# de HTTP 500 pour l'utilisateur final.
# ---------------------------------------------------------------------------

async def test_handle_rag_query_degrades_gracefully_on_import_error(monkeypatch):
    import app.rag.service as rag_service_module

    def _boom():
        raise ImportError("sentence_transformers n'est pas installé")

    monkeypatch.setattr(rag_service_module, "get_rag_service", _boom)

    rag_context, fallback = await chat_intents.handle_rag_query("Que dit le règlement intérieur ?")

    assert rag_context == ""
    assert fallback  # une réponse de repli en français est toujours renvoyée
    assert "indisponible" in fallback.lower()


async def test_handle_rag_query_degrades_gracefully_when_not_initialized(monkeypatch):
    import app.rag.service as rag_service_module

    class _FakeService:
        async def initialize(self):
            return False

        def query(self, message):
            raise AssertionError("query() ne doit pas être appelé si l'init a échoué")

    monkeypatch.setattr(rag_service_module, "get_rag_service", lambda: _FakeService())

    rag_context, fallback = await chat_intents.handle_rag_query("Que disent les documents ?")

    assert rag_context == ""
    assert "indisponible" in fallback.lower()