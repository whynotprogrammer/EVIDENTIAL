import logging
import re
from typing import Any, Dict, List, Optional
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from backend.app.models.audit import AuditAction, AuditStatus
from backend.app.models.case import Case
from backend.app.models.document import Document, DocumentTranslation
from backend.app.models.entity import ExtractedEntity, EntityType
from backend.app.models.user import User, UserRole
from backend.app.schemas.search import SearchQuery, SearchResponse, SearchResultItem, SearchResultType
from backend.app.services.audit_service import log_audit_event

logger = logging.getLogger("evidential.search")


def sanitize_search_term(term: str) -> str:
    """Escapes SQL LIKE wildcards and removes dangerous escape sequences."""
    if not term:
        return ""
    # Escape SQL wildcards
    sanitized = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return sanitized.strip()


def extract_highlight_snippet(text: Optional[str], term: str, window: int = 60) -> str:
    """Extracts a contextual snippet around the matched search term."""
    if not text:
        return ""
    if not term:
        return text[: window * 2].strip() + ("..." if len(text) > window * 2 else "")

    lower_text = text.lower()
    lower_term = term.lower()
    idx = lower_text.find(lower_term)
    if idx == -1:
        # Check for partial word matches
        words = lower_term.split()
        for w in words:
            idx = lower_text.find(w)
            if idx != -1:
                break

    if idx == -1:
        return text[: window * 2].strip() + ("..." if len(text) > window * 2 else "")

    start = max(0, idx - window)
    end = min(len(text), idx + len(term) + window)
    snippet = text[start:end].replace("\n", " ").strip()
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


def execute_investigation_search(
    db: Session,
    current_user: User,
    query_params: SearchQuery,
    client_ip: str = "127.0.0.1",
) -> SearchResponse:
    """
    Executes case-authorized search across Cases, Documents, and Extracted Entities.
    
    CRITICAL RULE:
    Authorization MUST happen before retrieval.
    User A must never retrieve Case B data under any circumstances.
    """
    filters_applied: Dict[str, Any] = {}

    # Step 1: Enforce Authorization Boundary BEFORE Any Retrieval
    if current_user.role == UserRole.ADMIN:
        auth_case_ids_q = db.query(Case.id)
    else:
        # Non-admin users are strictly restricted to assigned cases or unassigned team cases
        auth_case_ids_q = db.query(Case.id).filter(
            or_(
                Case.assigned_officer_id == current_user.id,
                Case.created_by_id == current_user.id,
                Case.assigned_officer_id == None,
            )
        )

    authorized_case_ids = [c[0] for c in auth_case_ids_q.all()]

    # If the user has access to 0 cases, return empty response immediately
    if not authorized_case_ids:
        return SearchResponse(
            total=0,
            query=query_params.q,
            filters_applied=filters_applied,
            search_mode="KEYWORD_ENTITY_AUTHORIZED",
            results=[],
        )

    # Empty search query handling
    raw_q = query_params.q.strip() if query_params.q else ""
    sanitized_q = sanitize_search_term(raw_q)
    
    has_filter = bool(
        raw_q
        or query_params.case_number
        or query_params.entity_type
        or query_params.entity_value
        or query_params.crime_type
        or query_params.location
    )

    if not has_filter:
        # Empty search with no filters returns empty results
        return SearchResponse(
            total=0,
            query="",
            filters_applied={},
            search_mode="KEYWORD_ENTITY_AUTHORIZED",
            results=[],
        )

    collected_results: List[SearchResultItem] = []

    # -------------------------------------------------------------
    # 1. Search Cases (Title, Description, Case Number, Location, Crime Type)
    # -------------------------------------------------------------
    case_query = db.query(Case).filter(Case.id.in_(authorized_case_ids))

    if query_params.case_number:
        clean_cn = query_params.case_number.strip()
        case_query = case_query.filter(Case.case_number.ilike(f"%{clean_cn}%"))
        filters_applied["case_number"] = clean_cn

    if query_params.crime_type:
        clean_ct = query_params.crime_type.strip()
        case_query = case_query.filter(Case.crime_type.ilike(f"%{clean_ct}%"))
        filters_applied["crime_type"] = clean_ct

    if query_params.location:
        clean_loc = query_params.location.strip()
        case_query = case_query.filter(
            or_(
                Case.location.ilike(f"%{clean_loc}%"),
                Case.police_station.ilike(f"%{clean_loc}%"),
            )
        )
        filters_applied["location"] = clean_loc

    if raw_q:
        filters_applied["q"] = raw_q
        case_query = case_query.filter(
            or_(
                Case.case_number.ilike(f"%{sanitized_q}%"),
                Case.title.ilike(f"%{sanitized_q}%"),
                Case.description.ilike(f"%{sanitized_q}%"),
                Case.location.ilike(f"%{sanitized_q}%"),
                Case.police_station.ilike(f"%{sanitized_q}%"),
                Case.crime_type.ilike(f"%{sanitized_q}%"),
            )
        )

    matched_cases = case_query.all()
    for c in matched_cases:
        matched_field = "Case Record"
        snippet = c.title
        if raw_q and raw_q.lower() in (c.description or "").lower():
            matched_field = "Description"
            snippet = extract_highlight_snippet(c.description, raw_q)
        elif raw_q and raw_q.lower() in (c.case_number or "").lower():
            matched_field = "Case Number"
            snippet = c.case_number
        elif raw_q and raw_q.lower() in (c.location or "").lower():
            matched_field = "Location"
            snippet = c.location

        collected_results.append(
            SearchResultItem(
                result_type=SearchResultType.CASE,
                case_id=c.id,
                case_number=c.case_number,
                case_title=c.title,
                crime_type=c.crime_type,
                match_field=matched_field,
                match_snippet=snippet,
                score=1.0,
            )
        )

    # -------------------------------------------------------------
    # 2. Search Extracted Entities (PERSON, PHONE, VEHICLE, LOCATION, etc.)
    # -------------------------------------------------------------
    entity_query = (
        db.query(ExtractedEntity, Case)
        .join(Case, ExtractedEntity.case_id == Case.id)
        .filter(ExtractedEntity.case_id.in_(authorized_case_ids))
    )

    if query_params.entity_type:
        clean_et = query_params.entity_type.strip().upper()
        entity_query = entity_query.filter(ExtractedEntity.entity_type == clean_et)
        filters_applied["entity_type"] = clean_et

    if query_params.entity_value:
        clean_ev = query_params.entity_value.strip()
        entity_query = entity_query.filter(
            or_(
                ExtractedEntity.entity_value.ilike(f"%{clean_ev}%"),
                ExtractedEntity.normalized_value.ilike(f"%{clean_ev}%"),
            )
        )
        filters_applied["entity_value"] = clean_ev

    if query_params.location:
        clean_loc = query_params.location.strip()
        entity_query = entity_query.filter(
            and_(
                ExtractedEntity.entity_type == EntityType.LOCATION,
                ExtractedEntity.entity_value.ilike(f"%{clean_loc}%"),
            )
        )

    if raw_q and not query_params.entity_value:
        entity_query = entity_query.filter(
            or_(
                ExtractedEntity.entity_value.ilike(f"%{sanitized_q}%"),
                ExtractedEntity.normalized_value.ilike(f"%{sanitized_q}%"),
                ExtractedEntity.context_snippet.ilike(f"%{sanitized_q}%"),
            )
        )

    matched_entities = entity_query.all()
    for ent, c in matched_entities:
        snippet = ent.context_snippet or f"{ent.entity_type.value}: {ent.entity_value}"
        collected_results.append(
            SearchResultItem(
                result_type=SearchResultType.ENTITY,
                case_id=c.id,
                case_number=c.case_number,
                case_title=c.title,
                crime_type=c.crime_type,
                document_id=ent.document_id,
                entity_id=ent.id,
                entity_type=ent.entity_type.value,
                entity_value=ent.entity_value,
                match_field=f"Entity ({ent.entity_type.value})",
                match_snippet=snippet,
                score=0.95,
            )
        )

    # -------------------------------------------------------------
    # 3. Search Document Text (Original Text & Translations)
    # -------------------------------------------------------------
    if raw_q:
        doc_query = (
            db.query(Document, Case)
            .join(Case, Document.case_id == Case.id)
            .filter(Document.case_id.in_(authorized_case_ids))
        )

        doc_query = doc_query.filter(
            or_(
                Document.original_text.ilike(f"%{sanitized_q}%"),
                Document.original_filename.ilike(f"%{sanitized_q}%"),
            )
        )

        matched_docs = doc_query.all()
        for d, c in matched_docs:
            snippet = extract_highlight_snippet(d.original_text, raw_q)
            collected_results.append(
                SearchResultItem(
                    result_type=SearchResultType.DOCUMENT,
                    case_id=c.id,
                    case_number=c.case_number,
                    case_title=c.title,
                    crime_type=c.crime_type,
                    document_id=d.id,
                    document_filename=d.original_filename,
                    match_field="Original OCR Document Text",
                    match_snippet=snippet,
                    score=0.90,
                )
            )

        # Also search Document Translations
        trans_query = (
            db.query(DocumentTranslation, Document, Case)
            .join(Document, DocumentTranslation.document_id == Document.id)
            .join(Case, Document.case_id == Case.id)
            .filter(Document.case_id.in_(authorized_case_ids))
            .filter(DocumentTranslation.translated_text.ilike(f"%{sanitized_q}%"))
        )

        matched_trans = trans_query.all()
        for t, d, c in matched_trans:
            snippet = extract_highlight_snippet(t.translated_text, raw_q)
            collected_results.append(
                SearchResultItem(
                    result_type=SearchResultType.DOCUMENT,
                    case_id=c.id,
                    case_number=c.case_number,
                    case_title=c.title,
                    crime_type=c.crime_type,
                    document_id=d.id,
                    document_filename=d.original_filename,
                    match_field=f"Translation ({t.source_language} -> English)",
                    match_snippet=snippet,
                    score=0.88,
                )
            )

    # Total unpaginated results
    total_matches = len(collected_results)

    # Sort results by relevance score
    collected_results.sort(key=lambda r: r.score, reverse=True)

    # Apply Pagination (skip and limit)
    paginated_results = collected_results[query_params.skip : query_params.skip + query_params.limit]

    # Step 6: Audit Log Event
    log_audit_event(
        db=db,
        action=AuditAction.SEARCH_EXECUTED,
        user=current_user,
        resource_type="SEARCH",
        details=f"Search executed: q='{raw_q}', matches={total_matches}, authorized_cases={len(authorized_case_ids)}",
        ip_address=client_ip,
        status=AuditStatus.SUCCESS,
    )

    return SearchResponse(
        total=total_matches,
        query=raw_q,
        filters_applied=filters_applied,
        search_mode="KEYWORD_ENTITY_AUTHORIZED",
        results=paginated_results,
    )
