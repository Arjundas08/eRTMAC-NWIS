from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ...db.database import get_db
from ...schemas.ask_schemas import AskNWISRequest, AskNWISResponse
from ...services.rag_service import rag_service
from ...core.security import get_current_user

router = APIRouter(prefix="/ask", tags=["Ask NWIS Knowledge Copilot"])

@router.post("", response_model=AskNWISResponse)
def ask_nwis_endpoint(
    request: AskNWISRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Answers complex drilling questions grounded strictly in historical offset evidence.
    """
    return rag_service.answer_engineering_query(db, request)
