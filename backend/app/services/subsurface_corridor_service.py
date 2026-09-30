"""
NWIS GEOCORE — SUBSURFACE CORRIDOR SERVICE
Calculates 3D spatial relationships and proximity corridors between wellbore trajectories
using actual directional survey geometry (Minimum Curvature), not surface coordinates alone.
Includes explicit safety disclaimers and historical incident positioning.
"""

import math
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.db import models
from backend.app.services.trajectory_engine import TrajectoryEngine, SurveyStationData

SAFETY_DISCLAIMER = (
    "ENGINEERING & SAFETY ADVISORY: The GeoCore Subsurface Corridor is an informational geological "
    "correlation, proximity screening, and analogue visualization tool. It does NOT replace certified "
    "wellbore anti-collision analysis, gyro multi-station validation, or ISCWSA directional drilling safety clearance protocols."
)

class SubsurfaceCorridorService:
    """
    Computes 3D subsurface trajectory corridors and projects geological formations
    and historical drilling incidents onto the spatial volume.
    """

    @classmethod
    def generate_corridor(
        cls,
        db: Session,
        primary_well_id: str,
        offset_well_ids: Optional[List[str]] = None,
        max_corridor_radius_m: float = 6000.0
    ) -> Dict[str, Any]:
        primary_well = db.query(models.Well).filter(models.Well.well_id == primary_well_id).first()
        if not primary_well:
            raise ValueError(f"Primary well {primary_well_id} not found.")

        # Determine eligible offsets
        if not offset_well_ids:
            all_wells = db.query(models.Well).filter(models.Well.well_id != primary_well_id).all()
            offset_well_ids = [w.well_id for w in all_wells]

        # Compute Primary Well Trajectory
        primary_surveys = db.query(models.WellboreSurvey).filter(
            models.WellboreSurvey.well_id == primary_well_id
        ).order_by(models.WellboreSurvey.md_m.asc()).all()

        raw_primary = [
            {"md_m": s.md_m, "inclination_deg": s.inclination_deg, "azimuth_deg": s.azimuth_deg}
            for s in primary_surveys
        ]
        primary_traj = TrajectoryEngine.compute_trajectory(
            raw_primary,
            primary_well.kb_elevation_m,
            surface_northing=0.0,
            surface_easting=0.0
        ) if raw_primary else []

        # Convert primary trajectory to dictionary format
        primary_points = [st.to_dict() for st in primary_traj]

        # Primary Formation Picks
        primary_formations = db.query(models.FormationTop).filter(
            models.FormationTop.well_id == primary_well_id
        ).order_by(models.FormationTop.top_tvdss_m.asc()).all()

        fmt_boundaries = [
            {
                "formation_name": f.formation_name,
                "top_tvdss_m": f.top_tvdss_m,
                "base_tvdss_m": f.base_tvdss_m,
                "lithology": f.lithology_primary
            }
            for f in primary_formations
        ]

        # Process each offset well
        offset_trajectories = []
        all_incident_markers = []

        # Coordinate origin: primary well surface location
        lat0 = primary_well.latitude
        lon0 = primary_well.longitude

        for off_id in offset_well_ids:
            off_well = db.query(models.Well).filter(models.Well.well_id == off_id).first()
            if not off_well:
                continue

            # Calculate surface displacement in meters (local tangent plane approximation)
            dlat_m = (off_well.latitude - lat0) * 111139.0
            dlon_m = (off_well.longitude - lon0) * 111139.0 * math.cos(math.radians(lat0))
            surface_dist_m = math.hypot(dlat_m, dlon_m)

            if surface_dist_m > max_corridor_radius_m:
                continue

            # Directional surveys
            off_surveys = db.query(models.WellboreSurvey).filter(
                models.WellboreSurvey.well_id == off_id
            ).order_by(models.WellboreSurvey.md_m.asc()).all()

            raw_off = [
                {"md_m": s.md_m, "inclination_deg": s.inclination_deg, "azimuth_deg": s.azimuth_deg}
                for s in off_surveys
            ]

            if raw_off:
                off_traj = TrajectoryEngine.compute_trajectory(
                    raw_off,
                    off_well.kb_elevation_m,
                    surface_northing=dlat_m,
                    surface_easting=dlon_m
                )
                off_points = [st.to_dict() for st in off_traj]
            else:
                off_points = []

            # Subsurface 3D minimum distance to primary well
            min_subsurface_dist_m = surface_dist_m
            for pst in primary_traj:
                for ost in (off_traj if raw_off else []):
                    # Check stations at roughly comparable TVDSS
                    if abs(pst.tvdss_m - ost.tvdss_m) < 150.0:
                        dist3d = math.sqrt(
                            (pst.northing_m - ost.northing_m)**2 +
                            (pst.easting_m - ost.easting_m)**2 +
                            (pst.tvdss_m - ost.tvdss_m)**2
                        )
                        if dist3d < min_subsurface_dist_m:
                            min_subsurface_dist_m = dist3d

            # Fetch historical events for this offset well
            off_events = db.query(models.DrillingEvent).filter(
                models.DrillingEvent.well_id == off_id
            ).all()

            for evt in off_events:
                # Interpolate 3D position of event in offset well
                evt_north = dlat_m
                evt_east = dlon_m
                if raw_off and off_traj:
                    try:
                        interp_evt = TrajectoryEngine.interpolate_at_md(off_traj, evt.depth_md_m, off_well.kb_elevation_m)
                        evt_north = interp_evt.northing_m
                        evt_east = interp_evt.easting_m
                    except Exception:
                        pass

                all_incident_markers.append({
                    "event_id": evt.event_id,
                    "well_id": off_id,
                    "event_type": evt.event_type,
                    "severity": evt.severity,
                    "depth_md_m": evt.depth_md_m,
                    "depth_tvdss_m": evt.depth_tvdss_m,
                    "formation_name": evt.formation_name,
                    "subsurface_coords": {
                        "northing_m": round(evt_north, 1),
                        "easting_m": round(evt_east, 1),
                        "tvdss_m": evt.depth_tvdss_m
                    },
                    "narrative": evt.operational_narrative,
                    "mitigation": evt.mitigation_applied,
                    "source_citation": evt.source_citation,
                    "verification_status": evt.verification_status,
                    "doc_id": evt.doc_id
                })

            offset_trajectories.append({
                "well_id": off_id,
                "well_name": off_well.well_name,
                "surface_distance_m": round(surface_dist_m, 1),
                "min_subsurface_distance_m": round(min_subsurface_dist_m, 1),
                "survey_station_count": len(off_points),
                "trajectory_points": off_points,
                "historical_events_count": len(off_events)
            })

        return {
            "primary_well": {
                "well_id": primary_well.well_id,
                "well_name": primary_well.well_name,
                "kb_elevation_m": primary_well.kb_elevation_m,
                "total_depth_md_m": primary_well.total_depth_md_m,
                "total_depth_tvd_m": primary_well.total_depth_tvd_m,
                "trajectory_points": primary_points
            },
            "formation_horizons": fmt_boundaries,
            "corridor_offsets": sorted(offset_trajectories, key=lambda o: o["min_subsurface_distance_m"]),
            "pinned_incident_markers": all_incident_markers,
            "safety_advisory": SAFETY_DISCLAIMER
        }
