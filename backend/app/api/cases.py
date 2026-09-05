from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db, require_roles, verify_case_access
from backend.app.models.audit import AuditAction, AuditStatus
from backend.app.models.case import Case, CasePriority, CaseStatus
from backend.app.models.user import User, UserRole
from backend.app.schemas.case import CaseCreate, CaseOut, CaseUpdate
from backend.app.services.audit_service import log_audit_event

router = APIRouter(prefix="/cases", tags=["Cases"])


def find_case_by_identifier(case_id: str, db: Session) -> Optional[Case]:
    """Retrieve case by numeric database ID or unique case_number string."""
    if case_id.isdigit():
        case = db.query(Case).filter(Case.id == int(case_id)).first()
        if case:
            return case
    return db.query(Case).filter(Case.case_number == case_id.strip()).first()


@router.get("", response_model=List[CaseOut])
@router.get("/", response_model=List[CaseOut])
def list_cases(
    status: Optional[CaseStatus] = None,
    crime_type: Optional[str] = None,
    priority: Optional[CasePriority] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List cases with case-level authorization and search:
    - ADMIN sees all cases across the system.
    - Non-ADMIN users see only cases assigned to them or unassigned cases.
    - Search matches case_number, title, description, and location.
    """
    query = db.query(Case)

    # Case-level authorization filter
    if current_user.role != UserRole.ADMIN:
        query = query.filter(
            or_(
                Case.assigned_officer_id == current_user.id,
                Case.created_by_id == current_user.id,
                Case.assigned_officer_id == None,
            )
        )
    
    if status:
        query = query.filter(Case.status == status)
    if crime_type:
        query = query.filter(Case.crime_type.ilike(f"%{crime_type}%"))
    if priority:
        query = query.filter(Case.priority == priority)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Case.case_number.ilike(search_term),
                Case.title.ilike(search_term),
                Case.description.ilike(search_term),
                Case.location.ilike(search_term),
                Case.crime_type.ilike(search_term),
                Case.police_station.ilike(search_term),
            )
        )
    
    cases = query.order_by(Case.created_at.desc()).offset(skip).limit(limit).all()
    return cases


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    request: Request,
    case_in: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.INVESTIGATOR])),
):
    """
    Register a new investigation case.
    Role requirement: ADMIN or INVESTIGATOR.
    """
    existing = db.query(Case).filter(Case.case_number == case_in.case_number.strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case with number '{case_in.case_number}' already exists.",
        )
    
    assigned_id = (
        case_in.assigned_officer_id
        if (current_user.role == UserRole.ADMIN and case_in.assigned_officer_id)
        else current_user.id
    )

    db_case = Case(
        case_number=case_in.case_number.strip(),
        title=case_in.title,
        description=case_in.description,
        crime_type=case_in.crime_type,
        status=case_in.status or CaseStatus.UNDER_INVESTIGATION,
        priority=case_in.priority or CasePriority.HIGH,
        police_station=case_in.police_station or "Central Cyber Crime Cell",
        district=case_in.district,
        state=case_in.state,
        location=case_in.location,
        incident_date=case_in.incident_date,
        created_by_id=current_user.id,
        assigned_officer_id=assigned_id,
    )
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit_event(
        db=db,
        action=AuditAction.CASE_CREATED,
        user=current_user,
        resource_type="CASE",
        resource_id=str(db_case.id),
        details=f"Created case {db_case.case_number}: {db_case.title}",
        ip_address=client_ip,
        status=AuditStatus.SUCCESS,
    )

    return db_case


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    request: Request,
    case_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve details for a single case by ID or case_number.
    Enforces case-level authorization check.
    """
    case = find_case_by_identifier(case_id, db)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    
    # Enforce case authorization
    verify_case_access(case, current_user)

    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit_event(
        db=db,
        action=AuditAction.CASE_VIEWED,
        user=current_user,
        resource_type="CASE",
        resource_id=str(case.id),
        details=f"Viewed case {case.case_number}",
        ip_address=client_ip,
        status=AuditStatus.SUCCESS,
    )

    return case


@router.patch("/{case_id}", response_model=CaseOut)
@router.put("/{case_id}", response_model=CaseOut)
def update_case(
    case_id: str,
    case_update: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.INVESTIGATOR])),
):
    """
    Update case metadata or investigation status.
    Role requirement: ADMIN or assigned INVESTIGATOR.
    """
    case = find_case_by_identifier(case_id, db)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    
    # Enforce case authorization
    verify_case_access(case, current_user)
    
    update_data = case_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
    
    db.commit()
    db.refresh(case)
    return case
