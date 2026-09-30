import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..db.models import Well, FormationTop, WellboreSurvey, DrillingEvent
from .stratigraphic_service import stratigraphic_service
from ..schemas.similarity_schemas import RankedOffsetWell, SimilarityExplanation

class SimilarityService:
    def rank_offset_wells(
        self,
        db: Session,
        active_well_id: str,
        target_formation: str,
        current_depth_tvdss: float,
        search_radius_km: float = 5.0
    ) -> List[RankedOffsetWell]:
        """
        Computes explainable multi-criteria similarity for all offset wells within the radius.
        """
        active_well = db.query(Well).filter(Well.well_id == active_well_id).first()
        if not active_well:
            raise ValueError(f"Active well {active_well_id} not found in database.")

        # Find all other candidate wells in the database
        candidate_wells = db.query(Well).filter(Well.well_id != active_well_id).all()
        ranked_results = []

        # Find active formation top in active well if available
        active_top = db.query(FormationTop).filter(
            FormationTop.well_id == active_well_id,
            FormationTop.formation_name == target_formation
        ).first()
        active_top_tvdss = active_top.top_tvdss_m if active_top else current_depth_tvdss

        for offset in candidate_wells:
            # 1. Geospatial Distance Score (S_geo)
            dist_km = stratigraphic_service.haversine_distance_km(
                active_well.latitude, active_well.longitude,
                offset.latitude, offset.longitude
            )
            if dist_km > search_radius_km:
                continue # Outside selected radius

            s_geo = max(0.0, 1.0 - (dist_km / search_radius_km))

            # 2. Stratigraphic Match Score (S_strat)
            offset_top = db.query(FormationTop).filter(
                FormationTop.well_id == offset.well_id,
                FormationTop.formation_name == target_formation
            ).first()

            strat_match = offset_top is not None
            if strat_match:
                # Delta between formation top depths (structural dip check)
                top_delta = abs(offset_top.top_tvdss_m - active_top_tvdss)
                s_strat = max(0.0, 1.0 - (top_delta / 100.0)) # 100m delta tolerance
            else:
                top_delta = 999.0
                s_strat = 0.2

            # 3. Trajectory Profile Similarity (S_traj)
            # Compare inclination at target depth
            offset_survey = db.query(WellboreSurvey).filter(
                WellboreSurvey.well_id == offset.well_id,
                WellboreSurvey.tvdss_m >= current_depth_tvdss - 150.0
            ).order_by(WellboreSurvey.tvdss_m.asc()).first()

            incl_diff = abs(offset_survey.inclination_deg - 30.0) if offset_survey else 15.0
            s_traj = max(0.0, 1.0 - (incl_diff / 45.0))

            # 4. Historical Event Density (S_event)
            events = db.query(DrillingEvent).filter(
                DrillingEvent.well_id == offset.well_id,
                DrillingEvent.formation_name == target_formation
            ).all()
            event_count = len(events)
            s_event = min(1.0, 0.4 + (0.3 * event_count)) if event_count > 0 else 0.3

            # 5. Composite Multi-Criteria Similarity
            # Weights: Geo=0.20, Strat=0.35, Traj=0.15, Event=0.30
            composite_score = round(
                (0.20 * s_geo) + (0.35 * s_strat) + (0.15 * s_traj) + (0.30 * s_event),
                3
            )

            # Generate plain-English explainability reasons
            reasons = []
            if dist_km <= 2.0:
                reasons.append(f"Immediate proximity ({dist_km:.2f} km from active well)")
            else:
                reasons.append(f"Located {dist_km:.2f} km away in same block")

            if strat_match:
                reasons.append(f"Penetrated matching {target_formation} (top delta: {top_delta:.1f}m TVDSS)")
            else:
                reasons.append(f"Unconfirmed {target_formation} pick in offset record")

            if event_count > 0:
                reasons.append(f"Encountered {event_count} documented operational incidents in {target_formation}")

            # Confidence level
            if composite_score >= 0.80:
                confidence = "HIGH"
            elif composite_score >= 0.60:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"

            events_summary = [
                {
                    "event_type": ev.event_type,
                    "severity": ev.severity,
                    "depth_tvdss_m": ev.depth_tvdss_m,
                    "npt_hours": ev.npt_hours,
                    "citation": ev.source_citation
                }
                for ev in events
            ]

            ranked_results.append(RankedOffsetWell(
                offset_well_id=offset.well_id,
                well_name=offset.well_name,
                composite_similarity_score=composite_score,
                rank=0, # Will assign after sorting
                confidence_level=confidence,
                explanation=SimilarityExplanation(
                    geospatial_distance_km=dist_km,
                    stratigraphic_match=strat_match,
                    formation_top_delta_m=top_delta if strat_match else -1.0,
                    trajectory_deviation_diff_deg=round(incl_diff, 1),
                    historical_event_count=event_count,
                    primary_reasons=reasons
                ),
                relevant_events_summary=events_summary
            ))

        # Sort descending by composite score
        ranked_results.sort(key=lambda x: x.composite_similarity_score, reverse=True)
        for i, item in enumerate(ranked_results):
            item.rank = i + 1

        return ranked_results

similarity_service = SimilarityService()
