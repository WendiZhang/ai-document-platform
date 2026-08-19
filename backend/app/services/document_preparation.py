from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding_service import (
    EmbeddingError,
    generate_embedding,
)
from app.services.text_chunker import (
    TextChunkingError,
    split_text_into_chunks,
)
from app.services.text_extractor import (
    DocumentExtractionError,
    extract_document_text,
)


def update_document_failure(
    db: Session,
    document: Document,
    message: str,
) -> None:
    document.status = "failed"
    document.processing_error = message

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()


def prepare_document_in_background(
    document_id: UUID,
    owner_id: UUID,
) -> None:
    """
    Extract, chunk, and embed a document outside the HTTP request.

    A new database session is created because the request-scoped
    session is no longer available after the response is returned.
    """
    db = SessionLocal()

    try:
        statement = select(Document).where(
            Document.id == document_id,
            Document.owner_id == owner_id,
        )

        document = db.scalar(statement)

        if document is None:
            return

        # Step 1: extract text
        document.status = "processing"
        document.processing_error = None
        db.commit()

        try:
            extracted_text = extract_document_text(
                storage_path=document.storage_path,
                content_type=document.content_type,
                original_filename=document.original_filename,
            )

        except DocumentExtractionError as exc:
            update_document_failure(
                db=db,
                document=document,
                message=str(exc),
            )
            return

        document.extracted_text = extracted_text
        document.status = "chunking"
        db.commit()

        # Step 2: create chunks
        try:
            text_chunks = split_text_into_chunks(
                text=extracted_text,
                chunk_size=1200,
                chunk_overlap=200,
            )

        except TextChunkingError as exc:
            update_document_failure(
                db=db,
                document=document,
                message=str(exc),
            )
            return

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

        document.status = "embedding"
        db.flush()
        db.commit()

        # Step 3: generate embeddings
        try:
            for chunk_record in chunk_records:
                chunk_record.embedding = generate_embedding(
                    chunk_record.content
                )

        except EmbeddingError as exc:
            db.rollback()

            document = db.scalar(statement)

            if document is not None:
                update_document_failure(
                    db=db,
                    document=document,
                    message=str(exc),
                )

            return

        document.status = "ready"
        document.processing_error = None
        db.commit()

    except SQLAlchemyError as exc:
        db.rollback()

        try:
            document = db.scalar(
                select(Document).where(
                    Document.id == document_id,
                    Document.owner_id == owner_id,
                )
            )

            if document is not None:
                update_document_failure(
                    db=db,
                    document=document,
                    message=(
                        "A database error occurred while "
                        "preparing the document."
                    ),
                )

        except SQLAlchemyError:
            db.rollback()

        print(
            "BACKGROUND DOCUMENT PREPARATION ERROR:",
            exc,
        )

    except Exception as exc:
        db.rollback()

        try:
            document = db.scalar(
                select(Document).where(
                    Document.id == document_id,
                    Document.owner_id == owner_id,
                )
            )

            if document is not None:
                update_document_failure(
                    db=db,
                    document=document,
                    message=(
                        "An unexpected error occurred while "
                        "preparing the document."
                    ),
                )

        except SQLAlchemyError:
            db.rollback()

        print(
            "UNEXPECTED DOCUMENT PREPARATION ERROR:",
            exc,
        )

    finally:
        db.close()