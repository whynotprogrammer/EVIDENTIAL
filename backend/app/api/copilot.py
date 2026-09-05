from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.copilot import (
    CopilotCaseSummaryResponse,
    CopilotQueryRequest,
    CopilotQueryResponse,
)
from backend.app.services.copilot_service import CopilotService

router = APIRouter(tags=["AI Investigation Copilot"])


@router.post(
    "/copilot/query",
    response_model=CopilotQueryResponse,
    summary="Query AI Copilot with grounded case context and citations",
)
def query_copilot(
    payload: CopilotQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Executes a grounded investigative query against strictly authorized case records.
    Returns verifiable source citations, defends against prompt injections,
    and returns explicit uncertainty fallback when evidence is absent.
    """
    return CopilotService.query(
        db=db,
        current_user=current_user,
        payload=payload,
    )


@router.get(
    "/cases/{case_id}/copilot/summary",
    response_model=CopilotCaseSummaryResponse,
    summary="Get grounded AI executive case summary with citations",
)
def get_case_copilot_summary(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generates an instant, grounded AI overview of the case including
    identified persons, evidence counts, timeline event counts, and source citations.
    """
    return CopilotService.get_summary(
        db=db,
        current_user=current_user,
        case_id=case_id,
    )
