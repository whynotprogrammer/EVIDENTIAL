from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.correlation import (
    CorrelationAnalyzeRequest,
    CorrelationListResponse,
)
from backend.app.services.correlation_service import CorrelationService

router = APIRouter(tags=["Cross-FIR Correlation"])


@router.get(
    "/cases/{case_id}/correlations",
    response_model=CorrelationListResponse,
    summary="Get explainable cross-FIR correlations for a specific case",
)
def get_case_correlations(
    case_id: int,
    min_threshold: float = Query(0.25, ge=0.0, le=1.0, description="Minimum correlation score threshold"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Computes explainable cross-FIR correlations for the designated source case.
    Strictly enforces pre-retrieval authorization.
    """
    return CorrelationService.get_correlations_for_case(
        db=db,
        current_user=current_user,
        case_id=case_id,
        min_threshold=min_threshold,
    )


@router.post(
    "/correlations/analyze",
    response_model=CorrelationListResponse,
    summary="Trigger ad-hoc cross-FIR correlation comparison",
)
def analyze_correlations(
    req: CorrelationAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Triggers on-demand correlation analysis between source case and target case
    or across all authorized cases.
    """
    return CorrelationService.get_correlations_for_case(
        db=db,
        current_user=current_user,
        case_id=req.source_case_id,
        target_case_id=req.target_case_id,
        min_threshold=req.min_threshold or 0.25,
    )
