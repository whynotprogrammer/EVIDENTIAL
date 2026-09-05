from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.core.config import settings
from backend.app.core.security import create_access_token, verify_password
from backend.app.models.audit import AuditAction, AuditStatus
from backend.app.models.user import User
from backend.app.schemas.token import LoginRequest, Token
from backend.app.schemas.user import UserOut
from backend.app.services.audit_service import log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email and password, returning a signed JWT access token."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    user = db.query(User).filter(User.email == login_data.email.strip().lower()).first()
    
    if not user or not verify_password(login_data.password, user.hashed_password):
        # Log failed attempt
        log_audit_event(
            db=db,
            action=AuditAction.LOGIN,
            user=user,
            resource_type="USER",
            resource_id=str(user.id) if user else login_data.email,
            details=f"Failed login attempt for {login_data.email}",
            ip_address=client_ip,
            status=AuditStatus.FAILURE,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated. Contact system administrator.",
        )

    # Issue JWT token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        role=user.role.value,
        expires_delta=access_token_expires,
    )

    # Log successful login
    log_audit_event(
        db=db,
        action=AuditAction.LOGIN,
        user=user,
        resource_type="USER",
        resource_id=str(user.id),
        details=f"Successful login for {user.email} [{user.role.value}]",
        ip_address=client_ip,
        status=AuditStatus.SUCCESS,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Fetch profile of currently authenticated user."""
    return current_user


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Log out current user and record audit log entry."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    log_audit_event(
        db=db,
        action=AuditAction.LOGOUT,
        user=current_user,
        resource_type="USER",
        resource_id=str(current_user.id),
        details=f"User {current_user.email} logged out",
        ip_address=client_ip,
        status=AuditStatus.SUCCESS,
    )
    return {"message": "Successfully logged out"}
