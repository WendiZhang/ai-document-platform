import json

from fastapi.responses import StreamingResponse

from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSource,
)
from app.services.embedding_service import (
    EmbeddingError,
    generate_embedding,
)
from app.services.rag_service import (
    RAGError,
    generate_rag_answer,
    stream_rag_answer,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

@router.post(
    "",
    response_model=ChatResponse,
)
def chat_with_all_documents(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    try:
        question_embedding = generate_embedding(
            payload.question
        )

    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    distance = (
        DocumentChunk.embedding.cosine_distance(
            question_embedding
        )
    )

    statement = (
        select(
            DocumentChunk,
            Document,
            distance.label("distance"),
        )
        .join(
            Document,
            Document.id
            == DocumentChunk.document_id,
        )
        .where(
            Document.owner_id
            == current_user.id,
            DocumentChunk.embedding.is_not(None),
        )
    )
    
    if payload.document_id is not None:
        statement = statement.where(
            Document.id == payload.document_id
        )

    statement = (
        statement
        .order_by(distance)
        .limit(5)
    )

    rows = db.execute(statement).all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No embedded document content "
                "is available."
            ),
        )

    context_chunks = [
        chunk.content
        for chunk, _, _ in rows
    ]

    try:
        answer = generate_rag_answer(
            question=payload.question,
            context_chunks=context_chunks,
        )

    except RAGError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    sources = [
        ChatSource(
            document_id=chunk.document_id,
            document_name=document.original_filename,
            chunk_id=chunk.id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            score=max(
                0.0,
                1.0 - float(distance_value),
            ),
        )
        for chunk, document, distance_value in rows
    ]

    return ChatResponse(
        answer=answer,
        sources=sources,
    )
    
def get_user_chat_session(
    session_id: UUID,
    owner_id: UUID,
    db: Session,
) -> ChatSession:
    statement = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.owner_id == owner_id,
    )

    chat_session = db.scalar(statement)

    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    return chat_session

def get_recent_chat_messages(
    session_id: UUID,
    db: Session,
    limit: int = 8,
) -> list[ChatMessage]:
    """
    Return the latest chat messages in chronological order.
    """
    statement = (
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id
        )
        .order_by(
            ChatMessage.created_at.desc()
        )
        .limit(limit)
    )

    newest_first = list(
        db.scalars(statement).all()
    )

    return list(
        reversed(newest_first)
    )
    
def build_retrieval_query(
    question: str,
    recent_messages: list[ChatMessage],
) -> str:
    history_text = "\n".join(
        f"{message.role}: {message.content}"
        for message in recent_messages
    )

    if not history_text:
        return question

    return (
        "Recent conversation:\n"
        f"{history_text}\n\n"
        "Current question:\n"
        f"{question}"
    )
    
@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chat_session(
    payload: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSession:
    title = (
        payload.title.strip()
        if payload.title
        else "New conversation"
    )

    chat_session = ChatSession(
        owner_id=current_user.id,
        title=title,
    )

    try:
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The chat session could not be created.",
        ) from exc

    return chat_session

@router.get(
    "/sessions",
    response_model=list[ChatSessionResponse],
)
def list_chat_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatSession]:
    statement = (
        select(ChatSession)
        .where(
            ChatSession.owner_id == current_user.id
        )
        .order_by(
            ChatSession.updated_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )
    
@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageResponse],
)
def list_chat_messages(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatMessage]:
    chat_session = get_user_chat_session(
        session_id=session_id,
        owner_id=current_user.id,
        db=db,
    )

    statement = (
        select(ChatMessage)
        .where(
            ChatMessage.session_id == chat_session.id
        )
        .order_by(
            ChatMessage.created_at.asc()
        )
    )

    return list(
        db.scalars(statement).all()
    )
    
@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_chat_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    chat_session = get_user_chat_session(
        session_id=session_id,
        owner_id=current_user.id,
        db=db,
    )

    try:
        db.delete(chat_session)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The chat session could not be deleted.",
        ) from exc
        
        
@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatResponse,
)
def chat_with_documents(
    session_id: UUID,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    chat_session = get_user_chat_session(
        session_id=session_id,
        owner_id=current_user.id,
        db=db,
    )

    recent_messages = get_recent_chat_messages(
        session_id=chat_session.id,
        db=db,
        limit=8,
    )

    retrieval_query = build_retrieval_query(
        question=payload.question,
        recent_messages=recent_messages,
    )

    try:
        question_embedding = generate_embedding(
            retrieval_query
        )

    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    distance = (
        DocumentChunk.embedding.cosine_distance(
            question_embedding
        )
    )

    statement = (
        select(
            DocumentChunk,
            Document,
            distance.label("distance"),
        )
        .join(
            Document,
            Document.id == DocumentChunk.document_id,
        )
        .where(
            Document.owner_id == current_user.id,
            DocumentChunk.embedding.is_not(None),
        )
    )

    if payload.document_id is not None:
        statement = statement.where(
            Document.id == payload.document_id
        )

    statement = (
        statement
        .order_by(distance)
        .limit(5)
    )

    rows = db.execute(statement).all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No embedded document content is available."
            ),
        )

    sources = [
        ChatSource(
            document_id=document.id,
            document_name=document.original_filename,
            chunk_id=chunk.id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            score=max(
                0.0,
                1.0 - float(distance_value),
            ),
        )
        for chunk, document, distance_value in rows
    ]

    conversation_history = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in recent_messages
        if message.role in {
            "user",
            "assistant",
        }
    ]

    try:
        answer = generate_rag_answer(
            question=payload.question,
            context_chunks=[
                chunk.content
                for chunk, _, _ in rows
            ],
            conversation_history=conversation_history,
        )

    except RAGError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    user_message = ChatMessage(
        session_id=chat_session.id,
        role="user",
        content=payload.question,
        sources=None,
    )

    assistant_message = ChatMessage(
        session_id=chat_session.id,
        role="assistant",
        content=answer,
        sources=[
            source.model_dump(
                mode="json"
            )
            for source in sources
        ],
    )

    if chat_session.title == "New conversation":
        chat_session.title = (
            payload.question[:80].strip()
            or "New conversation"
        )

    try:
        db.add_all(
            [
                user_message,
                assistant_message,
            ]
        )

        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "The chat messages could not be saved."
            ),
        ) from exc

    return ChatResponse(
        session_id=chat_session.id,
        answer=answer,
        sources=sources,
    )


@router.post(
    "/sessions/{session_id}/stream",
)
def stream_chat_with_documents(
    session_id: UUID,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat_session = get_user_chat_session(
        session_id=session_id,
        owner_id=current_user.id,
        db=db,
    )

    recent_messages = get_recent_chat_messages(
        session_id=chat_session.id,
        db=db,
        limit=8,
    )

    retrieval_query = build_retrieval_query(
        question=payload.question,
        recent_messages=recent_messages,
    )

    try:
        question_embedding = generate_embedding(
            retrieval_query
        )

    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    distance = (
        DocumentChunk.embedding.cosine_distance(
            question_embedding
        )
    )

    statement = (
        select(
            DocumentChunk,
            Document,
            distance.label("distance"),
        )
        .join(
            Document,
            Document.id == DocumentChunk.document_id,
        )
        .where(
            Document.owner_id == current_user.id,
            DocumentChunk.embedding.is_not(None),
        )
    )

    if payload.document_id is not None:
        statement = statement.where(
            Document.id == payload.document_id
        )

    statement = (
        statement
        .order_by(distance)
        .limit(5)
    )

    rows = db.execute(statement).all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No embedded document content is available.",
        )

    sources = [
        ChatSource(
            document_id=document.id,
            document_name=document.original_filename,
            chunk_id=chunk.id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            score=max(
                0.0,
                1.0 - float(distance_value),
            ),
        )
        for chunk, document, distance_value in rows
    ]

    conversation_history = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in recent_messages
        if message.role in {
            "user",
            "assistant",
        }
    ]

    def event_stream():
        full_answer = ""

        try:
            for delta in stream_rag_answer(
                question=payload.question,
                context_chunks=[
                    chunk.content
                    for chunk, _, _ in rows
                ],
                conversation_history=conversation_history,
            ):
                full_answer += delta

                yield (
                    json.dumps({
                        "type": "delta",
                        "content": delta,
                    })
                    + "\n"
                )

            user_message = ChatMessage(
                session_id=chat_session.id,
                role="user",
                content=payload.question,
                sources=None,
            )

            assistant_message = ChatMessage(
                session_id=chat_session.id,
                role="assistant",
                content=full_answer,
                sources=[
                    source.model_dump(
                        mode="json"
                    )
                    for source in sources
                ],
            )

            if chat_session.title == "New conversation":
                chat_session.title = (
                    payload.question[:80].strip()
                    or "New conversation"
                )

            db.add_all([
                user_message,
                assistant_message,
            ])

            db.commit()

            yield (
                json.dumps({
                    "type": "sources",
                    "sources": [
                        source.model_dump(
                            mode="json"
                        )
                        for source in sources
                    ],
                })
                + "\n"
            )

            yield (
                json.dumps({
                    "type": "done",
                })
                + "\n"
            )

        except Exception as exc:
            db.rollback()

            print(
                "STREAM CHAT ERROR:",
                exc,
            )

            yield (
                json.dumps({
                    "type": "error",
                    "message": (
                        "The AI response could not be generated."
                    ),
                })
                + "\n"
            )

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
    )
