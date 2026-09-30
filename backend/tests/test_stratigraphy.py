import pytest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.stratigraphic_service import stratigraphic_service

def test_haversine_distance():
    # Volve 15/9-F-12 (58.44123, 1.89531) to 15/9-F-14 (58.44315, 1.89842)
    dist_km = stratigraphic_service.haversine_distance_km(58.44123, 1.89531, 58.44315, 1.89842)
    assert 0.2 < dist_km < 0.35, f"Expected ~0.28 km, got {dist_km}"

def test_compute_tvdss():
    # TVD = 2850m, KB = 43.5m -> TVDSS = 2806.5m
    tvdss = stratigraphic_service.compute_tvdss(2850.0, 43.5)
    assert tvdss == 2806.5

def test_minimum_curvature_vertical():
    # Vertical section from 0 to 500m
    d_tvd, d_n, d_e, dls = stratigraphic_service.minimum_curvature_step(
        md1=0.0, inc1_deg=0.0, azi1_deg=0.0,
        md2=500.0, inc2_deg=0.0, azi2_deg=0.0
    )
    assert d_tvd == 500.0
    assert d_n == 0.0
    assert d_e == 0.0
    assert dls == 0.0

def test_minimum_curvature_build_section():
    # Build section from 1000m (5 deg) to 1500m (15 deg)
    d_tvd, d_n, d_e, dls = stratigraphic_service.minimum_curvature_step(
        md1=1000.0, inc1_deg=5.0, azi1_deg=45.0,
        md2=1500.0, inc2_deg=15.0, azi2_deg=45.0
    )
    assert d_tvd > 0
    assert d_tvd < 500.0 # Curvature makes TVD < MD
    assert dls > 0
