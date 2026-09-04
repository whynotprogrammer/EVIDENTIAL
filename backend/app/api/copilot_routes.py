from fastapi import APIRouter, HTTPException, Depends, Header, status
from typing import Optional
from backend.app.schemas.copilot_models import (
    UserProfile,
    UserRole,
    ClearanceLevel,
    CopilotQueryRequest,
    CopilotQueryResponse,
)
from security.authorization.case_guard import (
    UnauthorizedCaseAccessException,
    CaseIsolationViolationException,
)
from ai.rag.security import PromptInjectionDetectedException
from ai.rag.copilot import InvestigationCopilot

router = APIRouter(prefix="/api/v1/cases", tags=["Investigation Copilot"])

# Default in-memory copilot service instance
_copilot_instance = InvestigationCopilot()


def get_current_user(
    x_user_id: Optional[str] = Header(default="INV-101"),
    x_username: Optional[str] = Header(default="OfficerSen"),
    x_user_role: Optional[str] = Header(default="INVESTIGATOR"),
    x_clearance: Optional[int] = Header(default=3),
    x_assigned_cases: Optional[str] = Header(default="CASE-2024-001"),
) -> UserProfile:
    """Extracts simulated authenticated user context from request headers."""
    assigned_list = [c.strip() for c in x_assigned_cases.split(",") if c.strip()] if x_assigned_cases else []
    try:
        role = UserRole(x_user_role)
    except ValueError:
        role = UserRole.INVESTIGATOR

    try:
        clearance = ClearanceLevel(x_clearance)
    except ValueError:
        clearance = ClearanceLevel.RESTRICTED

    return UserProfile(
        user_id=x_user_id or "ANON",
        username=x_username or "anonymous",
        role=role,
        clearance=clearance,
        assigned_case_ids=assigned_list,
        is_admin=(role == UserRole.ADMIN),
    )


@router.post(
    "/{case_id}/copilot/ask",
    response_model=CopilotQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask investigative questions to the Grounded Copilot",
)
def ask_copilot(
    case_id: str,
    request: CopilotQueryRequest,
    current_user: UserProfile = Depends(get_current_user),
) -> CopilotQueryResponse:
    """Executes a grounded, evidence-backed query against an authorized case."""
    if request.case_id != case_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path case_id '{case_id}' does not match request body case_id '{request.case_id}'.",
        )

    try:
        response = _copilot_instance.ask(user=current_user, request=request)
        return response
    except UnauthorizedCaseAccessException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except PromptInjectionDetectedException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CaseIsolationViolationException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security alert: {str(e)}",
        )
