import httpx
import pytest

from app.database import async_session
from app.main import app
from app.models.stagiaire import Stagiaire
from tests.conftest import create_user

pytestmark = pytest.mark.asyncio


async def _login(client: httpx.AsyncClient, email: str, password: str = "test123"):
    response = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


async def test_chat_requires_auth():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/chat", json={"message": "bonjour"})
        assert response.status_code == 401


async def test_full_chat_flow_with_persistence():
    async with async_session() as db:
        user = await create_user(db, "flow@test.tn")
        await db.commit()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        token = await _login(client, "flow@test.tn")
        headers = {"Authorization": f"Bearer {token}"}

        first = await client.post("/api/chat", json={"message": "bonjour"}, headers=headers)
        assert first.status_code == 200
        first_data = first.json()
        conversation_id = first_data["conversation_id"]
        assert conversation_id
        assert first_data["response"]

        second = await client.post(
            "/api/chat",
            json={"message": "merci", "conversation_id": conversation_id},
            headers=headers,
        )
        assert second.status_code == 200
        assert second.json()["conversation_id"] == conversation_id

        conversations = await client.get("/api/chat/conversations", headers=headers)
        assert conversations.status_code == 200
        data = conversations.json()
        assert len(data) == 1
        assert data[0]["id"] == conversation_id
        assert data[0]["message_count"] == 4

        messages = await client.get(f"/api/chat/conversations/{conversation_id}/messages", headers=headers)
        assert messages.status_code == 200
        history = messages.json()
        assert len(history) == 4
        assert [m["role"] for m in history] == ["user", "assistant", "user", "assistant"]
        assert history[0]["content"] == "bonjour"


async def test_conversation_isolation_between_users():
    async with async_session() as db:
        await create_user(db, "owner@test.tn")
        await create_user(db, "intruder@test.tn")
        await db.commit()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        owner_token = await _login(client, "owner@test.tn")
        intruder_token = await _login(client, "intruder@test.tn")

        created = await client.post(
            "/api/chat",
            json={"message": "message privé"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        conversation_id = created.json()["conversation_id"]

        intruder_headers = {"Authorization": f"Bearer {intruder_token}"}
        read = await client.get(
            f"/api/chat/conversations/{conversation_id}/messages", headers=intruder_headers
        )
        assert read.status_code == 404

        write = await client.post(
            "/api/chat",
            json={"message": "tentative", "conversation_id": conversation_id},
            headers=intruder_headers,
        )
        assert write.status_code == 404

        delete = await client.delete(
            f"/api/chat/conversations/{conversation_id}", headers=intruder_headers
        )
        assert delete.status_code == 404

        owner_delete = await client.delete(
            f"/api/chat/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert owner_delete.status_code == 204

        owner_convs = await client.get(
            "/api/chat/conversations", headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert owner_convs.json() == []


async def test_conversations_ordered_by_recent_activity():
    async with async_session() as db:
        await create_user(db, "order@test.tn")
        await db.commit()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        token = await _login(client, "order@test.tn")
        headers = {"Authorization": f"Bearer {token}"}

        first = await client.post("/api/chat", json={"message": "première conversation"}, headers=headers)
        first_id = first.json()["conversation_id"]
        second = await client.post("/api/chat", json={"message": "deuxième conversation"}, headers=headers)
        second_id = second.json()["conversation_id"]

        listed = await client.get("/api/chat/conversations", headers=headers)
        assert [c["id"] for c in listed.json()] == [second_id, first_id]

        await client.post(
            "/api/chat",
            json={"message": "activité récente", "conversation_id": first_id},
            headers=headers,
        )

        listed_after = await client.get("/api/chat/conversations", headers=headers)
        assert [c["id"] for c in listed_after.json()] == [first_id, second_id]


async def test_data_question_uses_real_data():
    async with async_session() as db:
        user = await create_user(db, "data@test.tn")
        db.add(Stagiaire(nom_complet="Zoé Données", statut_stage="Stage en cours"))
        db.add(Stagiaire(nom_complet="Léo Données", statut_stage="Stage en cours"))
        await db.commit()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        token = await _login(client, "data@test.tn")
        response = await client.post(
            "/api/chat",
            json={"message": "combien de stagiaires sont actuellement en stage ?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert "2" in response.json()["response"]


async def test_rate_limiting():
    from app.config import settings

    old_max = settings.CHAT_RATE_LIMIT_MAX
    settings.CHAT_RATE_LIMIT_MAX = 3
    try:
        async with async_session() as db:
            await create_user(db, "limit@test.tn")
            await db.commit()

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            token = await _login(client, "limit@test.tn")
            headers = {"Authorization": f"Bearer {token}"}
            statuses = []
            for _ in range(5):
                response = await client.post("/api/chat", json={"message": "bonjour"}, headers=headers)
                statuses.append(response.status_code)
            assert statuses[:3] == [200, 200, 200]
            assert statuses[3] == 429
            assert statuses[4] == 429
    finally:
        settings.CHAT_RATE_LIMIT_MAX = old_max


async def test_rag_question_never_returns_500_when_dependencies_unavailable(monkeypatch):
    """Régression bout en bout : une question documentaire ne doit jamais
    provoquer un HTTP 500, même si les dépendances RAG (sentence-transformers,
    FAISS) sont absentes ou cassées."""
    import app.rag.service as rag_service_module

    def _broken_get_rag_service():
        raise ImportError("sentence_transformers n'est pas installé")

    monkeypatch.setattr(rag_service_module, "get_rag_service", _broken_get_rag_service)

    async with async_session() as db:
        await create_user(db, "rag_missing_deps@test.tn")
        await db.commit()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        token = await _login(client, "rag_missing_deps@test.tn")
        response = await client.post(
            "/api/chat",
            json={"message": "Quelle est la procédure de soumission d'un rapport de stage ?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json()["response"]


async def test_document_question_about_attestations_does_not_return_db_answer():
    """Régression bout en bout du bug rapporté : une question documentaire
    contenant le mot « attestation » (ex. « Que dit le document concernant
    les attestations de stage ? ») ne doit pas renvoyer la réponse figée de
    la base de données ("N stagiaire(s) ont une attestation générée..."),
    même quand des stagiaires avec attestation existent en base."""
    from app.models.attestation import Attestation

    async with async_session() as db:
        user = await create_user(db, "doc_attestation@test.tn")
        stagiaire = Stagiaire(nom_complet="MOURALI Rania", statut_stage="Stage en cours")
        db.add(stagiaire)
        await db.flush()
        db.add(Attestation(
            stagiaire_id=stagiaire.id,
            numero_attestation="ATT-TEST-0001",
            generated_by=user.id,
        ))
        await db.commit()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        token = await _login(client, "doc_attestation@test.tn")
        response = await client.post(
            "/api/chat",
            json={"message": "Que dit le document concernant les attestations de stage ?"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        answer = response.json()["response"]
        # Ne doit pas être la réponse déterministe DATABASE (liste de noms).
        assert "ont une attestation générée" not in answer