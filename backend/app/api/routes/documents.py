from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.user import User
from app.schemas.document import (
    DocumentChunkingResponse,
    DocumentChunkResponse,
    DocumentDeleteResponse,
    DocumentProcessResponse,
    DocumentResponse,
    DocumentEmbeddingResponse,
    DocumentPrepareResponse,
    DocumentPreparationStartedResponse,
)
from app.services.file_storage import (
    delete_saved_file,
    save_upload_file,
)
from app.services.text_extractor import (
    DocumentExtractionError,
    extract_document_text,
)
from app.services.text_chunker import (
    TextChunkingError,
    split_text_into_chunks,
)
from app.services.embedding_service import (
    EmbeddingError,
    generate_embedding,
)
from app.services.document_preparation import (
    prepare_document_in_background,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


def get_user_document(
    document_id: UUID,
    owner_id: UUID,
    db: Session,
) -> Document:
    """
    Retrieve a document only when it belongs to the current user.

    Returning 404 for both nonexistent documents and documents owned
    by another user avoids revealing whether another user's document
    exists.
    """
    statement = select(Document).where(
        Document.id == document_id,
        Document.owner_id == owner_id,
    )

    document = db.scalar(statement)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    saved_file = await save_upload_file(file)

    document = Document(
        owner_id=current_user.id,
        original_filename=saved_file.original_filename,
        stored_filename=saved_file.stored_filename,
        content_type=saved_file.mime_type,
        file_size=saved_file.file_size,
        storage_path=str(saved_file.file_path),
        status="uploaded",
    )

    try:
        db.add(document)
        db.flush()
        db.refresh(document)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()
        delete_saved_file(saved_file.file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document could not be saved.",
        ) from exc

    return document


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    """
    Return documents belonging only to the authenticated user.

    Results are ordered from newest to oldest.
    """
    statement = (
        select(Document)
        .where(
            Document.owner_id == current_user.id
        )
        .order_by(
            Document.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
    )

    documents = db.scalars(statement).all()

    return list(documents)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    """
    Return one document only when it belongs to the authenticated user.
    """
    return get_user_document(
        document_id=document_id,
        owner_id=current_user.id,
        db=db,
    )


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDeleteResponse:
    """
    Delete the authenticated user's document record and stored file.
    """
    document = get_user_document(
        document_id=document_id,
        owner_id=current_user.id,
        db=db,
    )

    file_path = document.storage_path

    try:
        db.delete(document)
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document could not be deleted.",
        ) from exc

    try:
        file_deleted = delete_saved_file(file_path)

    except OSError as exc:
        print(
            "DOCUMENT FILE DELETE ERROR:",
            exc,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "The database record was deleted, but the stored "
                "file could not be removed."
            ),
        ) from exc

    if not file_deleted:
        print(
            "UNSAFE DOCUMENT PATH REJECTED:",
            file_path,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "The database record was deleted, but the stored "
                "file path was invalid."
            ),
        )

    return DocumentDeleteResponse(
        message="Document deleted successfully.",
        document_id=document_id,
    )
    
@router.post(
    "/{document_id}/process",
    response_model=DocumentProcessResponse,
)
def process_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentProcessResponse:
    document = get_user_document(
        document_id=document_id,
        owner_id=current_user.id,
        db=db,
    )

    document.status = "processing"
    document.processing_error = None

    try:
        db.commit()
        db.refresh(document)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "The document processing status "
                "could not be updated."
            ),
        ) from exc

    try:
        extracted_text = extract_document_text(
            storage_path=document.storage_path,
            content_type=document.content_type,
            original_filename=document.original_filename,
        )

    except DocumentExtractionError as exc:
        document.status = "failed"
        document.processing_error = str(exc)

        try:
            db.commit()

        except SQLAlchemyError:
            db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    document.extracted_text = extracted_text
    document.status = "processed"
    document.processing_error = None

    try:
        db.commit()
        db.refresh(document)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The extracted text could not be saved.",
        ) from exc

    return DocumentProcessResponse(
        message="Document processed successfully.",
        document_id=document.id,
        status=document.status,
        character_count=len(extracted_text),
    )


@router.post(
    "/{document_id}/chunks",
    response_model=DocumentChunkingResponse,
)
def create_document_chunks(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentChunkingResponse:
    document = get_user_document(
        document_id=document_id,
        owner_id=current_user.id,
        db=db,
    )

    if document.status != "processed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The document must be processed before "
                "chunks can be created."
            ),
        )

    if not document.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The document does not contain extracted text.",
        )

    try:
        text_chunks = split_text_into_chunks(
            text=document.extracted_text,
            chunk_size=1200,
            chunk_overlap=200,
        )

    except TextChunkingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    try:
        # Recreating chunks replaces any older version.
        db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document.id
            )
        )

        chunk_records = [
            DocumentChunk(
                document_id=document.id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                character_count=chunk.character_count,
                start_character=chunk.start_character,
                end_character=chunk.end_character,
            )
            for chunk in text_chunks
        ]

        db.add_all(chunk_records)

        document.status = "chunked"
        document.processing_error = None

        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The document chunks could not be saved.",
        ) from exc

    return DocumentChunkingResponse(
        message="Document chunks created successfully.",
        document_id=document.id,
        status=document.status,
        chunk_count=len(chunk_records),
    )
    
@router.get(
    "/{document_id}/chunks",
    response_model=list[DocumentChunkResponse],
)
def list_document_chunks(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DocumentChunk]:
    document = get_user_document(
        document_id=document_id,
        owner_id=current_user.id,
        db=db,
    )

    statement = (
        select(DocumentChunk)
        .where(
            DocumentChunk.document_id == document.id
        )
        .order_by(
            DocumentChunk.chunk_index.asc()
        )
    )

    chunks = db.scalars(statement).all()

    return list(chunks)

@router.post(
    "/{document_id}/embed",
    response_model=DocumentEmbeddingResponse,
)
def embed_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentEmbeddingResponse:
    document = get_user_document(
        document_id=document_id,
        owner_id=current_user.id,
        db=db,
    )

    if document.status != "chunked":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Document chunks must be created "
                "before embeddings can be generated."
            ),
        )

    statement = (
        select(DocumentChunk)
        .where(
            DocumentChunk.document_id
            == document.id
        )
        .order_by(
            DocumentChunk.chunk_index.asc()
        )
    )

    chunks = list(
        db.scalars(statement).all()
    )

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The document does not contain chunks.",
        )

    try:
        for chunk in chunks:
            chunk.embedding = generate_embedding(
                chunk.content
            )

        document.status = "embedded"

        db.commit()

    except EmbeddingError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The embeddings could not be saved.",
        ) from exc

    return DocumentEmbeddingResponse(
        message="Document embeddings created successfully.",
        document_id=document.id,
        status=document.status,
        embedded_chunk_count=len(chunks),
    )
    
@router.post(
    "/{document_id}/prepare",
    response_model=DocumentPreparationStartedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def prepare_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentPreparationStartedResponse:
    document = get_user_document(
        document_id=document_id,
        owner_id=current_user.id,
        db=db,
    )

    active_statuses = {
        "queued",
        "processing",
        "chunking",
        "embedding",
    }

    if document.status in active_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This document is already being prepared.",
        )

    document.status = "queued"
    document.processing_error = None

    try:
        db.commit()
        db.refresh(document)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "The document preparation task "
                "could not be started."
            ),
        ) from exc

    background_tasks.add_task(
        prepare_document_in_background,
        document.id,
        current_user.id,
    )

    return DocumentPreparationStartedResponse(
        message="Document preparation started.",
        document_id=document.id,
        status=document.status,
    )