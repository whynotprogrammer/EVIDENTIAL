import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.case import Case
from backend.app.models.user import User
from backend.app.schemas.court_package import CourtEvidencePackageOut, CourtPackageReadiness
from backend.app.services.court_package_service import CourtPackageService

logger = logging.getLogger("evidential.court_package.api")

router = APIRouter(prefix="/cases", tags=["Court Evidence Package"])


def resolve_case_id(case_id_str: str, db: Session) -> int:
    """Helper to resolve numeric case ID from integer string or case_number."""
    if case_id_str.isdigit():
        c = db.query(Case).filter(Case.id == int(case_id_str)).first()
        if c:
            return c.id
    c = db.query(Case).filter(Case.case_number == case_id_str.strip()).first()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case identifier '{case_id_str}' not found.",
        )
    return c.id


@router.get("/{case_id}/court-package/readiness", response_model=CourtPackageReadiness)
def get_package_readiness(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get dynamic readiness checklist across all 11 court package sections
    using real case data. Returns availability status, counts, missing items, and preview.
    """
    cid = resolve_case_id(case_id, db)
    return CourtPackageService.get_package_readiness(db, current_user, cid)


@router.post("/{case_id}/court-package", response_model=CourtEvidencePackageOut, status_code=status.HTTP_201_CREATED)
def generate_court_package(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate, hash, and persist an official Court Evidence Package for a case.
    Logs an audit trail entry and a timeline milestone.
    """
    cid = resolve_case_id(case_id, db)
    return CourtPackageService.generate_package(db, current_user, cid)


@router.get("/{case_id}/court-package/latest", response_model=Optional[CourtEvidencePackageOut])
def get_latest_court_package(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the most recent Court Evidence Package generated for this case if any exists.
    """
    cid = resolve_case_id(case_id, db)
    return CourtPackageService.get_latest_package(db, current_user, cid)


@router.get("/{case_id}/court-package/{package_id}", response_model=CourtEvidencePackageOut)
def get_court_package_by_id(
    case_id: str,
    package_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a specific Court Evidence Package by package_id or database ID.
    """
    cid = resolve_case_id(case_id, db)
    return CourtPackageService.get_package_by_id(db, current_user, cid, package_id)
