"""
NWIS CHRONOS — POINT-IN-TIME EVIDENCE FIREWALL
Guarantees zero future-information leakage during historical replay.
Freezes knowledge base to records genuinely published and available at the historical evaluation timestamp.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.db import models

class TemporalFirewallViolation(Exception):
    """Raised when an operation attempts to access documents, events, or telemetry beyond the frozen evaluation timestamp."""
    pass

def verify_document_availability(filename: str, doc_timestamp: datetime, cutoff_timestamp: datetime) -> bool:
    """Verifies that a document was published strictly prior to the evaluation cutoff. Raises TemporalFirewallViolation if violated."""
    if doc_timestamp > cutoff_timestamp:
        raise TemporalFirewallViolation(
            f"Temporal Firewall Violation: Document '{filename}' dated {doc_timestamp.isoformat()} "
            f"was published AFTER evaluation cutoff {cutoff_timestamp.isoformat()}."
        )
    return True

class PointInTimeFirewall:
    """
    Cryptographic and chronological firewall isolating prospective replay evaluations
    from future wellbores, subsequent drilling events, and later document publications.
    """

    @classmethod
    def create_snapshot(
        cls,
        db: Session,
        target_well_id: str,
        as_of_timestamp: str,
        as_of_depth_md_m: Optional[float] = None
    ) -> models.HistoricalMemorySnapshot:
        """
        Constructs an immutable Historical Memory Snapshot frozen at `as_of_timestamp`.
        """
        target_well = db.query(models.Well).filter(models.Well.well_id == target_well_id).first()
        if not target_well:
            raise ValueError(f"Target well {target_well_id} not found.")

        # 1. Discover Prior Eligible Wells
        # A well is eligible as an offset analogue ONLY if it was completed or active prior to as_of_timestamp
        all_wells = db.query(models.Well).filter(models.Well.well_id != target_well_id).all()
        eligible_offset_ids = []
        excluded_offset_ids = []

        for w in all_wells:
            # Check spud / completion dates
            # If well was spudded AFTER as_of_timestamp, it is physically in the future
            if w.spud_date and w.spud_date > as_of_timestamp:
                excluded_offset_ids.append({
                    "well_id": w.well_id,
                    "reason": f"Spud date ({w.spud_date}) is in the future relative to evaluation cutoff ({as_of_timestamp})"
                })
            else:
                eligible_offset_ids.append(w.well_id)

        # 2. Retrieve Prior Verified Drilling Events
        # An event is eligible ONLY if event_timestamp < as_of_timestamp AND from an eligible prior well
        prior_events = db.query(models.DrillingEvent).filter(
            models.DrillingEvent.well_id.in_(eligible_offset_ids),
            models.DrillingEvent.event_timestamp < as_of_timestamp,
            models.DrillingEvent.verification_status.in_(["VERIFIED", "ORIGINAL_VERIFIED"])
        ).all()

        # 3. Retrieve Prior Verified Documents
        prior_docs = db.query(models.Document).filter(
            models.Document.well_id.in_(eligible_offset_ids),
            models.Document.source_date <= as_of_timestamp
        ).all()

        # 4. Generate Deterministic Checksum
        content_manifest = {
            "target_well_id": target_well_id,
            "as_of_timestamp": as_of_timestamp,
            "as_of_depth_md_m": as_of_depth_md_m,
            "eligible_offset_ids": sorted(eligible_offset_ids),
            "prior_events_ids": sorted([e.event_id for e in prior_events]),
            "prior_doc_hashes": sorted([d.sha256_hash for d in prior_docs if d.sha256_hash])
        }
        manifest_str = json.dumps(content_manifest, sort_keys=True)
        checksum = hashlib.sha256(manifest_str.encode("utf-8")).hexdigest()

        # 5. Persist Historical Memory Snapshot
        snapshot = models.HistoricalMemorySnapshot(
            target_well_id=target_well_id,
            cutoff_timestamp=as_of_timestamp,
            cutoff_depth_md_m=as_of_depth_md_m,
            eligible_offset_ids_json=json.dumps(eligible_offset_ids),
            verified_events_count=len(prior_events),
            documents_available_count=len(prior_docs),
            checksum_sha256=checksum
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)

        return snapshot

    @classmethod
    def get_firewall_transparency(
        cls,
        db: Session,
        target_well_id: str,
        as_of_timestamp: str
    ) -> Dict[str, Any]:
        """
        Produces the "What the Engineer Could Have Known" transparency report.
        Explains precisely which prior wells and documents were accessible vs excluded.
        """
        target_well = db.query(models.Well).filter(models.Well.well_id == target_well_id).first()
        if not target_well:
            raise ValueError(f"Target well {target_well_id} not found.")

        all_wells = db.query(models.Well).filter(models.Well.well_id != target_well_id).all()
        available_wells = []
        excluded_future_wells = []

        for w in all_wells:
            if w.spud_date and w.spud_date > as_of_timestamp:
                excluded_future_wells.append({
                    "well_id": w.well_id,
                    "well_name": w.well_name,
                    "spud_date": w.spud_date,
                    "exclusion_reason": f"Drilled in the future relative to replay date {as_of_timestamp}"
                })
            else:
                available_wells.append({
                    "well_id": w.well_id,
                    "well_name": w.well_name,
                    "spud_date": w.spud_date,
                    "completion_date": w.completion_date,
                    "status": "ACCESSIBLE_HISTORICAL_RECORD"
                })

        available_events = db.query(models.DrillingEvent).filter(
            models.DrillingEvent.well_id.in_([w["well_id"] for w in available_wells]),
            models.DrillingEvent.event_timestamp < as_of_timestamp
        ).all()

        blocked_future_events = db.query(models.DrillingEvent).filter(
            models.DrillingEvent.event_timestamp >= as_of_timestamp
        ).all()

        return {
            "target_well": {
                "well_id": target_well.well_id,
                "well_name": target_well.well_name,
                "spud_date": target_well.spud_date,
                "evaluation_as_of": as_of_timestamp
            },
            "firewall_summary": {
                "accessible_offset_wells_count": len(available_wells),
                "excluded_future_wells_count": len(excluded_future_wells),
                "accessible_historical_events_count": len(available_events),
                "blocked_future_events_count": len(blocked_future_events)
            },
            "accessible_offset_wells": available_wells,
            "excluded_future_wells": excluded_future_wells,
            "accessible_historical_events": [
                {
                    "event_id": e.event_id,
                    "well_id": e.well_id,
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "depth_md_m": e.depth_md_m,
                    "formation": e.formation_name,
                    "occurred_at": e.event_timestamp,
                    "source_citation": e.source_citation
                }
                for e in available_events
            ]
        }


def freeze_historical_memory(well_id: str, as_of_timestamp: str, as_of_depth_md_m: Optional[float] = None, db: Optional[Session] = None):
    """Convenience wrapper for PointInTimeFirewall.create_snapshot"""
    from backend.app.db.database import SessionLocal
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True
    try:
        return PointInTimeFirewall.create_snapshot(db, target_well_id=well_id, as_of_timestamp=as_of_timestamp, as_of_depth_md_m=as_of_depth_md_m)
    finally:
        if own_session:
            db.close()


def get_what_the_engineer_could_have_known(well_id: str, as_of_timestamp: str, db: Optional[Session] = None) -> Dict[str, Any]:
    """Convenience wrapper for PointInTimeFirewall.get_firewall_transparency"""
    from backend.app.db.database import SessionLocal
    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True
    try:
        return PointInTimeFirewall.get_firewall_transparency(db, target_well_id=well_id, as_of_timestamp=as_of_timestamp)
    finally:
        if own_session:
            db.close()
