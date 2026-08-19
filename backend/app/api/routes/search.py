from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.schemas.search import (
    SemanticSearchRequest,
    SemanticSearchResponse,
    SemanticSearchResult,
)
from app.services.embedding_service import (
    EmbeddingError,
    generate_embedding,
)


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.post(
    "/semantic",
    response_model=SemanticSearchResponse,
)
def semantic_search(
    payload: SemanticSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SemanticSearchResponse:
    try:
        query_embedding = generate_embedding(
            payload.query
        )

    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    distance = (
        DocumentChunk.embedding.cosine_distance(
            query_embedding
        )
    )

    statement = (
        select(
            DocumentChunk,
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
        .order_by(distance)
        .limit(payload.limit)
    )

    rows = db.execute(statement).all()

    results = [
        SemanticSearchResult(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            chunk_index=chunk.chunk_index,
            content=chunk.content,
            score=max(
                0.0,
                1.0 - float(distance_value),
            ),
        )
        for chunk, distance_value in rows
    ]

    return SemanticSearchResponse(
        query=payload.query,
        results=results,
    )