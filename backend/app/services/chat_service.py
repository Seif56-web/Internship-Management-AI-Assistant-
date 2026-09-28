import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.conversation import ChatConversation, ChatMessage
from app.services import chat_intents
from app.services.llm_provider import (
    get_llm_provider,
    SYSTEM_PROMPT,
    DummyProvider,
    LLMProviderError,
)

logger = logging.getLogger(__name__)

HISTORY_TOKENS_LIMIT = 10


async def get_or_create_conversation(
    db: AsyncSession,
    user: User,
    conversation_id: int | None = None,
    title: str | None = None,
) -> ChatConversation:
    """Renvoie la conversation de l'utilisateur (créée si besoin).

    Vérifie toujours l'appartenance : un utilisateur ne peut pas accéder
    à une conversation qui n'est pas la sienne (None si refusée).
    """
    if conversation_id is not None:
        result = await db.execute(
            select(ChatConversation).where(ChatConversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if not conversation or conversation.user_id != user.id:
            return None
        return conversation

    conversation = ChatConversation(user_id=user.id, title=title)
    db.add(conversation)
    await db.flush()
    await db.refresh(conversation)
    return conversation


async def get_user_conversations(db: AsyncSession, user: User) -> list[ChatConversation]:
    result = await db.execute(
        select(ChatConversation)
        .where(ChatConversation.user_id == user.id)
        .order_by(ChatConversation.updated_at.desc(), ChatConversation.id.desc())
    )
    return list(result.scalars().all())


async def get_conversation_messages(
    db: AsyncSession, user: User, conversation_id: int
) -> list[ChatMessage] | None:
    result = await db.execute(
        select(ChatConversation).where(ChatConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation or conversation.user_id != user.id:
        return None
    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at, ChatMessage.id)
    )
    return list(messages_result.scalars().all())


async def delete_conversation(db: AsyncSession, user: User, conversation_id: int) -> bool:
    result = await db.execute(
        select(ChatConversation).where(ChatConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation or conversation.user_id != user.id:
        return False
    await db.delete(conversation)
    await db.flush()
    return True


async def _load_history(db: AsyncSession, conversation_id: int) -> list[dict]:
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation_id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(HISTORY_TOKENS_LIMIT)
    )
    messages = list(reversed(result.scalars().all()))
    return [{"role": m.role, "content": m.content} for m in messages]


async def add_message(db: AsyncSession, conversation_id: int, role: str, content: str) -> ChatMessage:
    message = ChatMessage(conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    await db.flush()
    await db.refresh(message)
    return message


def _build_messages(
    question: str,
    history: list[dict],
    data_context: str | None = None,
    rag_context: str | None = None,
) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)

    context_parts = []
    if data_context:
        context_parts.append(f"=== CONTEXTE BASE DE DONNÉES (TEMPS RÉEL) ===\n{data_context}")
    if rag_context:
        context_parts.append(f"{rag_context}")

    if context_parts:
        question = f"{question}\n\n" + "\n\n".join(context_parts)

    messages.append({"role": "user", "content": question})
    return messages


def _general_fallback(message: str) -> str:
    """Réponses déterministes pour les intentions générales (LLM indisponible)."""
    normalized = chat_intents.normalize(message)

    if not normalized:
        return "Je n'ai pas compris votre demande. Pouvez-vous reformuler ?"

    if any(word in normalized for word in ("bonjour", "salut", "hello", "bonsoir", "coucou", "hi")):
        return "Bonjour ! Je suis l'assistant de gestion des stagiaires. Comment puis-je vous aider ?"

    if any(word in normalized for word in ("merci", "super", "parfait", "genial", "cool", "excellent")):
        return "Avec plaisir ! N'hésitez pas si vous avez d'autres questions."

    if any(word in normalized for word in ("au revoir", "bye", "bientot", "adieu")):
        return "Au revoir ! À bientôt sur la plateforme de gestion des stagiaires."

    if any(word in normalized for word in ("aide", "help", "quoi", "qui es")):
        return (
            "Je suis l'assistant de la plateforme de gestion des stagiaires Hutchinson. "
            "Vous pouvez me poser des questions sur les stagiaires, encadrants, évaluations, "
            "rapports, validations et attestations, par exemple :\n"
            "- « Combien de stagiaires sont actuellement en stage ? »\n"
            "- « Quels stagiaires n'ont pas encore soumis leur rapport ? »\n"
            "- « Quels rapports sont encore en attente de validation ? »\n"
            "- « Donne-moi les informations concernant le stagiaire X »\n"
            "- « Combien de stagiaires ont obtenu plus de 15 ? »\n"
            "- « Quelle est la note de Seif ? »"
        )

    return (
        "J'ai bien reçu votre message. Je peux répondre à des questions sur les stagiaires, "
        "encadrants, évaluations, rapports et attestations de la plateforme. "
        "Essayez par exemple : « Combien de stagiaires sont en stage ? »"
    )


async def generate_response(
    db: AsyncSession,
    user: User,
    message: str,
    history: list[dict] | None = None,
) -> str:
    """Génère la réponse de l'assistant avec routage hybride DATABASE/RAG/HYBRID.

    - DATABASE : question métier structurée -> requête SQL + LLM
    - RAG : question documentaire/procédurale -> recherche vectorielle + LLM
    - HYBRID : question mêlant les deux -> SQL + recherche vectorielle + LLM
    - GENERAL : salutations/aide -> LLM ou fallback déterministe
    - LLM indisponible : fallback déterministe (données réelles uniquement)
    """
    # Détection du type de requête
    query_type = chat_intents.detect_query_type(message)

    data_context = None
    data_fallback = None
    rag_context = None
    rag_fallback = None

    if query_type in (chat_intents.QueryType.DATABASE, chat_intents.QueryType.HYBRID):
        # Intention métier structurée
        intent = chat_intents.detect_intent(message)
        if intent:
            data_context, data_fallback = await chat_intents.handle_intent(db, user, message, intent)

    if query_type in (chat_intents.QueryType.RAG, chat_intents.QueryType.HYBRID):
        # Question documentaire
        rag_context, rag_fallback = await chat_intents.handle_rag_query(message)

    provider = get_llm_provider()
    if isinstance(provider, DummyProvider):
        # LLM non disponible : utiliser les fallbacks déterministes
        if data_fallback is not None:
            return data_fallback
        if rag_fallback is not None:
            return rag_fallback
        return _general_fallback(message)

    try:
        response = await provider.complete(
            _build_messages(message, history or [], data_context, rag_context)
        )
        if response:
            return response
        raise LLMProviderError("Réponse LLM vide")
    except LLMProviderError as e:
        logger.error("Chat : échec du LLM, repli sur réponse déterministe (%s)", e)
        # En cas d'erreur LLM, privilégier les données structurées (source de vérité)
        if data_fallback is not None:
            return data_fallback
        if rag_fallback is not None:
            return rag_fallback
        return _general_fallback(message)