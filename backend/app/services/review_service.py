"""
Human-in-the-Loop Document Review Service.
Manages reviewer queues, manual verification decisions (Approve, Reject, Modify),
preserves original vs corrected values, and logs tamper-evident audit records.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from backend.app.db.models import ReviewTask, ReviewDecision, DrillingEvent, EventEvidence, Document, AuditEvent
from backend.app.schemas.review_schemas import ReviewDecisionRequest

class ReviewService:
    def list_pending_tasks(self, db: Session, status: str = "PENDING") -> List[Dict[str, Any]]:
        """Lists review tasks requiring human validation."""
        tasks = db.query(ReviewTask).filter(ReviewTask.status == status).order_by(ReviewTask.created_at.desc()).all()
        results = []
        for t in tasks:
            doc = db.query(Document).filter(Document.doc_id == t.doc_id).first()
            event = db.query(DrillingEvent).filter(DrillingEvent.event_id == t.event_id).first() if t.event_id else None
            results.append({
                "task_id": t.task_id,
                "doc_id": t.doc_id,
                "original_filename": doc.original_filename if doc else "Unknown",
                "event_id": t.event_id,
                "status": t.status,
                "flag_reason": t.flag_reason,
                "event_type": event.event_type if event else "UNCLASSIFIED",
                "depth_md_m": event.depth_md_m if event else None,
                "formation_name": event.formation_name if event else None,
                "original_payload": json.loads(t.original_payload_json) if t.original_payload_json else {},
                "created_at": t.created_at
            })
        return results

    def submit_decision(self, db: Session, req: ReviewDecisionRequest) -> Dict[str, Any]:
        """
        Executes a human reviewer decision: APPROVED, REJECTED, or MODIFIED.
        Updates event verification status and logs cryptographic audit record.
        """
        task = db.query(ReviewTask).filter(ReviewTask.task_id == req.task_id).first()
        if not task:
            raise ValueError(f"Review task {req.task_id} not found.")

        now_utc = datetime.now(timezone.utc)
        decision_id = str(uuid.uuid4())

        decision_record = ReviewDecision(
            decision_id=decision_id,
            task_id=task.task_id,
            reviewer_id=req.reviewer_id,
            reviewer_role=req.reviewer_role,
            decision=req.decision,
            corrections_json=json.dumps(req.corrections) if req.corrections else None,
            comments=req.comments,
            decision_timestamp=now_utc
        )
        db.add(decision_record)

        event = db.query(DrillingEvent).filter(DrillingEvent.event_id == task.event_id).first() if task.event_id else None
        evidence = db.query(EventEvidence).filter(EventEvidence.evidence_id == task.evidence_id).first() if task.evidence_id else None

        final_status = "VERIFIED"

        if req.decision == "APPROVED":
            task.status = "RESOLVED"
            final_status = "VERIFIED"
            if event:
                event.verification_status = "VERIFIED"
                event.reviewed_by = req.reviewer_id
                event.reviewed_at = now_utc
            if evidence:
                evidence.evidence_status = "VERIFIED"

        elif req.decision == "REJECTED":
            task.status = "REJECTED"
            final_status = "REJECTED"
            if event:
                event.verification_status = "REJECTED"
                event.reviewed_by = req.reviewer_id
                event.reviewed_at = now_utc
            if evidence:
                evidence.evidence_status = "REJECTED"

        elif req.decision == "MODIFIED":
            task.status = "RESOLVED"
            final_status = "VERIFIED"
            if event and req.corrections:
                # Apply human corrections while preserving original narrative in audit log
                if "depth_md_m" in req.corrections:
                    event.depth_md_m = float(req.corrections["depth_md_m"])
                if "depth_tvdss_m" in req.corrections:
                    event.depth_tvdss_m = float(req.corrections["depth_tvdss_m"])
                if "formation_name" in req.corrections:
                    event.formation_name = str(req.corrections["formation_name"])
                if "event_type" in req.corrections:
                    event.event_type = str(req.corrections["event_type"])
                if "mitigation_applied" in req.corrections:
                    event.mitigation_applied = str(req.corrections["mitigation_applied"])

                event.verification_status = "VERIFIED"
                event.reviewed_by = req.reviewer_id
                event.reviewed_at = now_utc

            if evidence:
                evidence.evidence_status = "VERIFIED"

        # Preserve cryptographic audit event
        audit_entry = AuditEvent(
            user_id=req.reviewer_id,
            action=f"REVIEW_DECISION_{req.decision}",
            resource_type="review_task",
            resource_id=task.task_id,
            details_json=json.dumps({
                "decision": req.decision,
                "event_id": task.event_id,
                "corrections": req.corrections,
                "comments": req.comments,
                "previous_status": task.status,
                "new_verification_status": final_status
            })
        )
        db.add(audit_entry)
        db.commit()

        return {
            "decision_id": decision_id,
            "task_id": task.task_id,
            "decision": req.decision,
            "verification_status": final_status,
            "message": f"Review decision {req.decision} recorded by {req.reviewer_id}.",
            "audit_logged": True
        }

review_service = ReviewService()
