import logging
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger("nwis.audit")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class AuditLogger:
    @staticmethod
    def compute_record_hash(prev_hash: str, payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(f"{prev_hash}:{serialized}".encode("utf-8")).hexdigest()

    @staticmethod
    def log_action(
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Dict[str, Any],
        client_ip: Optional[str] = "127.0.0.1"
    ) -> Dict[str, Any]:
        audit_payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "client_ip": client_ip,
            "details": details
        }
        
        # In production this appends to PostgreSQL tamper-evident table
        logger.info(f"AUDIT_RECORD: {json.dumps(audit_payload, default=str)}")
        return audit_payload

audit_logger = AuditLogger()
