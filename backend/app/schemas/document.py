from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: UUID
    owner_id: UUID
    original_filename: str
    content_type: str
    file_size: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDeleteResponse(BaseModel):
    message: str
    document_id: UUID


class DocumentProcessResponse(BaseModel):
    message: str
    document_id: UUID
    status: str
    character_count: int
    

class DocumentChunkResponse(BaseModel):
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    character_count: int
    start_character: int
    end_character: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class DocumentChunkingResponse(BaseModel):
    message: str
    document_id: UUID
    status: str
    chunk_count: int
    
class DocumentEmbeddingResponse(BaseModel):
    message: str
    document_id: UUID
    status: str
    embedded_chunk_count: int
    
class DocumentPrepareResponse(BaseModel):
    message: str
    document_id: UUID
    status: str
    character_count: int
    chunk_count: int
    embedded_chunk_count: int
    
class DocumentPreparationStartedResponse(BaseModel):
    message: str
    document_id: UUID
    status: str
