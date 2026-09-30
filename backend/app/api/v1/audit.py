from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ...db.database import get_db
from ...db.models import AuditLog
from ...core.security import get_current_user, require_role, ROLE_AUDITOR, ROLE_SUPERINTENDENT

router = APIRouter(prefix="/audit", tags=["Governance & Audit Logging"])

@router.get("/logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Retrieves immutable audit trail of engineering decisions, overrides, and queries.
    """
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details_json
        }
        for log in logs
    ]
