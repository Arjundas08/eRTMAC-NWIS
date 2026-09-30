from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid
from ..db.models import DrillingEvent, LookaheadAlert, FormationTop
from ..schemas.lookahead_schemas import (
    LookaheadRequest, LookaheadResponse, LookaheadAlertItem, DrillerFeedbackRequest
)

class RiskService:
    def evaluate_lookahead_horizon(
        self,
        db: Session,
        request: LookaheadRequest
    ) -> LookaheadResponse:
        """
        Scans upcoming depth window for historical offset incidents.
        Enforces:
        1. Geological datum sanity checks (MD >= TVD).
        2. Strict chronological cutoff (event_timestamp < as_of_timestamp).
        3. Evidence-or-Silence invariant.
        """
        active_well_id = request.active_well_id
        current_md = request.current_bit_depth_md_m
        current_tvdss = request.current_bit_depth_tvdss_m
        target_formation = request.active_formation
        horizon_window = request.lookahead_window_m
        as_of_ts = request.as_of_timestamp

        # Geological sanity check: MD cannot be less than TVD/TVDSS
        if current_md < current_tvdss:
            return LookaheadResponse(
                active_well_id=active_well_id,
                current_bit_tvdss_m=current_tvdss,
                active_formation=target_formation,
                lookahead_window_m=horizon_window,
                hazard_level="CLEAR",
                alert_count=0,
                alerts=[],
                telemetry_anomaly_flag=False,
                evidence_status="INSUFFICIENT_GEOLOGICAL_EVIDENCE",
                evaluation_cutoff_timestamp=as_of_ts
            )

        # Target interval in TVDSS
        horizon_top = current_tvdss
        horizon_base = current_tvdss + horizon_window

        # Query offset events within the upcoming depth interval
        # Exclude active well itself (zero data leakage)
        # Enforce that only VERIFIED records enter trusted risk intelligence (block REJECTED/PENDING)
        query = db.query(DrillingEvent).filter(
            DrillingEvent.well_id != active_well_id,
            DrillingEvent.depth_tvdss_m >= horizon_top,
            DrillingEvent.depth_tvdss_m <= horizon_base,
            DrillingEvent.verification_status == "VERIFIED"
        )

        # Apply strict chronological cutoff if specified
        if as_of_ts:
            query = query.filter(DrillingEvent.event_timestamp < as_of_ts)

        candidate_events = query.all()

        # Also search by matching formation name within the same temporal boundary
        fm_query = db.query(DrillingEvent).filter(
            DrillingEvent.well_id != active_well_id,
            DrillingEvent.formation_name == target_formation,
            DrillingEvent.verification_status == "VERIFIED"
        )
        if as_of_ts:
            fm_query = fm_query.filter(DrillingEvent.event_timestamp < as_of_ts)

        formation_events = fm_query.all()

        # Combine and deduplicate
        all_relevant_events = {}
        for ev in candidate_events + formation_events:
            lead_dist = round(ev.depth_tvdss_m - current_tvdss, 1)
            # Must be ahead of bit, within horizon window
            if 0.0 < lead_dist <= horizon_window:
                all_relevant_events[ev.event_id] = (ev, lead_dist)

        alerts: List[LookaheadAlertItem] = []
        highest_risk_score = 0.0

        # Check real-time telemetry anomalies if provided
        telemetry_anomaly = False
        if request.recent_telemetry:
            tel = request.recent_telemetry
            # Anomaly rules:
            # 1. Torque spike > 18 kft-lbs
            # 2. Standpipe pressure spike > 3400 psi
            # 3. Flow out vs Flow in discrepancy
            if tel.torque_kftlbs and tel.torque_kftlbs > 18.0:
                telemetry_anomaly = True
            if tel.spp_psi and tel.spp_psi > 3400:
                telemetry_anomaly = True
            if tel.flow_in_gpm and tel.flow_out_pct and tel.flow_out_pct < 85.0:
                telemetry_anomaly = True

        for event_id, (ev, lead_dist) in all_relevant_events.items():
            # Calculate baseline risk score based on severity and proximity
            base_score = 0.65
            if ev.severity == "CRITICAL":
                base_score = 0.90
            elif ev.severity == "SEVERE":
                base_score = 0.80
            elif ev.severity == "MODERATE":
                base_score = 0.65

            # Closer lead distance increases urgency
            proximity_multiplier = max(0.85, 1.0 - (lead_dist / (horizon_window * 2.0)))
            computed_score = round(min(0.98, base_score * proximity_multiplier), 3)

            # Elevate if real-time telemetry already shows symptoms
            if telemetry_anomaly:
                computed_score = min(0.99, computed_score + 0.10)

            if computed_score > highest_risk_score:
                highest_risk_score = computed_score

            mitigation_text = ev.mitigation_applied or "Follow standard field procedure for mitigation."

            alert_item = LookaheadAlertItem(
                hazard_type=ev.event_type,
                severity=ev.severity,
                projected_tvdss_m=ev.depth_tvdss_m,
                lead_distance_m=lead_dist,
                source_offset_well=ev.well_id,
                source_citation=ev.source_citation,
                historical_narrative=ev.operational_narrative,
                recommended_mitigation=mitigation_text,
                risk_score=computed_score
            )
            alerts.append(alert_item)

            # Persist alert record into database
            db_alert = LookaheadAlert(
                alert_id=str(uuid.uuid4()),
                active_well_id=active_well_id,
                current_bit_tvdss_m=current_tvdss,
                target_formation=target_formation,
                horizon_window_m=horizon_window,
                hazard_predicted=ev.event_type,
                risk_score=computed_score,
                matched_event_id=ev.event_id,
                recommended_mitigation=mitigation_text,
                evidence_citation=ev.source_citation
            )
            db.add(db_alert)

        db.commit()

        # Sort alerts by risk score descending
        alerts.sort(key=lambda x: x.risk_score, reverse=True)

        # Determine overall hazard level
        if not alerts:
            hazard_level = "CLEAR"
            evidence_status = "NO_HISTORICAL_PRECEDENT"
        elif highest_risk_score >= 0.85:
            hazard_level = "CRITICAL"
            evidence_status = "VERIFIED_OFFSET_EVIDENCE"
        elif highest_risk_score >= 0.70:
            hazard_level = "WARNING"
            evidence_status = "VERIFIED_OFFSET_EVIDENCE"
        else:
            hazard_level = "ADVISORY"
            evidence_status = "VERIFIED_OFFSET_EVIDENCE"

        return LookaheadResponse(
            active_well_id=active_well_id,
            current_bit_tvdss_m=current_tvdss,
            active_formation=target_formation,
            lookahead_window_m=horizon_window,
            hazard_level=hazard_level,
            alert_count=len(alerts),
            alerts=alerts,
            telemetry_anomaly_flag=telemetry_anomaly,
            evidence_status=evidence_status,
            evaluation_cutoff_timestamp=as_of_ts
        )

    def record_driller_feedback(
        self,
        db: Session,
        feedback: DrillerFeedbackRequest
    ) -> Dict[str, Any]:
        """
        Records human-in-the-loop driller feedback to close the operational learning loop.
        """
        alert = db.query(LookaheadAlert).filter(LookaheadAlert.alert_id == feedback.alert_id).first()
        if not alert:
            # Also search by matched event or recent alert
            alert = db.query(LookaheadAlert).order_by(LookaheadAlert.created_at.desc()).first()

        if alert:
            alert.driller_response = feedback.driller_response
            alert.driller_comments = feedback.driller_comments
            alert.response_timestamp = datetime.now(timezone.utc)
            db.commit()
            return {
                "status": "success",
                "alert_id": alert.alert_id,
                "recorded_response": feedback.driller_response,
                "timestamp": alert.response_timestamp.isoformat()
            }
        else:
            return {"status": "error", "message": "No matching alert found to update."}

risk_service = RiskService()
