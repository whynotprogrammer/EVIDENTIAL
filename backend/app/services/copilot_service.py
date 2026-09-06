import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, load_only

from ai.rag.copilot_engine import InvestigationCopilotEngine
from backend.app.models.audit import AuditAction, AuditEvent, AuditStatus
from backend.app.models.case import Case
from backend.app.models.document import Document, DocumentTranslation
from backend.app.models.entity import EntityType, ExtractedEntity
from backend.app.models.evidence import Evidence
from backend.app.models.timeline_event import InvestigationEvent
from backend.app.models.user import User, UserRole
from backend.app.schemas.copilot import (
    CopilotCaseSummaryResponse,
    CopilotQueryRequest,
    CopilotQueryResponse,
    SourceCitation,
)
from backend.app.services.correlation_service import CorrelationService

logger = logging.getLogger("evidential.copilot")


class CopilotService:
    @staticmethod
    def _is_case_authorized(db: Session, current_user: User, case_id: int) -> bool:
        """Enforces strict pre-retrieval authorization on case data."""
        if current_user.role == UserRole.ADMIN:
            return db.query(Case).filter(Case.id == case_id).first() is not None

        case = (
            db.query(Case)
            .filter(
                Case.id == case_id,
                or_(
                    Case.assigned_officer_id == current_user.id,
                    Case.created_by_id == current_user.id,
                    Case.assigned_officer_id == None,
                ),
            )
            .first()
        )
        return case is not None

    @classmethod
    def _assemble_authorized_case_context(cls, db: Session, case_id: int, current_user: User) -> Dict[str, Any]:
        """Retrieves and packages all grounded case artifacts for the copilot engine."""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Case ID {case_id} not found.",
            )

        # Some existing local databases predate optional Document columns such
        # as ``original_filename``. Load only the columns required for grounded
        # Copilot context so an FIR with no attached documents remains usable.
        documents = (
            db.query(Document)
            .options(load_only(
                Document.id, Document.case_id, Document.filename,
                Document.file_size_bytes, Document.sha256_hash,
                Document.processing_status, Document.detected_language,
                Document.original_text,
            ))
            .filter(Document.case_id == case_id)
            .all()
        )
        document_names_by_id = {document.id: document.filename for document in documents}
        doc_data = []
        for d in documents:
            trans = db.query(DocumentTranslation).filter(DocumentTranslation.document_id == d.id).first()
            doc_data.append({
                "id": d.id,
                # ``filename`` is available in both legacy and current schema.
                "original_filename": d.filename,
                "file_size_bytes": d.file_size_bytes,
                "sha256_hash": d.sha256_hash,
                "processing_status": d.processing_status.value if hasattr(d.processing_status, "value") else str(d.processing_status),
                "detected_language": d.detected_language,
                "original_text": d.original_text,
                "translated_text": trans.translated_text if trans else None,
            })

        entities = db.query(ExtractedEntity).filter(ExtractedEntity.case_id == case_id).all()
        ent_data = []
        for e in entities:
            e_type = e.entity_type.value if hasattr(e.entity_type, "value") else str(e.entity_type)
            if "." in e_type:
                e_type = e_type.split(".")[-1]
            ent_data.append({
                "id": e.id,
                "entity_type": str(e_type).upper(),
                "entity_value": e.entity_value,
                "normalized_value": e.normalized_value,
                "confidence": e.confidence,
                "context_snippet": e.context_snippet,
                # Use the safely loaded document metadata rather than
                # lazy-loading the legacy Document relationship.
                "source_document": document_names_by_id.get(e.document_id),
            })

        evidence_items = db.query(Evidence).filter(Evidence.case_id == case_id).all()
        ev_data = [
            {
                "id": ev.id,
                "title": ev.title,
                "evidence_type": ev.evidence_type.value if hasattr(ev.evidence_type, "value") else str(ev.evidence_type),
                "description": ev.description,
                "sha256_hash": ev.sha256_hash,
                "file_path": ev.file_path,
            }
            for ev in evidence_items
        ]

        investigation_events = db.query(InvestigationEvent).filter(InvestigationEvent.case_id == case_id).all()
        tl_data = []
        if case.incident_date:
            tl_data.append({
                "id": f"case-{case.id}-fir",
                "event_date": case.incident_date.isoformat() if hasattr(case.incident_date, "isoformat") else str(case.incident_date),
                "event_type": "SOURCE_FIR_DATE",
                "title": "Source FIR date",
                "description": "FIR year, month, and day recorded in the source dataset.",
                "source": f"Source FIR Record {case.case_number}",
                "source_type": "CASE_RECORD",
                "source_document": None,
            })
        for ie in investigation_events:
            src_doc = ie.source_document.original_filename if ie.source_document else f"Officer Log #{ie.id}"
            tl_data.append({
                "id": f"ie-{ie.id}",
                "event_date": ie.event_date.isoformat() if hasattr(ie.event_date, "isoformat") else str(ie.event_date),
                "event_type": ie.event_type.value if hasattr(ie.event_type, "value") else str(ie.event_type),
                "title": ie.title,
                "description": ie.description,
                "source": src_doc,
                "source_type": "INVESTIGATION_LOG",
                "source_document": src_doc,
            })

        # Gather authorized correlations
        correlations_data = []
        correlations_available = True
        try:
            corr_resp = CorrelationService.get_correlations_for_case(
                db=db, current_user=current_user, case_id=case_id, min_threshold=0.3
            )
            for c in corr_resp.correlations:
                correlations_data.append({
                    "related_case": {
                        "id": c.related_case.id,
                        "case_number": c.related_case.case_number,
                        "title": c.related_case.title,
                        "crime_type": c.related_case.crime_type,
                        "district": c.related_case.district,
                        "fir_year": c.related_case.fir_year,
                        "crime_head": c.related_case.crime_head,
                    },
                    "correlation_score": c.correlation_score,
                    "matching_factors": c.matching_factors,
                    "explanation": c.explanation,
                })
        except Exception:
            logger.warning("Could not load correlations for case %s", case_id)
            correlations_available = False

        return {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "crime_type": case.crime_type,
            "description": case.description,
            "location": case.location,
            "police_station": case.police_station,
            "incident_date": case.incident_date.isoformat() if case.incident_date and hasattr(case.incident_date, "isoformat") else str(case.incident_date or ""),
            "source_fir": {
                "record_id": case.case_number,
                "district": case.district,
                "unit_name": case.police_station,
                "fir_year": case.fir_year,
                "fir_month": case.fir_month,
                "fir_day": case.fir_day,
                "fir_type": case.fir_type,
                "fir_stage": case.fir_stage,
                "crime_group": case.crime_type,
                "crime_head": case.crime_head,
                "complaint_mode": case.complaint_mode,
                "place_of_offence": case.location,
                "act_section": case.act_section,
                "victim_count": case.victim_count,
                "accused_count": case.accused_count,
                "arrested_count": case.arrested_count,
                "conviction_count": case.conviction_count,
            } if case.source_record_key else None,
            "documents": doc_data,
            "entities": ent_data,
            "evidence_items": ev_data,
            "timeline_events": tl_data,
            "correlations": correlations_data,
            "correlations_available": correlations_available,
        }

    @classmethod
    def query(
        cls,
        db: Session,
        current_user: User,
        payload: CopilotQueryRequest,
    ) -> CopilotQueryResponse:
        """
        Executes a grounded AI copilot question against authorized case records.
        Strictly prevents unauthorized retrieval and prompt injection.
        """
        # 1. Pre-retrieval authorization gate
        if not cls._is_case_authorized(db, current_user, payload.case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to query copilot intelligence for this case.",
            )

        # 2. Assemble verified case context
        case_context = cls._assemble_authorized_case_context(db, payload.case_id, current_user)

        # 3. Grounded Engine Processing
        result = InvestigationCopilotEngine.process_query(
            question=payload.question,
            case_data=case_context,
            related_cases=case_context.get("correlations", []),
        )

        citations = [
            SourceCitation(
                citation_id=c["citation_id"],
                source_type=c["source_type"],
                source_title=c["source_title"],
                document_filename=c.get("document_filename"),
                snippet=c.get("snippet"),
            )
            for c in result.get("citations", [])
        ]

        # 4. Audit Log
        audit_entry = AuditEvent(
            user_id=current_user.id,
            user_email=current_user.email,
            action=AuditAction.COPILOT_QUERY,
            status=AuditStatus.SUCCESS,
            details=json.dumps({
                "action": "COPILOT_QUERY",
                "case_id": payload.case_id,
                "question": payload.question[:100],
                "uncertainty_flag": result.get("uncertainty_flag", False),
                "citations_count": len(citations),
            }),
        )
        db.add(audit_entry)
        db.commit()

        return CopilotQueryResponse(
            case_id=payload.case_id,
            case_number=case_context.get("case_number", "UNKNOWN"),
            question=payload.question,
            answer=result.get("answer", ""),
            citations=citations,
            uncertainty_flag=result.get("uncertainty_flag", False),
            confidence_level=result.get("confidence_level", "HIGH"),
        )

    @classmethod
    def get_summary(
        cls,
        db: Session,
        current_user: User,
        case_id: int,
    ) -> CopilotCaseSummaryResponse:
        """Generates an instant grounded AI executive summary with key persons, evidence, and citations."""
        if not cls._is_case_authorized(db, current_user, case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to access case summary.",
            )

        case_context = cls._assemble_authorized_case_context(db, case_id, current_user)
        result = InvestigationCopilotEngine.process_query(
            question="Summarize this case",
            case_data=case_context,
            related_cases=case_context.get("correlations", []),
        )

        citations = [
            SourceCitation(
                citation_id=c["citation_id"],
                source_type=c["source_type"],
                source_title=c["source_title"],
                document_filename=c.get("document_filename"),
                snippet=c.get("snippet"),
            )
            for c in result.get("citations", [])
        ]

        person_names = list({
            e["entity_value"] for e in case_context.get("entities", []) if e.get("entity_type") in ("PERSON", "PERSON_NAME")
        })

        return CopilotCaseSummaryResponse(
            case_id=case_id,
            case_number=case_context.get("case_number", "UNKNOWN"),
            case_title=case_context.get("title", "Untitled Case"),
            summary_answer=result.get("answer", ""),
            citations=citations,
            persons_identified=person_names,
            evidence_count=len(case_context.get("evidence_items", [])),
            timeline_events_count=len(case_context.get("timeline_events", [])),
        )
