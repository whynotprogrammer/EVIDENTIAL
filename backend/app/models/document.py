import enum
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from backend.app.db.session import Base


class DocumentProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(64), nullable=True)
    
    # Cryptographic Hash (SHA-256) of raw uploaded file
    sha256_hash = Column(String(64), nullable=False, index=True)
    
    # Ownership
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_by = relationship("User")

    # Processing Status
    processing_status = Column(
        Enum(DocumentProcessingStatus),
        default=DocumentProcessingStatus.PENDING,
        nullable=False,
        index=True,
    )
    error_message = Column(Text, nullable=True)

    # Multilingual & OCR attributes (reserved for subsequent phases)
    detected_language = Column(String(64), nullable=True, default="Unknown")
    language_confidence = Column(Float, nullable=True)
    original_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    ocr_engine = Column(String(64), nullable=True, default="Hybrid-OCR")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    case = relationship("Case", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    translations = relationship("DocumentTranslation", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("ExtractedEntity", back_populates="document", cascade="all, delete-orphan")


class DocumentVersion(Base):
    """Immutable version history for uploaded documents."""
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    sha256_hash = Column(String(64), nullable=False)
    
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_by = relationship("User")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="versions")


class DocumentTranslation(Base):
    """Separate table preserving original document text while storing translations."""
    __tablename__ = "document_translations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    
    source_language = Column(String(64), nullable=False)
    target_language = Column(String(64), nullable=False, default="English")
    translated_text = Column(Text, nullable=False)
    translator_model = Column(String(64), nullable=True, default="Neural-Translate-v2")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("Document", back_populates="translations")
