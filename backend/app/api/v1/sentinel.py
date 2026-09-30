"""NWIS SENTINEL — REST API ROUTER
Endpoints for Engineering Question Answering, Formation-Aware Hybrid Search,
Evidence Graph Tracing, and Independent QA Benchmarking.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db import models
from backend.app.services.sentinel_query_planner import SentinelQueryPlanner
from backend.app.services.sentinel_retrieval_engine import SentinelRetrievalEngine
from backend.app.services.sentinel_answer_engine import SentinelAnswerEngine
from backend.app.services.sentinel_eval_service import SentinelEvalService

router = APIRouter(prefix="/sentinel", tags=["NWIS Sentinel Intelligence"])


# --- Request/Response Models ---

class SentinelAskRequest(BaseModel):
    query: str = Field(..., description="Petroleum engineering question", json_schema_extra={"example": "Which offset wells experienced severe lost circulation in the Hugin formation?"})
    active_well_id: Optional[str] = Field("NO-15/9-F-14", description="Currently monitored or target wellbore")
    force_mode: Optional[str] = Field(None, description="Optional forced presentation mode: TEXT, TABLE, GEOLOGICAL, EVIDENCE, CHRONOS")


class SentinelSearchRequest(BaseModel):
    query: str = Field(..., description="Engineering search string")
    target_well_id: Optional[str] = Field(None, description="Target wellbore filter")
    target_formation: Optional[str] = Field(None, description="Target formation filter")
    event_category: Optional[str] = Field(None, description="Hazard category filter")
    temporal_cutoff: Optional[str] = Field(None, description="Point-in-Time historical cutoff date")


# --- Endpoints ---

@router.post("/ask")
def ask_sentinel(
    req: SentinelAskRequest,
    db: Session = Depends(get_db)
):
    """Answers complex petroleum engineering questions using Formation-Aware Hybrid Retrieval,
    Evidence-Level Claim Verification, and deterministic Evidence-or-Silence abstention.
    """
    try:
        return SentinelAnswerEngine.answer_engineering_query(
            db=db,
            query=req.query,
            active_well_id=req.active_well_id,
            user_role="DRILLING_ENGINEER",
            force_mode=req.force_mode
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentinel question answering failed: {str(e)}")


@router.post("/search")
def search_sentinel_evidence(
    req: SentinelSearchRequest,
    db: Session = Depends(get_db)
):
    """Executes direct 4-mode hybrid retrieval (Structured, Geospatial, Geological, Semantic)
    without natural-language synthesis.
    """
    try:
        plan = SentinelQueryPlanner.parse_query(req.query, active_well_id=req.target_well_id)
        if req.target_formation:
            plan.target_formation = req.target_formation
        if req.event_category:
            plan.event_category = req.event_category
        if req.temporal_cutoff:
            plan.temporal_cutoff = req.temporal_cutoff

        return SentinelRetrievalEngine.execute_hybrid_retrieval(db, plan, user_role="DRILLING_ENGINEER")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentinel hybrid retrieval failed: {str(e)}")


@router.get("/search")
def search_sentinel_evidence_get(
    query: Optional[str] = Query(None, description="Engineering search string"),
    target_well_id: Optional[str] = Query(None),
    target_formation: Optional[str] = Query(None),
    event_category: Optional[str] = Query(None),
    temporal_cutoff: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """GET endpoint for Sentinel hybrid search."""
    req = SentinelSearchRequest(
        query=query or "",
        target_well_id=target_well_id,
        target_formation=target_formation,
        event_category=event_category,
        temporal_cutoff=temporal_cutoff
    )
    return search_sentinel_evidence(req, db)


@router.get("/evidence/{chunk_id}")
def get_evidence_chunk(
    chunk_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves full metadata, page number, bounding box, and provenance for a specific knowledge chunk."""
    chunk = db.query(models.KnowledgeChunk).filter(models.KnowledgeChunk.chunk_id == chunk_id).first()
    if not chunk:
        raise HTTPException(status_code=404, detail=f"Knowledge chunk {chunk_id} not found.")

    return {
        "chunk_id": chunk.chunk_id,
        "doc_id": chunk.doc_id,
        "well_id": chunk.well_id,
        "page_number": chunk.page_number,
        "passage_text": chunk.passage_text,
        "formation_name": chunk.formation_name,
        "event_category": chunk.event_category,
        "depth_interval": f"{chunk.depth_start_md_m} - {chunk.depth_end_md_m} m" if chunk.depth_start_md_m else None,
        "depth_datum": chunk.depth_datum,
        "provenance_tier": chunk.provenance_tier,
        "verification_status": chunk.verification_status,
        "sha256_hash": chunk.sha256_hash,
        "source_date": chunk.source_date
    }


@router.get("/evaluation")
def get_sentinel_benchmarks(
    db: Session = Depends(get_db)
):
    """Returns the latest comparative benchmark across Baseline A, Baseline B, Baseline C, and Sentinel."""
    try:
        return SentinelEvalService.run_benchmark(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch benchmarks: {str(e)}")


@router.post("/evaluation/run")
def execute_sentinel_benchmark(
    db: Session = Depends(get_db)
):
    """Executes live 10-question evaluation benchmark measuring Recall@5, MRR, NDCG, and Abstention Correctness."""
    try:
        return SentinelEvalService.run_benchmark(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")
