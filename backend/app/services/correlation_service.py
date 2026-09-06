import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, load_only

from ai.correlation.correlation_engine import CorrelationEngine
from backend.app.models.audit import AuditAction, AuditEvent, AuditStatus
from backend.app.models.case import Case
from backend.app.models.correlation import CaseCorrelation
from backend.app.models.document import Document, DocumentTranslation
from backend.app.models.entity import ExtractedEntity
from backend.app.models.user import User, UserRole
from backend.app.schemas.correlation import (
    CaseSummary,
    CorrelationListResponse,
    CorrelationResult,
    MatchedEntityItem,
)

logger = logging.getLogger("evidential.correlation")


class CorrelationService:
    @staticmethod
    def _get_authorized_case_ids(db: Session, current_user: User) -> set[int]:
        """Pre-retrieval authorization boundary check."""
        if current_user.role == UserRole.ADMIN:
            q = db.query(Case.id)
        else:
            q = db.query(Case.id).filter(
                or_(
                    Case.assigned_officer_id == current_user.id,
                    Case.created_by_id == current_user.id,
                    Case.assigned_officer_id == None,
                )
            )
        return {r[0] for r in q.all()}

    @classmethod
    def _package_case_data(cls, db: Session, case_id: int) -> Optional[Dict[str, Any]]:
        """Packages case record, entities, and document translations for correlation analysis."""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return None

        entities = (
            db.query(ExtractedEntity)
            .filter(ExtractedEntity.case_id == case_id)
            .all()
        )
        entity_dicts = [
            {
                "entity_type": e.entity_type.value if hasattr(e.entity_type, "value") else str(e.entity_type),
                "entity_value": e.entity_value,
                "normalized_value": e.normalized_value or e.entity_value,
            }
            for e in entities
        ]

        documents = (
            db.query(Document)
            .options(load_only(Document.id, Document.case_id, Document.original_text))
            .filter(Document.case_id == case_id)
            .all()
        )
        doc_dicts = []
        for d in documents:
            # Check for translation
            trans = (
                db.query(DocumentTranslation)
                .filter(DocumentTranslation.document_id == d.id)
                .first()
            )
            doc_dicts.append({
                "original_text": d.original_text or "",
                "translated_text": trans.translated_text if trans else "",
            })

        return {
            "id": case.id,
            "case_number": case.case_number,
            "title": case.title,
            "description": case.description or "",
            "crime_type": case.crime_type,
            "location": case.location or "",
            "police_station": case.police_station or "",
            "incident_date": case.incident_date,
            "entities": entity_dicts,
            "documents": doc_dicts,
            "status": case.status.value if hasattr(case.status, "value") else str(case.status),
            "source_record_key": case.source_record_key,
            "district": case.district,
            "fir_year": case.fir_year,
            "fir_month": case.fir_month,
            "crime_head": case.crime_head,
            "fir_stage": case.fir_stage,
            "fir_type": case.fir_type,
            "act_section": case.act_section,
            "latitude": case.latitude,
            "longitude": case.longitude,
        }

    @classmethod
    def get_correlations_for_case(
        cls,
        db: Session,
        current_user: User,
        case_id: int,
        min_threshold: float = 0.25,
        target_case_id: Optional[int] = None,
    ) -> CorrelationListResponse:
        """
        Computes explainable cross-FIR correlations for a target case.
        Strictly enforces pre-retrieval authorization.
        """
        authorized_case_ids = cls._get_authorized_case_ids(db, current_user)

        # 1. Authorization check for source case
        if case_id not in authorized_case_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not authorized to view or correlate this case.",
            )

        source_case_data = cls._package_case_data(db, case_id)
        if not source_case_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Source case ID {case_id} not found.",
            )

        # A single broad matching field is not enough to call two source FIRs
        # potentially related. Imported FIRs therefore use a conservative floor.
        effective_threshold = max(min_threshold, 0.35) if source_case_data.get("source_record_key") else min_threshold

        # 2. Determine candidate related cases (strictly within authorized set)
        if target_case_id:
            if target_case_id not in authorized_case_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Target comparison case is not in your authorized jurisdiction.",
                )
            candidate_ids = [target_case_id]
        else:
            candidate_ids = [cid for cid in authorized_case_ids if cid != case_id]

        correlations: List[CorrelationResult] = []

        # 3. Pairwise comparison across authorized cases
        for cand_id in candidate_ids:
            cand_data = cls._package_case_data(db, cand_id)
            if not cand_data:
                continue

            analysis = CorrelationEngine.compare_cases(
                source_case_data=source_case_data,
                related_case_data=cand_data,
                min_threshold=min_threshold,
            )

            if analysis["correlation_score"] >= effective_threshold:
                matched_entities = [
                    MatchedEntityItem(
                        entity_type=me["entity_type"],
                        source_value=me["source_value"],
                        related_value=me["related_value"],
                        similarity=me["similarity"],
                        match_type=me.get("match_type", "EXACT"),
                    )
                    for me in analysis["matching_entities"]
                ]

                res_item = CorrelationResult(
                    source_case=CaseSummary(
                        id=analysis["source_case"]["id"],
                        case_number=analysis["source_case"]["case_number"],
                        title=analysis["source_case"]["title"],
                        crime_type=analysis["source_case"]["crime_type"],
                        status=source_case_data.get("status"),
                    ),
                    related_case=CaseSummary(
                        id=analysis["related_case"]["id"],
                        case_number=analysis["related_case"]["case_number"],
                        title=analysis["related_case"]["title"],
                        crime_type=analysis["related_case"]["crime_type"],
                        status=cand_data.get("status"),
                        district=cand_data.get("district"),
                        fir_year=cand_data.get("fir_year"),
                        crime_head=cand_data.get("crime_head"),
                    ),
                    correlation_score=analysis["correlation_score"],
                    matching_entities=matched_entities,
                    matching_factors=analysis["matching_factors"],
                    factor_scores=analysis.get("factor_scores"),
                    explanation=analysis["explanation"],
                )
                correlations.append(res_item)

                # Persist or update correlation record in DB
                existing_corr = (
                    db.query(CaseCorrelation)
                    .filter(
                        CaseCorrelation.source_case_id == case_id,
                        CaseCorrelation.related_case_id == cand_id,
                    )
                    .first()
                )
                if existing_corr:
                    existing_corr.correlation_score = analysis["correlation_score"]
                    existing_corr.matching_factors = analysis["matching_factors"]
                    existing_corr.matching_entities = [m.model_dump() for m in matched_entities]
                    existing_corr.factor_scores = analysis.get("factor_scores")
                    existing_corr.explanation = analysis["explanation"]
                else:
                    new_corr = CaseCorrelation(
                        source_case_id=case_id,
                        related_case_id=cand_id,
                        correlation_score=analysis["correlation_score"],
                        matching_factors=analysis["matching_factors"],
                        matching_entities=[m.model_dump() for m in matched_entities],
                        factor_scores=analysis.get("factor_scores"),
                        explanation=analysis["explanation"],
                    )
                    db.add(new_corr)

        db.commit()

        # Sort descending by correlation score
        correlations.sort(key=lambda c: c.correlation_score, reverse=True)
        correlations = correlations[:10]

        # 4. Audit logging
        audit_entry = AuditEvent(
            user_id=current_user.id,
            user_email=current_user.email,
            action=AuditAction.CORRELATION_ANALYZED,
            status=AuditStatus.SUCCESS,
            details=json.dumps({
                "source_case_id": case_id,
                "candidate_count": len(candidate_ids),
                "correlations_found": len(correlations),
                "top_score": correlations[0].correlation_score if correlations else 0.0,
            }),
        )
        db.add(audit_entry)
        db.commit()

        return CorrelationListResponse(
            source_case_id=case_id,
            total=len(correlations),
            correlations=correlations,
        )
