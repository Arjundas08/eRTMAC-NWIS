"""
NWIS CHRONOS — HISTORICAL REPLAY ENGINE
Deterministic chronological simulation of historical drilling operations.
Features step, play/pause, jump-to-incident, point-in-time firewall enforcement,
and automated advisory generation with lead-distance accounting.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.db import models
from backend.app.services.trajectory_engine import TrajectoryEngine, InsufficientGeologicalEvidenceError
from backend.app.services.chronos_firewall import PointInTimeFirewall

class ChronosReplayEngine:
    """
    Executes reproducible historical drilling replays without accessing future operational outcomes.
    """

    @classmethod
    def start_replay_session(
        cls,
        db: Session,
        well_id: str,
        start_depth_md_m: float = 2650.0,
        end_depth_md_m: Optional[float] = None,
        lookahead_window_m: float = 100.0,
        speed_factor: float = 1.0
    ) -> Dict[str, Any]:
        well = db.query(models.Well).filter(models.Well.well_id == well_id).first()
        if not well:
            raise ValueError(f"Well {well_id} not found.")

        actual_end_depth = end_depth_md_m or (well.total_depth_md_m or 3400.0)

        # 1. Establish Point-in-Time Cutoff Date based on well spud
        # For a prospective replay, the initial cutoff is the spud date
        cutoff_date = well.spud_date or "2008-08-02"

        # 2. Freeze Historical Memory Snapshot
        snapshot = PointInTimeFirewall.create_snapshot(
            db, target_well_id=well_id, as_of_timestamp=cutoff_date, as_of_depth_md_m=start_depth_md_m
        )

        # 3. Create Session
        session = models.ReplaySession(
            well_id=well_id,
            start_depth_md_m=start_depth_md_m,
            current_depth_md_m=start_depth_md_m,
            end_depth_md_m=actual_end_depth,
            start_time=cutoff_date,
            current_time=cutoff_date,
            speed_factor=speed_factor,
            status="INITIALIZED",
            snapshot_id=snapshot.snapshot_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # Return initial step state
        return cls.get_session_state(db, session.session_id, lookahead_window_m=lookahead_window_m)

    @classmethod
    def get_session_state(
        cls,
        db: Session,
        session_id: str,
        lookahead_window_m: float = 100.0
    ) -> Dict[str, Any]:
        session = db.query(models.ReplaySession).filter(models.ReplaySession.session_id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        well = db.query(models.Well).filter(models.Well.well_id == session.well_id).first()
        snapshot = db.query(models.HistoricalMemorySnapshot).filter(
            models.HistoricalMemorySnapshot.snapshot_id == session.snapshot_id
        ).first()

        eligible_offset_ids = json.loads(snapshot.eligible_offset_ids_json) if snapshot else []

        # Calculate TVD and TVDSS for current bit depth
        surveys = db.query(models.WellboreSurvey).filter(
            models.WellboreSurvey.well_id == session.well_id
        ).order_by(models.WellboreSurvey.md_m.asc()).all()

        raw_surveys = [
            {"md_m": s.md_m, "inclination_deg": s.inclination_deg, "azimuth_deg": s.azimuth_deg}
            for s in surveys
        ]
        traj = TrajectoryEngine.compute_trajectory(raw_surveys, well.kb_elevation_m)
        bit_station = TrajectoryEngine.interpolate_at_md(traj, session.current_depth_md_m, well.kb_elevation_m)

        # Determine current geological formation
        formations = db.query(models.FormationTop).filter(
            models.FormationTop.well_id == session.well_id
        ).order_by(models.FormationTop.top_md_m.asc()).all()

        cur_formation = "Nordland GP"
        next_formation = None
        for i, f in enumerate(formations):
            next_top = formations[i + 1].top_md_m if i + 1 < len(formations) else 99999.0
            if f.top_md_m <= session.current_depth_md_m < next_top:
                cur_formation = f.formation_name
                if i + 1 < len(formations):
                    next_formation = formations[i + 1]
                break

        # Generate Telemetry packet
        telemetry = {
            "bit_depth_md_m": round(session.current_depth_md_m, 2),
            "bit_depth_tvd_m": round(bit_station.tvd_m, 2),
            "bit_depth_tvdss_m": round(bit_station.tvdss_m, 2),
            "inclination_deg": round(bit_station.inclination_deg, 2),
            "azimuth_deg": round(bit_station.azimuth_deg, 2),
            "current_formation": cur_formation,
            "next_formation_top_md": next_formation.top_md_m if next_formation else None,
            "rop_m_hr": round(14.5 + (session.current_depth_md_m % 5) * 1.2, 1),
            "wob_klbs": round(21.0 + (session.current_depth_md_m % 4) * 0.8, 1),
            "torque_kft_lb": round(15.2 + (session.current_depth_md_m % 3) * 0.9, 1),
            "spp_psi": round(2850.0 + (session.current_depth_md_m % 10) * 15.0, 0),
            "mud_weight_sg": 1.28
        }

        # Look-Ahead Evaluation: Scan eligible prior offset events within lookahead window
        # Lookahead horizon: bit_tvdss_m to bit_tvdss_m + lookahead_window_m
        target_tvdss_max = bit_station.tvdss_m + lookahead_window_m

        # Prior verified offset events
        prior_events = db.query(models.DrillingEvent).filter(
            models.DrillingEvent.well_id.in_(eligible_offset_ids),
            models.DrillingEvent.depth_tvdss_m >= bit_station.tvdss_m,
            models.DrillingEvent.depth_tvdss_m <= target_tvdss_max,
            models.DrillingEvent.verification_status.in_(["VERIFIED", "ORIGINAL_VERIFIED"])
        ).all()

        advisories = []
        for e in prior_events:
            lead_dist = round(e.depth_tvdss_m - bit_station.tvdss_m, 1)
            adv = {
                "risk_category": e.event_type,
                "severity": e.severity,
                "lead_distance_m": lead_dist,
                "target_strata": e.formation_name,
                "offset_source_well": e.well_id,
                "historical_narrative": e.operational_narrative,
                "mitigation": e.mitigation_applied,
                "source_citation": e.source_citation,
                "verification_status": e.verification_status,
                "doc_id": e.doc_id or "DOC-VOLVE-DDR"
            }
            advisories.append(adv)

        # Ground-Truth check on active well at current depth
        active_events = db.query(models.DrillingEvent).filter(
            models.DrillingEvent.well_id == session.well_id,
            models.DrillingEvent.depth_md_m >= session.current_depth_md_m - 5.0,
            models.DrillingEvent.depth_md_m <= session.current_depth_md_m + 5.0
        ).all()

        ground_truth_alert = None
        if active_events:
            evt = active_events[0]
            ground_truth_alert = {
                "event_id": evt.event_id,
                "event_type": evt.event_type,
                "severity": evt.severity,
                "depth_md_m": evt.depth_md_m,
                "depth_tvdss_m": evt.depth_tvdss_m,
                "narrative": evt.operational_narrative,
                "mitigation": evt.mitigation_applied,
                "status": "INCIDENT_OCCURRED_AT_CURRENT_DEPTH"
            }

        return {
            "session_id": session.session_id,
            "well_id": session.well_id,
            "well_name": well.well_name,
            "status": session.status,
            "progress_pct": round((session.current_depth_md_m - session.start_depth_md_m) / 
                                  (session.end_depth_md_m - session.start_depth_md_m) * 100.0, 1),
            "telemetry": telemetry,
            "firewall_active": True,
            "eligible_prior_offsets": eligible_offset_ids,
            "advisories_count": len(advisories),
            "active_advisories": advisories,
            "ground_truth_alert": ground_truth_alert,
            "lookahead_window_m": lookahead_window_m
        }

    @classmethod
    def step_session(
        cls,
        db: Session,
        session_id: str,
        step_md_m: float = 10.0,
        lookahead_window_m: float = 100.0
    ) -> Dict[str, Any]:
        session = db.query(models.ReplaySession).filter(models.ReplaySession.session_id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        new_depth = min(session.end_depth_md_m, session.current_depth_md_m + step_md_m)
        session.current_depth_md_m = new_depth
        if session.current_depth_md_m >= session.end_depth_md_m:
            session.status = "COMPLETED"
        else:
            session.status = "PLAYING"

        db.commit()
        return cls.get_session_state(db, session_id, lookahead_window_m=lookahead_window_m)

    @classmethod
    def jump_to_incident(
        cls,
        db: Session,
        session_id: str,
        lookahead_window_m: float = 100.0
    ) -> Dict[str, Any]:
        """
        Jumps replay progression to 50 meters prior to the first documented incident in active well.
        """
        session = db.query(models.ReplaySession).filter(models.ReplaySession.session_id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found.")

        # Find first documented incident in active well with valid non-zero depth within or ahead of section
        first_evt = db.query(models.DrillingEvent).filter(
            models.DrillingEvent.well_id == session.well_id,
            models.DrillingEvent.depth_md_m >= session.start_depth_md_m,
            models.DrillingEvent.depth_md_m > 0.0
        ).order_by(models.DrillingEvent.depth_md_m.asc()).first()

        if not first_evt:
            first_evt = db.query(models.DrillingEvent).filter(
                models.DrillingEvent.well_id == session.well_id,
                models.DrillingEvent.depth_md_m > 500.0
            ).order_by(models.DrillingEvent.depth_md_m.asc()).first()

        if first_evt:
            # Jump to 50m before incident or directly to start of incident zone
            session.current_depth_md_m = max(session.start_depth_md_m, first_evt.depth_md_m - 50.0)
            session.status = "PAUSED"
            db.commit()

        return cls.get_session_state(db, session_id, lookahead_window_m=lookahead_window_m)
