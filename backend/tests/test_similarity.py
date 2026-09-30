import pytest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.db.database import SessionLocal
from backend.app.services.similarity_service import similarity_service

def test_similarity_ranking_order():
    db = SessionLocal()
    try:
        ranked = similarity_service.rank_offset_wells(
            db=db,
            active_well_id="NO-15/9-F-12",
            target_formation="Hugin FM",
            current_depth_tvdss=2850.0,
            search_radius_km=5.0
        )

        assert len(ranked) > 0, "Expected ranked offset wells within 5km radius."
        # Verify ranking order is sorted descending by score
        for i in range(len(ranked) - 1):
            assert ranked[i].composite_similarity_score >= ranked[i+1].composite_similarity_score
            assert ranked[i].rank == i + 1

        # Check explainability reasons are provided
        top_offset = ranked[0]
        assert len(top_offset.explanation.primary_reasons) > 0
        assert top_offset.explanation.geospatial_distance_km <= 5.0
    finally:
        db.close()
