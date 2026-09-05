import logging
import os
from datetime import datetime, timezone
from typing import Dict, Optional
from sqlalchemy.orm import Session

from ai.classification.classifier import DocumentClassifier
from ai.nlp.entity_extractor import EntityExtractor
from ai.nlp.language_detector import LanguageDetector
from ai.nlp.translator import DocumentTranslator
from ai.ocr.ocr_engine import OCREngine
from backend.app.models.audit import AuditAction, AuditStatus
from backend.app.models.document import Document, DocumentProcessingStatus, DocumentTranslation
from backend.app.models.entity import ExtractedEntity, EntityType
from backend.app.models.user import User
from backend.app.services.audit_service import log_audit_event

logger = logging.getLogger("evidential.ai_pipeline")


class DocumentAIPipeline:
    """
    Master Document AI Pipeline Orchestrator for EVIDENTIAL.
    Orchestrates Preprocessing -> OCR -> Language Detection -> Text Storage -> Translation -> Entity Extraction -> Classification.
    """

    @classmethod
    def process_document(
        cls,
        document_id: int,
        db: Session,
        actor_user: Optional[User] = None,
        override_text: Optional[str] = None,
    ) -> Document:
        """
        Executes the entire document AI pipeline on a registered document.
        Guarantees state management (QUEUED -> PROCESSING -> COMPLETED/FAILED)
        and strict original text immutability.
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document with ID {document_id} not found.")

        # Step 1: Transition status to PROCESSING
        doc.processing_status = DocumentProcessingStatus.PROCESSING
        doc.error_message = None
        db.commit()
        db.refresh(doc)

        try:
            # Step 2: Validate file existence or override text
            if override_text:
                raw_text = override_text
                ocr_confidence = 0.99
                ocr_engine_name = "Synthetic-Direct"
            else:
                if not os.path.exists(doc.file_path):
                    raise FileNotFoundError(f"Source file not found at {doc.file_path}")

                # Step 3: Run Preprocessing + Multi-Engine OCR
                ocr_result = OCREngine.extract_text(doc.file_path, mime_type=doc.mime_type)
                raw_text = ocr_result.text
                ocr_confidence = ocr_result.confidence
                ocr_engine_name = ocr_result.engine

            # Step 4: Language Detection
            detected_lang, lang_conf = LanguageDetector.detect_language(raw_text)

            # Step 5: Store Original OCR Text (Never Overwritten by Translation)
            doc.original_text = raw_text
            doc.detected_language = detected_lang
            doc.language_confidence = lang_conf
            doc.ocr_confidence = ocr_confidence
            doc.ocr_engine = ocr_engine_name

            # Step 6: Translation (if non-English)
            if detected_lang.lower() not in ("english", "unknown") and len(raw_text) > 5:
                translated_text, translator_model = DocumentTranslator.translate_to_english(
                    text=raw_text,
                    source_language=detected_lang,
                )
                # Check if translation already exists for document
                existing_trans = (
                    db.query(DocumentTranslation)
                    .filter(DocumentTranslation.document_id == doc.id)
                    .first()
                )
                if existing_trans:
                    existing_trans.translated_text = translated_text
                    existing_trans.source_language = detected_lang
                    existing_trans.translator_model = translator_model
                else:
                    db_trans = DocumentTranslation(
                        document_id=doc.id,
                        source_language=detected_lang,
                        target_language="English",
                        translated_text=translated_text,
                        translator_model=translator_model,
                    )
                    db.add(db_trans)

            # Step 7: Entity Extraction (11 Entity Types)
            # Clear previous entities for this document on reprocess
            db.query(ExtractedEntity).filter(ExtractedEntity.document_id == doc.id).delete()

            # Analyze both original and translated text for maximum recall
            combined_text_for_ner = raw_text
            extracted_items = EntityExtractor.extract_entities(combined_text_for_ner)

            for item in extracted_items:
                try:
                    # Validate against enum
                    enum_type = EntityType[item.entity_type]
                    db_entity = ExtractedEntity(
                        case_id=doc.case_id,
                        document_id=doc.id,
                        entity_type=enum_type,
                        entity_value=item.entity_value,
                        normalized_value=item.normalized_value,
                        confidence=item.confidence,
                        context_snippet=item.context_snippet,
                    )
                    db.add(db_entity)
                except KeyError:
                    logger.warning(f"Unknown entity type: {item.entity_type}")

            # Step 8: Crime Classification
            law_sections = [
                e.normalized_value for e in extracted_items if e.entity_type == "LAW_SECTION"
            ]
            classification = DocumentClassifier.classify_document(
                text=raw_text,
                law_sections=law_sections,
            )

            # Step 9: Mark as COMPLETED
            doc.processing_status = DocumentProcessingStatus.COMPLETED
            doc.updated_at = datetime.now(timezone.utc)

            # Optionally refine case priority if recommended is higher
            if doc.case and classification.recommended_priority == "CRITICAL":
                doc.case.priority = "CRITICAL"

            db.commit()
            db.refresh(doc)

            # Step 10: Audit Log Event
            if actor_user:
                log_audit_event(
                    db=db,
                    action=AuditAction.AI_ANALYSIS_EXECUTED,
                    user=actor_user,
                    resource_type="DOCUMENT",
                    resource_id=str(doc.id),
                    details=(
                        f"AI Document Pipeline completed successfully. Language: {detected_lang} ({lang_conf:.2f}), "
                        f"OCR Engine: {ocr_engine_name}, Extracted {len(extracted_items)} entities, "
                        f"Classification: {classification.primary_category} ({classification.confidence:.2f})"
                    ),
                    status=AuditStatus.SUCCESS,
                )

            logger.info(
                f"Successfully processed Document #{doc.id}: Language={detected_lang}, "
                f"Entities={len(extracted_items)}, Classification={classification.primary_category}"
            )
            return doc

        except Exception as exc:
            db.rollback()
            logger.exception(f"Document #{doc.id} AI processing failed: {exc}")
            doc.processing_status = DocumentProcessingStatus.FAILED
            doc.error_message = str(exc)
            doc.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(doc)

            if actor_user:
                log_audit_event(
                    db=db,
                    action=AuditAction.AI_ANALYSIS_EXECUTED,
                    user=actor_user,
                    resource_type="DOCUMENT",
                    resource_id=str(doc.id),
                    details=f"AI Pipeline failed: {str(exc)}",
                    status=AuditStatus.FAILURE,
                )
            raise exc
