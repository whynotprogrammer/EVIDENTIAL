from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.timeline import (
    CaseTimelineResponse,
    TimelineEventCreate,
    TimelineEventOut,
)
from backend.app.services.timeline_service import TimelineService

router = APIRouter(tags=["Investigation Timeline"])


@router.get(
    "/cases/{case_id}/timeline",
    response_model=CaseTimelineResponse,
    summary="Get source-grounded chronological investigation timeline for a case",
)
def get_case_timeline(
    case_id: int,
    order: str = Query("asc", pattern="^(asc|desc)$", description="Chronological sorting order (asc or desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Synthesizes a source-grounded, chronological timeline across FIR registration,
    documents, AI extractions, evidence, and official officer milestones.
    Pre-retrieval authorization is strictly enforced.
    """
    return TimelineService.get_case_timeline(
        db=db,
        current_user=current_user,
        case_id=case_id,
        order=order,
    )


@router.post(
    "/cases/{case_id}/timeline/events",
    response_model=TimelineEventOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record an official verified investigation milestone",
)
def create_case_timeline_event(
    case_id: int,
    payload: TimelineEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Allows an authorized officer to record an official investigation event
    with source document attribution.
    """
    return TimelineService.create_investigation_event(
        db=db,
        current_user=current_user,
        case_id=case_id,
        payload=payload,
    )
