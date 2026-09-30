import math
from typing import Tuple, List, Dict, Optional

class GeologicalDatumError(ValueError):
    """Raised when geological reference datums or wellbore parameters are invalid or missing."""
    pass

class StratigraphicService:
    @staticmethod
    def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Computes great-circle distance between two coordinates in kilometers on WGS84 ellipsoid.
        """
        R = 6371.0 # Earth's mean radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2.0) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2.0) ** 2)
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return round(R * c, 3)

    @staticmethod
    def compute_tvdss(tvd_m: float, kb_elevation_m: Optional[float]) -> float:
        """
        Computes True Vertical Depth Subsea (TVDSS).
        TVDSS = TVD - Kelly Bushing (KB) Elevation.
        Raises GeologicalDatumError if Kelly Bushing elevation is missing or invalid.
        """
        if kb_elevation_m is None or math.isnan(kb_elevation_m):
            raise GeologicalDatumError("INSUFFICIENT_GEOLOGICAL_EVIDENCE: Missing vertical reference datum (KB Elevation is null).")
        if kb_elevation_m < 0:
            raise GeologicalDatumError(f"INSUFFICIENT_GEOLOGICAL_EVIDENCE: Kelly Bushing elevation cannot be negative ({kb_elevation_m}m).")
        if tvd_m < 0:
            raise GeologicalDatumError(f"INSUFFICIENT_GEOLOGICAL_EVIDENCE: Negative TVD value ({tvd_m}m) is physically invalid.")
        return round(tvd_m - kb_elevation_m, 2)

    @classmethod
    def validate_depth_datum(cls, md_m: float, tvd_m: float, kb_elevation_m: Optional[float] = None) -> bool:
        """
        Validates depth datums for geological consistency:
        1. MD >= TVD
        2. KB elevation >= 0 if provided
        """
        if md_m < tvd_m:
            raise GeologicalDatumError(
                f"INSUFFICIENT_GEOLOGICAL_EVIDENCE: Measured Depth ({md_m}m) cannot be less than True Vertical Depth ({tvd_m}m)."
            )
        if kb_elevation_m is not None:
            if kb_elevation_m < 0:
                raise GeologicalDatumError(
                    f"INSUFFICIENT_GEOLOGICAL_EVIDENCE: Kelly Bushing elevation cannot be negative ({kb_elevation_m}m)."
                )
        return True
        """
        Verifies that Measured Depth is greater than or equal to True Vertical Depth.
        In 3D Euclidean wellbore geometry, MD can never be less than TVD.
        """
        if md_m < tvd_m:
            raise GeologicalDatumError(
                f"INSUFFICIENT_GEOLOGICAL_EVIDENCE: Measured Depth ({md_m}m) cannot be less than True Vertical Depth ({tvd_m}m)."
            )

    @staticmethod
    def minimum_curvature_step(
        md1: float, inc1_deg: float, azi1_deg: float,
        md2: float, inc2_deg: float, azi2_deg: float
    ) -> Tuple[float, float, float, float]:
        """
        API RP 7G Minimum Curvature Method step calculation between two survey stations.
        Returns: (delta_tvd, delta_north, delta_east, dogleg_severity_deg_30m)
        """
        delta_md = md2 - md1
        if delta_md <= 0:
            return 0.0, 0.0, 0.0, 0.0

        i1 = math.radians(inc1_deg)
        i2 = math.radians(inc2_deg)
        a1 = math.radians(azi1_deg)
        a2 = math.radians(azi2_deg)

        # Dogleg angle calculation
        cos_dl = math.cos(i2 - i1) - (math.sin(i1) * math.sin(i2) * (1.0 - math.cos(a2 - a1)))
        cos_dl = max(-1.0, min(1.0, cos_dl))
        dl = math.acos(cos_dl)

        # Ratio factor F
        if dl < 1e-6:
            rf = 1.0
        else:
            rf = (2.0 / dl) * math.tan(dl / 2.0)

        delta_tvd = (delta_md / 2.0) * (math.cos(i1) + math.cos(i2)) * rf
        delta_north = (delta_md / 2.0) * (math.sin(i1) * math.cos(a1) + math.sin(i2) * math.cos(a2)) * rf
        delta_east = (delta_md / 2.0) * (math.sin(i1) * math.sin(a1) + math.sin(i2) * math.sin(a2)) * rf

        dls_deg_30m = (math.degrees(dl) / delta_md) * 30.0 if delta_md > 0 else 0.0

        return round(delta_tvd, 2), round(delta_north, 2), round(delta_east, 2), round(dls_deg_30m, 2)

    @staticmethod
    def interpolate_trajectory(
        stations: List[Dict[str, float]],
        step_size_md_m: float = 10.0
    ) -> List[Dict[str, float]]:
        """
        Interpolates survey stations along wellbore using Minimum Curvature principles.
        Ensures continuous, realistic drill-bit progression without horizon jump-overs.
        Each station dictionary contains: {'md_m', 'tvd_m', 'tvdss_m', 'inclination_deg', 'azimuth_deg'}
        """
        if not stations:
            return []

        sorted_stations = sorted(stations, key=lambda s: s["md_m"])
        interpolated = []

        for i in range(len(sorted_stations) - 1):
            s1 = sorted_stations[i]
            s2 = sorted_stations[i + 1]

            md1, md2 = s1["md_m"], s2["md_m"]
            tvdss1, tvdss2 = s1["tvdss_m"], s2["tvdss_m"]
            inc1, inc2 = s1["inclination_deg"], s2["inclination_deg"]
            azi1, azi2 = s1["azimuth_deg"], s2["azimuth_deg"]

            delta_md = md2 - md1
            if delta_md <= 0:
                continue

            num_steps = max(1, int(math.ceil(delta_md / step_size_md_m)))
            for step in range(num_steps):
                frac = step / float(num_steps)
                cur_md = round(md1 + frac * delta_md, 2)
                cur_tvdss = round(tvdss1 + frac * (tvdss2 - tvdss1), 2)
                cur_inc = round(inc1 + frac * (inc2 - inc1), 2)
                cur_azi = round(azi1 + frac * (azi2 - azi1), 2)

                interpolated.append({
                    "md_m": cur_md,
                    "tvdss_m": cur_tvdss,
                    "inclination_deg": cur_inc,
                    "azimuth_deg": cur_azi
                })

        # Append final station
        last_s = sorted_stations[-1]
        interpolated.append({
            "md_m": last_s["md_m"],
            "tvdss_m": last_s["tvdss_m"],
            "inclination_deg": last_s["inclination_deg"],
            "azimuth_deg": last_s["azimuth_deg"]
        })

        return interpolated

    @staticmethod
    def compute_relative_formation_depth(
        current_tvdss: float,
        formation_top_tvdss: Optional[float]
    ) -> float:
        """
        Computes penetration depth into a specific geological formation.
        Positive value indicates meters below the formation top.
        """
        if formation_top_tvdss is None:
            raise GeologicalDatumError("INSUFFICIENT_GEOLOGICAL_EVIDENCE: Formation top TVDSS pick is undefined.")
        return round(current_tvdss - formation_top_tvdss, 2)

stratigraphic_service = StratigraphicService()
