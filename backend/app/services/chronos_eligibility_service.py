"""
NWIS CHRONOS — REPLAY-ELIGIBILITY REGISTRY SERVICE
Determines operational back-testing suitability tiers for historical wellbores:
- FULL_TIME_INDEXED (High-frequency WITSML stream available)
- DEPTH_INDEXED (Definitive directional surveys & continuous telemetry packets)
- DAILY_REPORT_RECONSTRUCTION (DDR shift-level operational progression)
- RETROSPECTIVE_ONLY (Pioneer well with zero prior offsets, or missing surveys)
- INSUFFICIENT_DATA (Missing datums or unverified formation picks)
"""

from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.db import models

class ChronosEligibilityService:
    """
    Evaluates wellbore telemetry coverage, directional survey quality, and prior analogue availability
    to categorize replay eligibility and prevent artificial precision.
    """

    @classmethod
    def evaluate_well_eligibility(cls, db: Session, well_id: str) -> Dict[str, Any]:
        well = db.query(models.Well).filter(models.Well.well_id == well_id).first()
        if not well:
            raise ValueError(f"Well {well_id} not found in registry.")

        surveys = db.query(models.WellboreSurvey).filter(models.WellboreSurvey.well_id == well_id).all()
        tops = db.query(models.FormationTop).filter(models.FormationTop.well_id == well_id).all()
        events = db.query(models.DrillingEvent).filter(models.DrillingEvent.well_id == well_id).all()

        has_drilling_dates = bool(well.spud_date and well.completion_date)
        has_verified_events = len(events) > 0
        has_definitive_survey = len(surveys) >= 4
        has_formation_tops = len(tops) >= 3

        # Count strictly prior offset wells
        prior_wells = []
        if well.spud_date:
            prior_wells = db.query(models.Well).filter(
                models.Well.well_id != well_id,
                models.Well.spud_date < well.spud_date
            ).all()

        has_prior_offsets = len(prior_wells) > 0

        # Tier Evaluation
        if not has_drilling_dates or not has_formation_tops:
            tier = "INSUFFICIENT_DATA"
            exclusion_reason = "Missing certified spud/completion timestamps or formation picks."
        elif not has_prior_offsets:
            tier = "RETROSPECTIVE_ONLY"
            exclusion_reason = f"Pioneer wellbore ({well.spud_date}); zero prior offset wells existed in field at time of spud."
        elif has_definitive_survey and has_formation_tops and has_prior_offsets:
            tier = "DEPTH_INDEXED"
            exclusion_reason = None
        else:
            tier = "DAILY_REPORT_RECONSTRUCTION"
            exclusion_reason = "Limited survey resolution; suitable for shift-level reconstruction only."

        # Notes
        notes = (
            f"Evaluated with {len(surveys)} survey stations, {len(tops)} formation tops, "
            f"and {len(prior_wells)} chronologically eligible prior offset wellbores."
        )

        # Upsert into ReplayEligibility table
        eligibility = db.query(models.ReplayEligibility).filter(models.ReplayEligibility.well_id == well_id).first()
        if not eligibility:
            eligibility = models.ReplayEligibility(
                well_id=well_id,
                eligibility_tier=tier,
                has_drilling_dates=has_drilling_dates,
                has_verified_events=has_verified_events,
                has_definitive_survey=has_definitive_survey,
                has_formation_tops=has_formation_tops,
                has_prior_offsets=has_prior_offsets,
                exclusion_reason=exclusion_reason,
                evaluation_notes=notes
            )
            db.add(eligibility)
        else:
            eligibility.eligibility_tier = tier
            eligibility.has_drilling_dates = has_drilling_dates
            eligibility.has_verified_events = has_verified_events
            eligibility.has_definitive_survey = has_definitive_survey
            eligibility.has_formation_tops = has_formation_tops
            eligibility.has_prior_offsets = has_prior_offsets
            eligibility.exclusion_reason = exclusion_reason
            eligibility.evaluation_notes = notes

        db.commit()

        return {
            "well_id": well.well_id,
            "well_name": well.well_name,
            "eligibility_tier": tier,
            "spud_date": well.spud_date,
            "completion_date": well.completion_date,
            "criteria": {
                "has_drilling_dates": has_drilling_dates,
                "has_verified_events": has_verified_events,
                "has_definitive_survey": has_definitive_survey,
                "has_formation_tops": has_formation_tops,
                "has_prior_offsets": has_prior_offsets,
                "prior_offsets_count": len(prior_wells),
                "prior_offset_ids": [p.well_id for p in prior_wells]
            },
            "exclusion_reason": exclusion_reason,
            "evaluation_notes": notes
        }

    @classmethod
    def list_all_eligibility(cls, db: Session) -> List[Dict[str, Any]]:
        wells = db.query(models.Well).all()
        return [cls.evaluate_well_eligibility(db, w.well_id) for w in wells]
