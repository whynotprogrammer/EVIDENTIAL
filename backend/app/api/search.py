from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.search import SearchQuery, SearchResponse
from backend.app.services.search_service import execute_investigation_search

router = APIRouter(prefix="/search", tags=["Investigation Search"])


@router.get("", response_model=SearchResponse)
@router.get("/", response_model=SearchResponse)
def search_investigation_get(
    request: Request,
    q: Optional[str] = Query(None, description="Keyword search term"),
    case_number: Optional[str] = Query(None, description="Case number search"),
    entity_type: Optional[str] = Query(None, description="Entity type filter (e.g. PHONE, VEHICLE, PERSON)"),
    entity_value: Optional[str] = Query(None, description="Entity value filter"),
    crime_type: Optional[str] = Query(None, description="Crime type filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max results per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Case-authorized investigation search endpoint (GET).
    Searches across authorized Cases, Documents, and Extracted Entities.
    """
    query_params = SearchQuery(
        q=q,
        case_number=case_number,
        entity_type=entity_type,
        entity_value=entity_value,
        crime_type=crime_type,
        location=location,
        skip=skip,
        limit=limit,
    )
    client_ip = request.client.host if request.client else "127.0.0.1"
    return execute_investigation_search(
        db=db,
        current_user=current_user,
        query_params=query_params,
        client_ip=client_ip,
    )


@router.post("", response_model=SearchResponse)
@router.post("/", response_model=SearchResponse)
def search_investigation_post(
    request: Request,
    query_params: SearchQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Case-authorized investigation search endpoint (POST).
    Searches across authorized Cases, Documents, and Extracted Entities using structured payload.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    return execute_investigation_search(
        db=db,
        current_user=current_user,
        query_params=query_params,
        client_ip=client_ip,
    )
