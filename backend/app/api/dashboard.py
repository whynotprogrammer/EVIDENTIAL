from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import func
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
    total_cases = db.query(Case).count()
    active_investigations = (
        db.query(Case)
        .filter(Case.status.in_([CaseStatus.OPEN, CaseStatus.UNDER_INVESTIGATION]))
        .count()
    )
    documents_processed = (
        db.query(Document)
        .filter(Document.processing_status == DocumentProcessingStatus.COMPLETED)
        .count()
    )
    total_evidence = db.query(Evidence).count()

    # Cases grouped by status
    status_counts = (
        db.query(Case.status, func.count(Case.id))
        .group_by(Case.status)
        .all()
    )
    cases_by_status = [
        {"name": status.value if hasattr(status, "value") else str(status), "count": count}
        for status, count in status_counts
    ]

    # Cases grouped by crime type
    crime_counts = (
        db.query(Case.crime_type, func.count(Case.id))
        .group_by(Case.crime_type)
        .order_by(func.count(Case.id).desc())
        .limit(8)
        .all()
    )
    cases_by_crime_type = [{"name": crime, "count": count} for crime, count in crime_counts]

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
    recent_audits = (
        db.query(AuditEvent)
        .order_by(AuditEvent.timestamp.desc())
        .limit(10)
        .all()
    )
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
        "cases_by_language": cases_by_language,
        "recent_audit_events": audit_list,
    }
