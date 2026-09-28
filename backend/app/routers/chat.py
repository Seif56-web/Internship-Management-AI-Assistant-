import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessageOut,
    ChatConversationOut,
)
from app.services import chat_service, chat_intents
from app.utils.rate_limiter import check_rate_limit
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.conversation import ChatConversation, ChatMessage
from app.database import get_db

router = APIRouter(prefix="/api/chat", tags=["Chat"])

logger = logging.getLogger(__name__)


def _make_title(message: str) -> str:
    title = message.strip()
    return title if len(title) <= 60 else title[:60] + "…"


@router.post("", response_model=ChatResponse)
async def send_message(
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    message = data.message.strip()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le message ne peut pas être vide",
        )
    if len(message) > 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le message est trop long (2000 caractères maximum)",
        )

    if not check_rate_limit(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Trop de messages envoyés. Veuillez réessayer dans un instant.",
        )

    intent = chat_intents.detect_intent(message)
    is_new = data.conversation_id is None
    conversation = await chat_service.get_or_create_conversation(
        db,
        current_user,
        conversation_id=data.conversation_id,
        title=_make_title(message) if is_new else None,
    )
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation introuvable",
        )

    history = await chat_service._load_history(db, conversation.id)
    response = await chat_service.generate_response(db, current_user, message, history)

    await chat_service.add_message(db, conversation.id, "user", message)
    await chat_service.add_message(db, conversation.id, "assistant", response)
    conversation.updated_at = datetime.now(timezone.utc)

    logger.info(
        "Chat : user_id=%s role=%s conversation_id=%s intent=%s msg_len=%d",
        current_user.id,
        current_user.role.value if hasattr(current_user.role, "value") else current_user.role,
        conversation.id,
        intent,
        len(message),
    )

    return ChatResponse(response=response, conversation_id=conversation.id)


@router.get("/conversations", response_model=list[ChatConversationOut])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversations = await chat_service.get_user_conversations(db, current_user)

    if conversations:
        counts_result = await db.execute(
            select(ChatMessage.conversation_id, func.count(ChatMessage.id))
            .where(ChatMessage.conversation_id.in_([c.id for c in conversations]))
            .group_by(ChatMessage.conversation_id)
        )
        counts = dict(counts_result.all())
    else:
        counts = {}

    return [
        ChatConversationOut(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=counts.get(c.id, 0),
        )
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessageOut])
async def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    messages = await chat_service.get_conversation_messages(db, current_user, conversation_id)
    if messages is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation introuvable",
        )
    return [ChatMessageOut.model_validate(m) for m in messages]


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await chat_service.delete_conversation(db, current_user, conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation introuvable",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)