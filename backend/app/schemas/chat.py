from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionCreate(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=255,
    )


class ChatSessionResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ChatRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )

    document_id: UUID | None = None


class ChatSource(BaseModel):
    document_id: UUID
    document_name: str
    chunk_id: UUID
    chunk_index: int
    content: str
    score: float


class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    sources: list[ChatSource] | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ChatResponse(BaseModel):
    session_id: UUID
    answer: str
    sources: list[ChatSource]