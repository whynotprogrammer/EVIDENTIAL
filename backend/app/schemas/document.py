from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.document import DocumentProcessingStatus
from backend.app.schemas.entity import EntityOut


class DocumentVersionOut(BaseModel):
    id: int
    document_id: int
    version_number: int
    file_path: str
    file_size_bytes: Optional[int] = None
    sha256_hash: str
    uploaded_by_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentTranslationOut(BaseModel):
    id: int
    document_id: int
    source_language: str
    target_language: str
    translated_text: str
    translator_model: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentOut(BaseModel):
    id: int
    case_id: int
    filename: str
    original_filename: str
    file_path: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    sha256_hash: str
    uploaded_by_id: Optional[int] = None
    processing_status: DocumentProcessingStatus
    error_message: Optional[str] = None
    
    detected_language: Optional[str] = "Unknown"
    language_confidence: Optional[float] = None
    original_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    ocr_engine: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    versions: List[DocumentVersionOut] = []
    translations: List[DocumentTranslationOut] = []
    entities: List[EntityOut] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentProcessResponse(BaseModel):
    document: DocumentOut
    message: str
