"""
NWIS GEOCORE — INDUSTRIAL DEPTH & TRAJECTORY ENGINE
Deterministic directional survey calculations, Minimum Curvature algorithm,
strict Kelly Bushing (KB) datum normalization, and controlled evidence-abstention.
"""

import math
from typing import List, Dict, Any, Optional, Tuple

class InsufficientGeologicalEvidenceError(ValueError):
    """Raised when critical survey or datum metadata is missing, preventing safe depth conversion."""
    pass

class IncompatibleDatumError(ValueError):
    """Raised when depth reference datums cannot be reconciled without physical error."""
    pass

class SurveyStationData:
    def __init__(
        self,
        md_m: float,
        inclination_deg: float,
        azimuth_deg: float,
        tvd_m: Optional[float] = None,
        tvdss_m: Optional[float] = None,
        northing_m: float = 0.0,
        easting_m: float = 0.0,
        dogleg_severity: float = 0.0,
        is_interpolated: bool = False
    ):
        self.md_m = float(md_m)
        self.inclination_deg = float(inclination_deg)
        self.azimuth_deg = float(azimuth_deg)
        self.tvd_m = float(tvd_m) if tvd_m is not None else None
        self.tvdss_m = float(tvdss_m) if tvdss_m is not None else None
        self.northing_m = float(northing_m)
        self.easting_m = float(easting_m)
        self.dogleg_severity = float(dogleg_severity)
        self.is_interpolated = bool(is_interpolated)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "md_m": round(self.md_m, 2),
            "inclination_deg": round(self.inclination_deg, 2),
            "azimuth_deg": round(self.azimuth_deg, 2),
            "tvd_m": round(self.tvd_m, 2) if self.tvd_m is not None else None,
            "tvdss_m": round(self.tvdss_m, 2) if self.tvdss_m is not None else None,
            "northing_m": round(self.northing_m, 2),
            "easting_m": round(self.easting_m, 2),
            "dogleg_severity_deg_30m": round(self.dogleg_severity, 3),
            "is_interpolated": self.is_interpolated
        }


class TrajectoryEngine:
    """
    Subsurface trajectory computation engine using the industry-standard
    Minimum Curvature Method (SPE 8424 / API RP 78).
    """

    @staticmethod
    def validate_datum(kb_elevation_m: Optional[float]) -> float:
        """
        Validates that a verified Kelly Bushing (KB) elevation is provided.
        Never substitutes missing datum values with zero.
        """
        if kb_elevation_m is None or not isinstance(kb_elevation_m, (int, float)):
            raise InsufficientGeologicalEvidenceError(
                "INSUFFICIENT_GEOLOGICAL_EVIDENCE: Kelly Bushing (KB) reference datum is missing. "
                "TVDSS cannot be computed without a certified elevation reference."
            )
        if kb_elevation_m < 0 or kb_elevation_m > 200:
            raise IncompatibleDatumError(
                f"INSUFFICIENT_GEOLOGICAL_EVIDENCE: KB elevation {kb_elevation_m}m is outside credible offshore jackup range (5m - 100m)."
            )
        return float(kb_elevation_m)

    @staticmethod
    def compute_tvdss(tvd_m: float, kb_elevation_m: Optional[float]) -> float:
        """
        Computes True Vertical Depth Subsea (TVDSS).
        Convention: TVDSS = TVD (RKB) - KB_elevation
        Zero elevation substitution is strictly prohibited.
        """
        valid_kb = TrajectoryEngine.validate_datum(kb_elevation_m)
        return round(tvd_m - valid_kb, 2)

    @staticmethod
    def minimum_curvature_step(
        md1: float, inc1_deg: float, azi1_deg: float,
        md2: float, inc2_deg: float, azi2_deg: float
    ) -> Tuple[float, float, float, float]:
        """
        Computes (delta_tvd, delta_north, delta_east, dls_deg_30m) between two survey stations
        using the Minimum Curvature Method.
        """
        delta_md = md2 - md1
        if delta_md < 0:
            raise ValueError(f"Station MD sequence must be non-decreasing: md1={md1}, md2={md2}")
        if delta_md == 0:
            return 0.0, 0.0, 0.0, 0.0

        i1 = math.radians(inc1_deg)
        i2 = math.radians(inc2_deg)
        a1 = math.radians(azi1_deg)
        a2 = math.radians(azi2_deg)

        # Dogleg angle (radians)
        cos_dl = math.cos(i1) * math.cos(i2) + math.sin(i1) * math.sin(i2) * math.cos(a2 - a1)
        cos_dl = max(-1.0, min(1.0, cos_dl))
        dl_rad = math.acos(cos_dl)

        # Ratio factor (RF)
        if dl_rad < 1e-6:
            rf = 1.0
        else:
            rf = (2.0 / dl_rad) * math.tan(dl_rad / 2.0)

        # Coordinate increments
        delta_tvd = (delta_md / 2.0) * (math.cos(i1) + math.cos(i2)) * rf
        delta_north = (delta_md / 2.0) * (math.sin(i1) * math.cos(a1) + math.sin(i2) * math.cos(a2)) * rf
        delta_east = (delta_md / 2.0) * (math.sin(i1) * math.sin(a1) + math.sin(i2) * math.sin(a2)) * rf

        # Dogleg severity in deg / 30m
        dls_deg_30m = math.degrees(dl_rad) * (30.0 / delta_md)

        return delta_tvd, delta_north, delta_east, dls_deg_30m

    @classmethod
    def compute_trajectory(
        cls,
        raw_stations: List[Dict[str, float]],
        kb_elevation_m: float,
        surface_northing: float = 0.0,
        surface_easting: float = 0.0
    ) -> List[SurveyStationData]:
        """
        Calculates a complete wellbore trajectory from raw survey observations.
        Ensures surface datum is anchored at (0, 0, 0).
        """
        valid_kb = cls.validate_datum(kb_elevation_m)
        if not raw_stations:
            raise InsufficientGeologicalEvidenceError("INSUFFICIENT_GEOLOGICAL_EVIDENCE: Directional survey station list is empty.")

        sorted_stations = sorted(raw_stations, key=lambda s: s["md_m"])
        computed: List[SurveyStationData] = []

        cur_tvd = 0.0
        cur_north = surface_northing
        cur_east = surface_easting

        prev_md = 0.0
        prev_inc = 0.0
        prev_azi = 0.0

        for idx, st in enumerate(sorted_stations):
            md = float(st["md_m"])
            inc = float(st["inclination_deg"])
            azi = float(st["azimuth_deg"])

            if idx == 0:
                if md > 0:
                    # Initial vertical lead
                    cur_tvd = md
                delta_tvd = cur_tvd
                dls = 0.0
            else:
                dtvd, dnorth, deast, dls = cls.minimum_curvature_step(
                    prev_md, prev_inc, prev_azi,
                    md, inc, azi
                )
                cur_tvd += dtvd
                cur_north += dnorth
                cur_east += deast

            tvdss = cur_tvd - valid_kb

            computed.append(SurveyStationData(
                md_m=md,
                inclination_deg=inc,
                azimuth_deg=azi,
                tvd_m=cur_tvd,
                tvdss_m=tvdss,
                northing_m=cur_north,
                easting_m=cur_east,
                dogleg_severity=dls,
                is_interpolated=False
            ))

            prev_md = md
            prev_inc = inc
            prev_azi = azi

        return computed

    @classmethod
    def interpolate_at_md(
        cls,
        trajectory: List[SurveyStationData],
        target_md_m: float,
        kb_elevation_m: float
    ) -> SurveyStationData:
        """
        Interpolates wellbore trajectory position at a specific target Measured Depth.
        Abstains if target MD is outside the surveyed interval.
        """
        cls.validate_datum(kb_elevation_m)
        if not trajectory:
            raise InsufficientGeologicalEvidenceError("INSUFFICIENT_GEOLOGICAL_EVIDENCE: No trajectory available for interpolation.")

        if target_md_m < trajectory[0].md_m or target_md_m > trajectory[-1].md_m:
            raise InsufficientGeologicalEvidenceError(
                f"INSUFFICIENT_GEOLOGICAL_EVIDENCE: Target MD {target_md_m}m is outside surveyed interval "
                f"[{trajectory[0].md_m}m - {trajectory[-1].md_m}m]. Extrapolation is prohibited."
            )

        # Check for exact station hit
        for st in trajectory:
            if math.isclose(st.md_m, target_md_m, abs_tol=0.05):
                return st

        # Locate interval
        for i in range(len(trajectory) - 1):
            s1 = trajectory[i]
            s2 = trajectory[i + 1]
            if s1.md_m <= target_md_m <= s2.md_m:
                fraction = (target_md_m - s1.md_m) / (s2.md_m - s1.md_m)
                interp_inc = s1.inclination_deg + fraction * (s2.inclination_deg - s1.inclination_deg)
                interp_azi = s1.azimuth_deg + fraction * (s2.azimuth_deg - s1.azimuth_deg)

                dtvd, dnorth, deast, dls = cls.minimum_curvature_step(
                    s1.md_m, s1.inclination_deg, s1.azimuth_deg,
                    target_md_m, interp_inc, interp_azi
                )

                tvd = round(s1.tvd_m + dtvd, 2)
                tvdss = round(tvd - kb_elevation_m, 2)

                return SurveyStationData(
                    md_m=target_md_m,
                    inclination_deg=interp_inc,
                    azimuth_deg=interp_azi,
                    tvd_m=tvd,
                    tvdss_m=tvdss,
                    northing_m=s1.northing_m + dnorth,
                    easting_m=s1.easting_m + deast,
                    dogleg_severity=dls,
                    is_interpolated=True
                )

        raise InsufficientGeologicalEvidenceError(f"INSUFFICIENT_GEOLOGICAL_EVIDENCE: Unable to bracket MD {target_md_m}m.")
