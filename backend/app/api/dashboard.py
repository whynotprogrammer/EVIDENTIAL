from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.audit import AuditEvent
from backend.app.models.case import Case, CaseStatus
from backend.app.models.document import Document, DocumentProcessingStatus
from backend.app.models.evidence import Evidence
from backend.app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Provide aggregated command center metrics and distribution charts."""
    # The command-center FIR figures intentionally include only imported source
    # records, never manually created demo/investigation cases.
    fir_query = db.query(Case).filter(Case.source_record_key != None)
    total_cases = fir_query.count()
    active_investigations = (
        fir_query.filter(Case.fir_stage == "Under Investigation")
        .count()
    )
    # Existing installations may predate document/evidence schema migrations.
    # These optional non-FIR counters must never prevent verified FIR metrics
    # from loading.
    try:
        documents_processed = (
            db.query(Document)
            .filter(Document.processing_status == DocumentProcessingStatus.COMPLETED)
            .count()
        )
    except OperationalError:
        db.rollback()
        documents_processed = 0
    try:
        total_evidence = db.query(Evidence).count()
    except OperationalError:
        db.rollback()
        total_evidence = 0

    # Cases grouped by status
    status_counts = (
        fir_query.with_entities(Case.fir_stage, func.count(Case.id))
        .group_by(Case.fir_stage)
        .all()
    )
    cases_by_status = [
        {"name": status or "Not Available", "count": count}
        for status, count in status_counts
    ]

    # Cases grouped by crime type
    crime_counts = (
        fir_query.with_entities(Case.crime_type, func.count(Case.id))
        .group_by(Case.crime_type)
        .order_by(func.count(Case.id).desc())
        .limit(8)
        .all()
    )
    cases_by_crime_type = [{"name": crime, "count": count} for crime, count in crime_counts]

    def grouped(column):
        return [
            {"name": str(value) if value is not None else "Not Available", "count": count}
            for value, count in fir_query.with_entities(column, func.count(Case.id)).group_by(column).order_by(func.count(Case.id).desc()).all()
        ]

    # Cases/documents grouped by detected language
    lang_counts = (
        db.query(Document.detected_language, func.count(Document.id))
        .filter(Document.detected_language != None)
        .group_by(Document.detected_language)
        .all()
    )
    cases_by_language = [
        {"name": lang if lang else "Unknown", "count": count}
        for lang, count in lang_counts
    ]

    # Recent Audit Log Activity
    try:
        recent_audits = (
            db.query(AuditEvent)
            .order_by(AuditEvent.timestamp.desc())
            .limit(10)
            .all()
        )
    except OperationalError:
        db.rollback()
        recent_audits = []
    audit_list = [
        {
            "id": a.id,
            "action": a.action.value if hasattr(a.action, "value") else str(a.action),
            "user_email": a.user_email,
            "resource_type": a.resource_type,
            "resource_id": a.resource_id,
            "details": a.details,
            "status": a.status.value if hasattr(a.status, "value") else str(a.status),
            "timestamp": a.timestamp.isoformat(),
        }
        for a in recent_audits
    ]

    return {
        "metrics": {
            "total_cases": total_cases,
            "active_investigations": active_investigations,
            "documents_processed": documents_processed,
            "evidence_items": total_evidence,
            "potential_correlations": 0,  # Updated dynamically when correlation runs
        },
        "cases_by_status": cases_by_status,
        "cases_by_crime_type": cases_by_crime_type,
        "firs_by_district": grouped(Case.district),
        "firs_by_crime_head": grouped(Case.crime_head),
        "firs_by_year": grouped(Case.fir_year),
        "firs_by_month": grouped(Case.fir_month),
        "records_with_valid_coordinates": fir_query.filter(Case.latitude != None, Case.longitude != None).count(),
        "cases_by_language": cases_by_language,
        "recent_audit_events": audit_list,
    }
