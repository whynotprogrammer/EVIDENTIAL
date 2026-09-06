"""
EVIDENTIAL Document AI Pipeline
================================
Master orchestrator: Upload → Preprocessing → OCR → Language Detection →
Text Storage → Translation → Entity Extraction → Crime Classification.

Mixed-language support:
  The pipeline records the DOMINANT detected language but also logs all scripts
  present in the document via the OCR engine's `detected_scripts` attribute.
  The original OCR text is stored ONCE and is NEVER overwritten by translation.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional
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
    Orchestrates the full document AI pipeline:
    Preprocessing → OCR → Language Detection → Text Storage →
    Translation → Entity Extraction → Crime Classification
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
        Execute the entire document AI pipeline.

        Parameters
        ----------
        document_id  : PK of the Document row to process
        db           : SQLAlchemy session
        actor_user   : user who triggered the pipeline (for audit logging)
        override_text: inject raw text directly (used in tests / data import)

        Returns
        -------
        The updated Document object (status = COMPLETED or FAILED).

        Raises
        ------
        ValueError  : document not found in DB
        Re-raises any unexpected exception after marking the doc as FAILED.
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found.")

        # ── Step 1: Mark as PROCESSING ───────────────────────────────────────
        doc.processing_status = DocumentProcessingStatus.PROCESSING
        doc.error_message = None
        db.commit()
        db.refresh(doc)

        try:
            # ── Step 2: OCR / text extraction ────────────────────────────────
            if override_text:
                raw_text = override_text
                ocr_confidence = 0.99
                ocr_engine_name = "Synthetic-Direct"
                detected_scripts: list = []
            else:
                if not os.path.exists(doc.file_path):
                    raise FileNotFoundError(
                        f"Source file not found at {doc.file_path!r}. "
                        "The uploaded document cannot be found on disk."
                    )

                ocr_result = OCREngine.extract_text(
                    doc.file_path, mime_type=doc.mime_type
                )

                if not ocr_result.text or ocr_result.engine == "Raster-Fallback":
                    # Non-fatal: store the fallback message so the investigator
                    # can see what happened, but do NOT raise — keep COMPLETED
                    # so the doc isn't stuck in PROCESSING.
                    logger.warning(
                        "Document #%d: OCR produced no readable text (engine=%s).",
                        document_id, ocr_result.engine,
                    )

                raw_text = ocr_result.text
                ocr_confidence = ocr_result.confidence
                ocr_engine_name = ocr_result.engine
                detected_scripts = getattr(ocr_result, "detected_scripts", [])

            # ── Step 3: Language Detection ───────────────────────────────────
            detected_lang, lang_conf = LanguageDetector.detect_language(raw_text)

            # For mixed-language docs, enrich the engine label
            if len(detected_scripts) > 1:
                scripts_label = "+".join(detected_scripts)
                logger.info(
                    "Document #%d: mixed-script document detected — %s",
                    document_id, scripts_label,
                )

            # ── Step 4: Persist original OCR text (NEVER overwritten) ────────
            doc.original_text = raw_text
            doc.detected_language = detected_lang
            doc.language_confidence = lang_conf
            doc.ocr_confidence = ocr_confidence
            doc.ocr_engine = ocr_engine_name
            db.commit()

            # ── Step 5: Translation (non-English only) ───────────────────────
            if detected_lang.lower() not in ("english", "unknown") and len(raw_text) > 5:
                try:
                    translated_text, translator_model = DocumentTranslator.translate_to_english(
                        text=raw_text,
                        source_language=detected_lang,
                    )
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
                        db.add(DocumentTranslation(
                            document_id=doc.id,
                            source_language=detected_lang,
                            target_language="English",
                            translated_text=translated_text,
                            translator_model=translator_model,
                        ))
                except Exception as trans_exc:
                    # Translation failure is non-fatal — log and continue
                    logger.warning(
                        "Document #%d: translation failed (%s). "
                        "Original text is preserved.",
                        document_id, trans_exc,
                    )

            # ── Step 6: Entity Extraction ────────────────────────────────────
            # Delete any existing entities for this document (re-process case)
            db.query(ExtractedEntity).filter(
                ExtractedEntity.document_id == doc.id
            ).delete()

            extracted_items = EntityExtractor.extract_entities(raw_text)
            for item in extracted_items:
                try:
                    enum_type = EntityType[item.entity_type]
                    db.add(ExtractedEntity(
                        case_id=doc.case_id,
                        document_id=doc.id,
                        entity_type=enum_type,
                        entity_value=item.entity_value,
                        normalized_value=item.normalized_value,
                        confidence=item.confidence,
                        context_snippet=item.context_snippet,
                    ))
                except KeyError:
                    logger.warning(
                        "Document #%d: unknown entity type %r — skipped.",
                        document_id, item.entity_type,
                    )

            # ── Step 7: Crime Classification ─────────────────────────────────
            law_sections = [
                e.normalized_value
                for e in extracted_items
                if e.entity_type == "LAW_SECTION"
            ]
            classification = DocumentClassifier.classify_document(
                text=raw_text, law_sections=law_sections
            )

            # Escalate case priority if classifier recommends CRITICAL
            if doc.case and classification.recommended_priority == "CRITICAL":
                doc.case.priority = "CRITICAL"

            # ── Step 8: Mark COMPLETED ───────────────────────────────────────
            doc.processing_status = DocumentProcessingStatus.COMPLETED
            doc.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(doc)

            # ── Step 9: Audit ────────────────────────────────────────────────
            if actor_user:
                log_audit_event(
                    db=db,
                    action=AuditAction.AI_ANALYSIS_EXECUTED,
                    user=actor_user,
                    resource_type="DOCUMENT",
                    resource_id=str(doc.id),
                    details=(
                        f"AI pipeline completed. "
                        f"Language: {detected_lang} ({lang_conf:.2f}), "
                        f"OCR engine: {ocr_engine_name}, "
                        f"Scripts: {detected_scripts or ['Latin']}, "
                        f"Entities: {len(extracted_items)}, "
                        f"Classification: {classification.primary_category} "
                        f"({classification.confidence:.2f})"
                    ),
                    status=AuditStatus.SUCCESS,
                )

            logger.info(
                "Document #%d processed: lang=%s conf=%.2f engine=%s "
                "entities=%d class=%s",
                doc.id, detected_lang, lang_conf, ocr_engine_name,
                len(extracted_items), classification.primary_category,
            )
            return doc

        except Exception as exc:
            db.rollback()
            logger.exception("Document #%d AI processing failed: %s", document_id, exc)

            # Persist FAILED status with a human-readable message
            try:
                doc = db.query(Document).filter(Document.id == document_id).first()
                if doc:
                    doc.processing_status = DocumentProcessingStatus.FAILED
                    doc.error_message = (
                        f"{type(exc).__name__}: {str(exc)}"[:512]
                    )
                    doc.updated_at = datetime.now(timezone.utc)
                    db.commit()
                    db.refresh(doc)
            except Exception as db_exc:
                logger.error(
                    "Could not persist FAILED status for document #%d: %s",
                    document_id, db_exc,
                )

            if actor_user:
                try:
                    log_audit_event(
                        db=db,
                        action=AuditAction.AI_ANALYSIS_EXECUTED,
                        user=actor_user,
                        resource_type="DOCUMENT",
                        resource_id=str(document_id),
                        details=f"AI pipeline failed: {type(exc).__name__}: {str(exc)}"[:512],
                        status=AuditStatus.FAILURE,
                    )
                except Exception:
                    pass

            raise exc
