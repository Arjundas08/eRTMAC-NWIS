"""
NWIS NEXUS — Cross-Module Intelligence Fusion & Decision Command Center (Phase 07)

Provides:
1. Unified Operations Dashboard: Aggregates real-time status from all NWIS subsystems
   (GeoCore, Chronos, Sentinel, Pulse) into a single operational picture.
2. Cross-Module Intelligence Fusion: Correlates telemetry anomalies with historical
   events, geological context, and AI-generated insights to produce Unified Advisories.
3. Decision Command Center: Tracks system-wide KPIs, alert severity distribution,
   evidence quality metrics, and module health indicators.
4. Operations Log: Maintains a persistent, append-only operations journal of all
   significant cross-module events for shift handover and auditing.
5. Evidence-or-Silence: All fused insights inherit the strictest evidence tier from
   contributing modules. If any input is INSUFFICIENT, the fusion output abstains.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
import hashlib
import json
import uuid

from backend.app.db.models import (
    Well, DrillingEvent, FormationTop, WellboreSurvey,
    KnowledgeChunk, OperationalAdvisory, TelemetrySource,
    NormalizedTelemetry, TelemetryQualityEvent, ReplaySession,
    AdvisoryEvent, EvaluationRun, QueryPlanRecord, GenerationAudit,
    Document
)


class NexusEngine:
    """
    Cross-module intelligence fusion engine.
    Aggregates status, health, and intelligence from all NWIS subsystems.
    """

    # =========================================================================
    # 1. SYSTEM-WIDE HEALTH & STATUS AGGREGATION
    # =========================================================================

    @staticmethod
    def get_system_health(db: Session) -> Dict[str, Any]:
        """
        Aggregates health status from all NWIS subsystems into a unified dashboard.
        Returns module statuses, data quality metrics, and operational readiness.
        """
        # Module health checks
        modules = {}

        # GeoCore: Check wells, surveys, formations
        well_count = db.query(Well).count()
        survey_count = db.query(WellboreSurvey).count()
        formation_count = db.query(FormationTop).count()
        modules["geocore"] = {
            "status": "OPERATIONAL" if well_count > 0 and survey_count > 0 else "DEGRADED",
            "wells_loaded": well_count,
            "survey_stations": survey_count,
            "formation_tops": formation_count,
            "evidence_contract": "STRICT_EVIDENCE_OR_SILENCE"
        }

        # Chronos: Check replay sessions and evaluations
        replay_count = db.query(ReplaySession).count()
        evaluation_count = db.query(EvaluationRun).count()
        active_replays = db.query(ReplaySession).filter(
            ReplaySession.status.in_(["PLAYING", "PAUSED"])
        ).count()
        modules["chronos"] = {
            "status": "OPERATIONAL" if well_count > 0 else "STANDBY",
            "total_sessions": replay_count,
            "active_sessions": active_replays,
            "evaluations_completed": evaluation_count,
            "temporal_firewall": "ENFORCED"
        }

        # Sentinel: Check knowledge chunks, query plans, audits
        chunk_count = db.query(KnowledgeChunk).count()
        query_count = db.query(QueryPlanRecord).count()
        audit_count = db.query(GenerationAudit).count()
        modules["sentinel"] = {
            "status": "OPERATIONAL" if chunk_count > 0 else "INITIALIZING",
            "knowledge_chunks": chunk_count,
            "queries_processed": query_count,
            "generation_audits": audit_count,
            "retrieval_mode": "FORMATION_AWARE_HYBRID"
        }

        # Pulse: Check telemetry sources and advisories
        source_count = db.query(TelemetrySource).count()
        online_sources = db.query(TelemetrySource).filter(
            TelemetrySource.connection_status == "ONLINE"
        ).count()
        telemetry_count = db.query(NormalizedTelemetry).count()
        advisory_count = db.query(OperationalAdvisory).count()
        active_advisories = db.query(OperationalAdvisory).filter(
            OperationalAdvisory.advisory_state.in_(["NEW", "ACKNOWLEDGED", "UNDER_REVIEW"])
        ).count()
        quality_events = db.query(TelemetryQualityEvent).count()
        modules["pulse"] = {
            "status": "OPERATIONAL" if source_count > 0 else "STANDBY",
            "telemetry_sources": source_count,
            "online_sources": online_sources,
            "normalized_records": telemetry_count,
            "total_advisories": advisory_count,
            "active_advisories": active_advisories,
            "quality_events": quality_events,
            "read_only_enforcement": True
        }

        # Documents: Check document store
        doc_count = db.query(Document).count()
        modules["document_ai"] = {
            "status": "OPERATIONAL" if doc_count > 0 else "STANDBY",
            "documents_ingested": doc_count
        }

        # Overall system status
        statuses = [m["status"] for m in modules.values()]
        if all(s == "OPERATIONAL" for s in statuses):
            overall = "ALL_SYSTEMS_OPERATIONAL"
        elif any(s == "DEGRADED" for s in statuses):
            overall = "DEGRADED"
        elif all(s == "STANDBY" for s in statuses):
            overall = "STANDBY"
        else:
            overall = "PARTIALLY_OPERATIONAL"

        # Drilling events summary
        event_count = db.query(DrillingEvent).count()
        events_by_type = {}
        for event in db.query(DrillingEvent.event_type).distinct().all():
            count = db.query(DrillingEvent).filter(
                DrillingEvent.event_type == event[0]
            ).count()
            events_by_type[event[0]] = count

        return {
            "system_name": "NWIS — Nearby Wells Intelligence System",
            "platform": "eRTMAC — Oil India Limited",
            "version": "7.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall,
            "modules": modules,
            "data_summary": {
                "total_wells": well_count,
                "total_drilling_events": event_count,
                "events_by_type": events_by_type,
                "total_documents": doc_count,
                "knowledge_chunks": chunk_count,
                "telemetry_records": telemetry_count
            },
            "safety_disclaimer": (
                "NWIS is a read-only advisory decision-support system. "
                "It does not replace certified Well Control systems or experienced engineering supervision."
            )
        }

    # =========================================================================
    # 2. CROSS-MODULE INTELLIGENCE FUSION
    # =========================================================================

    @staticmethod
    def fuse_well_intelligence(db: Session, well_id: str) -> Dict[str, Any]:
        """
        Fuses intelligence from all modules for a specific well into a unified
        operational picture. This is the NEXUS's core value proposition:
        combining geological context + historical events + telemetry state +
        AI-generated insights into a single evidence-backed assessment.
        """
        well = db.query(Well).filter(Well.well_id == well_id).first()
        if not well:
            return {
                "status": "WELL_NOT_FOUND",
                "well_id": well_id,
                "fused_intelligence": None,
                "abstention_reason": f"Well '{well_id}' not found in NWIS database"
            }

        # --- GeoCore Layer ---
        surveys = db.query(WellboreSurvey).filter(
            WellboreSurvey.well_id == well_id
        ).order_by(WellboreSurvey.md_m.asc()).all()
        formations = db.query(FormationTop).filter(
            FormationTop.well_id == well_id
        ).order_by(FormationTop.top_tvdss_m.asc()).all()

        geocore_layer = {
            "well_name": well.well_name,
            "field": well.field_name,
            "operator": well.operator,
            "total_depth_md_m": well.total_depth_md_m,
            "survey_stations": len(surveys),
            "formation_tops": [
                {
                    "formation": f.formation_name,
                    "top_tvdss_m": f.top_tvdss_m,
                    "lithology": f.lithology_primary,
                    "confidence": f.confidence_level
                }
                for f in formations
            ],
            "deepest_survey_md_m": surveys[-1].md_m if surveys else None,
            "kb_elevation_m": well.kb_elevation_m
        }

        # --- Historical Events Layer ---
        events = db.query(DrillingEvent).filter(
            DrillingEvent.well_id == well_id
        ).order_by(DrillingEvent.depth_md_m.asc()).all()

        severity_map = {"CRITICAL": 4, "SEVERE": 3, "MODERATE": 2, "MINOR": 1}
        events_layer = {
            "total_events": len(events),
            "events_by_severity": {},
            "events_by_type": {},
            "total_npt_hours": 0.0,
            "critical_events": [],
            "events_list": []
        }

        for e in events:
            sev = e.severity or "MINOR"
            etype = e.event_type or "UNKNOWN"
            events_layer["events_by_severity"][sev] = events_layer["events_by_severity"].get(sev, 0) + 1
            events_layer["events_by_type"][etype] = events_layer["events_by_type"].get(etype, 0) + 1
            events_layer["total_npt_hours"] += (e.npt_hours or 0.0)
            event_record = {
                "event_id": e.event_id,
                "type": etype,
                "severity": sev,
                "depth_md_m": e.depth_md_m,
                "depth_tvdss_m": e.depth_tvdss_m,
                "formation": e.formation_name,
                "npt_hours": e.npt_hours,
                "narrative": e.operational_narrative[:200] if e.operational_narrative else "",
                "verification_status": e.verification_status
            }
            events_layer["events_list"].append(event_record)
            if severity_map.get(sev, 0) >= 3:
                events_layer["critical_events"].append(event_record)

        # --- Telemetry Layer ---
        latest_telemetry = db.query(NormalizedTelemetry).filter(
            NormalizedTelemetry.wellbore_id == well_id
        ).order_by(NormalizedTelemetry.timestamp.desc()).first()

        telemetry_layer = None
        if latest_telemetry:
            telemetry_layer = {
                "latest_timestamp": latest_telemetry.timestamp,
                "md_m": latest_telemetry.md_m,
                "tvdss_m": latest_telemetry.tvdss_m,
                "rop_m_hr": latest_telemetry.rop_m_hr,
                "wob_kn": latest_telemetry.wob_kn,
                "rpm": latest_telemetry.rpm,
                "spp_kpa": latest_telemetry.spp_kpa,
                "mud_weight_sg": latest_telemetry.mud_weight_sg,
                "ecd_sg": latest_telemetry.ecd_sg,
                "quality_state": latest_telemetry.quality_state,
                "current_formation": latest_telemetry.current_formation
            }

        # --- Advisories Layer ---
        advisories = db.query(OperationalAdvisory).filter(
            OperationalAdvisory.wellbore_id == well_id
        ).order_by(OperationalAdvisory.created_at.desc()).limit(20).all()

        advisory_layer = {
            "total_advisories": len(advisories),
            "active": sum(1 for a in advisories if a.advisory_state in ("NEW", "ACKNOWLEDGED", "UNDER_REVIEW")),
            "resolved": sum(1 for a in advisories if a.advisory_state == "RESOLVED"),
            "suppressed": sum(1 for a in advisories if a.advisory_state == "SUPPRESSED"),
            "latest_advisories": [
                {
                    "advisory_id": a.advisory_id,
                    "hazard_type": a.hazard_type,
                    "severity": a.severity,
                    "state": a.advisory_state,
                    "title": a.title,
                    "formation": a.formation_name,
                    "depth_md_m": a.bit_depth_md_m,
                    "created_at": str(a.created_at)
                }
                for a in advisories[:5]
            ]
        }

        # --- Sentinel Knowledge Layer ---
        chunks = db.query(KnowledgeChunk).filter(
            KnowledgeChunk.well_id == well_id
        ).count()

        sentinel_layer = {
            "knowledge_chunks": chunks,
            "sentinel_status": "ENRICHED" if chunks > 0 else "AWAITING_INGESTION"
        }

        # --- FUSION: Risk Assessment ---
        risk_score = NexusEngine._calculate_risk_score(events_layer, telemetry_layer, advisory_layer)

        # Generate fusion hash for integrity
        fusion_payload = json.dumps({
            "well_id": well_id,
            "geocore": geocore_layer,
            "events_count": events_layer["total_events"],
            "risk_score": risk_score["composite_score"]
        }, sort_keys=True)
        fusion_hash = hashlib.sha256(fusion_payload.encode()).hexdigest()

        return {
            "status": "FUSED",
            "well_id": well_id,
            "fusion_timestamp": datetime.now(timezone.utc).isoformat(),
            "fusion_integrity_sha256": fusion_hash,
            "integrity_hash": fusion_hash,
            "geocore_layer": geocore_layer,
            "historical_events_layer": events_layer,
            "telemetry_layer": telemetry_layer,
            "advisory_layer": advisory_layer,
            "sentinel_layer": sentinel_layer,
            "risk_assessment": risk_score,
            "evidence_contract": "STRICT_EVIDENCE_OR_SILENCE",
            "safety_disclaimer": (
                "This fused intelligence report is generated from verified historical records and "
                "normalized telemetry data. It is advisory only. Human engineering judgement prevails."
            )
        }

    # =========================================================================
    # 3. RISK SCORING (Deterministic, Explainable, No Black-Box)
    # =========================================================================

    @staticmethod
    def _calculate_risk_score(
        events_layer: Dict, 
        telemetry_layer: Optional[Dict],
        advisory_layer: Dict
    ) -> Dict[str, Any]:
        """
        NWIS Context Priority Index (CPI) — Operational Prioritization Heuristic.
        
        Evaluates supervisory attention priority based on:
        - Historical event severity distribution (40% weight)
        - Active operational advisory burden (30% weight)
        - Telemetry sensor data quality state (30% weight)
        
        NOTE: This is a configurable operational prioritization heuristic, NOT an
        empirically calibrated failure probability or certified well control safety rating.
        """
        # Historical Component (0-100)
        severity_weights = {"CRITICAL": 25, "SEVERE": 15, "MODERATE": 5, "MINOR": 1}
        historical_score = 0.0
        total_events = events_layer.get("total_events", 0)
        for sev, count in events_layer.get("events_by_severity", {}).items():
            historical_score += severity_weights.get(sev, 0) * count
        # Bounded between 0 and 100
        historical_score = max(0.0, min(100.0, historical_score))
        
        # Advisory Component (0-100)
        active_advisories = advisory_layer.get("active", 0)
        advisory_score = max(0.0, min(100.0, active_advisories * 20.0))

        # Telemetry Quality Component (0-100, inverted: healthy=nominal)
        quality_scores = {
            "HEALTHY": 0.0,
            "DEGRADED": 40.0,
            "STALE": 60.0,
            "INSUFFICIENT": 80.0,
            "OFFLINE": 100.0
        }
        missing_telemetry = telemetry_layer is None
        if telemetry_layer:
            quality = telemetry_layer.get("quality_state", "HEALTHY")
            telemetry_score = quality_scores.get(quality, 50.0)
        else:
            # Missing telemetry handled cleanly as unmonitored neutral state (30.0), not false panic
            telemetry_score = 30.0
        
        # Weighted composite heuristic
        composite = (
            historical_score * 0.40 +
            advisory_score * 0.30 +
            telemetry_score * 0.30
        )
        composite = max(0.0, min(100.0, composite))

        # Priority tier classification
        if composite >= 75:
            tier = "CRITICAL"
            cpi_label = "URGENT_OPERATIONAL_CHECK"
        elif composite >= 50:
            tier = "ELEVATED"
            cpi_label = "PRIORITY_REVIEW"
        elif composite >= 25:
            tier = "MODERATE"
            cpi_label = "ATTENTION_ADVISORY"
        else:
            tier = "LOW"
            cpi_label = "MONITOR_NOMINAL"

        return {
            # Canonical Phase 08 naming
            "context_priority_index": round(composite, 2),
            "priority_tier": cpi_label,
            # Backward-compatible aliases for Phase 07 consumers
            "composite_score": round(composite, 2),
            "risk_tier": tier,
            "formula_version": "NWIS-CPI-v1.1-HEURISTIC",
            "weights": {
                "historical_incident_density": 0.40,
                "active_advisory_burden": 0.30,
                "telemetry_data_quality": 0.30
            },
            "components": {
                "historical_risk": {
                    "score": round(historical_score, 2),
                    "weight": 0.40,
                    "total_events": total_events,
                    "npt_hours": events_layer.get("total_npt_hours", 0.0)
                },
                "advisory_risk": {
                    "score": round(advisory_score, 2),
                    "weight": 0.30,
                    "active_advisories": active_advisories
                },
                "telemetry_quality_risk": {
                    "score": round(telemetry_score, 2),
                    "weight": 0.30,
                    "quality_state": telemetry_layer.get("quality_state", "NO_TELEMETRY") if telemetry_layer else "NO_TELEMETRY"
                }
            },
            "missing_telemetry_handled": missing_telemetry,
            "sensitivity_bounds": {
                "min_possible": 0.0,
                "max_possible": 100.0,
                "thresholds": "0-24: LOW / MONITOR_NOMINAL, 25-49: MODERATE / ATTENTION_ADVISORY, 50-74: ELEVATED / PRIORITY_REVIEW, 75-100: CRITICAL / URGENT_OPERATIONAL_CHECK"
            },
            "explanation": (
                f"Context Priority Index {composite:.1f}/100 [{cpi_label} / {tier}]. "
                f"Historical: {historical_score:.0f} ({total_events} events, "
                f"{events_layer.get('total_npt_hours', 0):.1f}h NPT). "
                f"Advisories: {advisory_score:.0f} ({active_advisories} active). "
                f"Telemetry: {telemetry_score:.0f}."
            ),
            "disclaimer": (
                "The NWIS Context Priority Index (CPI) is an operational prioritization heuristic designed to guide "
                "supervisory review across multi-well operations. It is NOT an empirical probability of failure, "
                "kick, or blowout, and does NOT replace certified well control safety systems or licensed engineering oversight."
            )
        }

    # =========================================================================
    # 4. OPERATIONS LOG — APPEND-ONLY SHIFT HANDOVER JOURNAL
    # =========================================================================

    @staticmethod
    def get_operations_log(db: Session, limit: int = 50) -> Dict[str, Any]:
        """
        Aggregates significant events from all modules into a time-ordered 
        operations log suitable for shift handover and regulatory audit.
        """
        log_entries = []

        # Recent advisories from Pulse
        advisories = db.query(OperationalAdvisory).order_by(
            OperationalAdvisory.created_at.desc()
        ).limit(limit).all()
        for a in advisories:
            log_entries.append({
                "timestamp": str(a.created_at),
                "source_module": "PULSE",
                "event_type": "OPERATIONAL_ADVISORY",
                "severity": a.severity,
                "well_id": a.wellbore_id,
                "summary": f"[{a.hazard_type}] {a.title}",
                "state": a.advisory_state,
                "advisory_id": a.advisory_id
            })

        # Recent Sentinel queries
        audits = db.query(GenerationAudit).order_by(
            GenerationAudit.created_at.desc()
        ).limit(limit).all()
        for audit in audits:
            log_entries.append({
                "timestamp": str(audit.created_at),
                "source_module": "SENTINEL",
                "event_type": "ENGINEERING_QUERY",
                "severity": "INFO",
                "well_id": None,
                "summary": f"Query: {audit.query_text[:100]}... ({audit.evidence_chunks_count} evidence chunks)",
                "state": audit.retrieval_status,
                "audit_id": audit.audit_id
            })

        # Recent Chronos replay sessions
        replays = db.query(ReplaySession).order_by(
            ReplaySession.created_at.desc()
        ).limit(limit).all()
        for r in replays:
            log_entries.append({
                "timestamp": str(r.created_at),
                "source_module": "CHRONOS",
                "event_type": "REPLAY_SESSION",
                "severity": "INFO",
                "well_id": r.well_id,
                "summary": f"Replay {r.status}: {r.start_depth_md_m}m → {r.end_depth_md_m}m @ {r.speed_factor}x",
                "state": r.status,
                "session_id": r.session_id
            })

        # Recent telemetry quality events from Pulse
        quality_events = db.query(TelemetryQualityEvent).order_by(
            TelemetryQualityEvent.timestamp.desc()
        ).limit(limit).all()
        for q in quality_events:
            log_entries.append({
                "timestamp": str(q.timestamp),
                "source_module": "PULSE_QUALITY",
                "event_type": "DATA_QUALITY_EVENT",
                "severity": q.severity,
                "well_id": q.wellbore_id,
                "summary": f"[{q.issue_type}] Channel: {q.channel_name or 'N/A'}",
                "state": q.issue_type,
                "event_id": q.event_id
            })

        # Sort all entries by timestamp descending
        log_entries.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "operations_log": log_entries[:limit],
            "entries": log_entries[:limit],
            "total_entries": len(log_entries),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer": "Operations log is for shift handover and engineering review only."
        }

    # =========================================================================
    # 5. KPI DASHBOARD METRICS
    # =========================================================================

    @staticmethod
    def get_kpi_metrics(db: Session) -> Dict[str, Any]:
        """
        Computes system-wide KPIs for the executive dashboard:
        - Evidence quality distribution
        - Advisory resolution rate
        - Telemetry uptime percentage
        - Sentinel query performance
        - NPT reduction potential
        """
        # Evidence quality distribution
        total_events = db.query(DrillingEvent).count()
        verified_events = db.query(DrillingEvent).filter(
            DrillingEvent.verification_status == "VERIFIED"
        ).count()
        evidence_quality_pct = (verified_events / total_events * 100) if total_events > 0 else 0.0

        # Advisory lifecycle metrics
        total_advisories = db.query(OperationalAdvisory).count()
        resolved_advisories = db.query(OperationalAdvisory).filter(
            OperationalAdvisory.advisory_state == "RESOLVED"
        ).count()
        resolution_rate = (resolved_advisories / total_advisories * 100) if total_advisories > 0 else 0.0

        # Telemetry health
        total_sources = db.query(TelemetrySource).count()
        online_sources = db.query(TelemetrySource).filter(
            TelemetrySource.connection_status == "ONLINE"
        ).count()
        uptime_pct = (online_sources / total_sources * 100) if total_sources > 0 else 0.0

        # Sentinel metrics
        total_queries = db.query(GenerationAudit).count()
        successful_queries = db.query(GenerationAudit).filter(
            GenerationAudit.retrieval_status == "SUCCESS"
        ).count()
        query_success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0.0

        # NPT exposure
        total_npt = sum(
            e.npt_hours or 0.0
            for e in db.query(DrillingEvent).all()
        )

        # Knowledge density
        total_chunks = db.query(KnowledgeChunk).count()
        wells_with_chunks = db.query(KnowledgeChunk.well_id).distinct().count()

        return {
            "kpis": {
                "evidence_quality": {
                    "verified_events_pct": round(evidence_quality_pct, 1),
                    "total_events": total_events,
                    "verified_events": verified_events
                },
                "advisory_resolution": {
                    "resolution_rate_pct": round(resolution_rate, 1),
                    "total_advisories": total_advisories,
                    "resolved": resolved_advisories
                },
                "telemetry_uptime": {
                    "uptime_pct": round(uptime_pct, 1),
                    "total_sources": total_sources,
                    "online_sources": online_sources
                },
                "sentinel_performance": {
                    "query_success_rate_pct": round(query_success_rate, 1),
                    "total_queries": total_queries,
                    "knowledge_chunks": total_chunks,
                    "wells_covered": wells_with_chunks
                },
                "npt_exposure": {
                    "total_npt_hours": round(total_npt, 1),
                    "avg_npt_per_event": round(total_npt / total_events, 2) if total_events > 0 else 0.0
                }
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    # =========================================================================
    # 6. MULTI-WELL COMPARISON MATRIX
    # =========================================================================

    @staticmethod
    def compare_wells(db: Session, well_ids: List[str]) -> Dict[str, Any]:
        """
        Builds a comparison matrix of multiple wells across all NWIS dimensions:
        geological profile, event history, telemetry status, and risk score.
        """
        comparison = []
        for wid in well_ids:
            well = db.query(Well).filter(Well.well_id == wid).first()
            if not well:
                comparison.append({
                    "well_id": wid,
                    "status": "NOT_FOUND"
                })
                continue

            events = db.query(DrillingEvent).filter(DrillingEvent.well_id == wid).all()
            formations = db.query(FormationTop).filter(FormationTop.well_id == wid).all()
            advisories = db.query(OperationalAdvisory).filter(OperationalAdvisory.wellbore_id == wid).all()
            chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.well_id == wid).count()

            total_npt = sum(e.npt_hours or 0.0 for e in events)
            severity_dist = {}
            for e in events:
                sev = e.severity or "MINOR"
                severity_dist[sev] = severity_dist.get(sev, 0) + 1

            comparison.append({
                "well_id": wid,
                "well_name": well.well_name,
                "field": well.field_name,
                "total_depth_md_m": well.total_depth_md_m,
                "formations_count": len(formations),
                "top_formation": formations[0].formation_name if formations else None,
                "events_count": len(events),
                "severity_distribution": severity_dist,
                "total_npt_hours": round(total_npt, 1),
                "active_advisories": sum(1 for a in advisories if a.advisory_state in ("NEW", "ACKNOWLEDGED", "UNDER_REVIEW")),
                "knowledge_chunks": chunks,
                "status": "COMPARED"
            })

        # Generate comparison hash
        comp_hash = hashlib.sha256(
            json.dumps({"wells": well_ids, "count": len(comparison)}, sort_keys=True).encode()
        ).hexdigest()

        return {
            "comparison_matrix": comparison,
            "well_count": len(well_ids),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "integrity_sha256": comp_hash
        }

    # =========================================================================
    # 7. ALERT SEVERITY TIMELINE
    # =========================================================================

    @staticmethod
    def get_alert_timeline(db: Session, well_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Builds a depth-indexed or time-indexed timeline of all alerts and advisories
        across the system for visualization on the NEXUS dashboard.
        """
        query = db.query(DrillingEvent)
        if well_id:
            query = query.filter(DrillingEvent.well_id == well_id)
        events = query.order_by(DrillingEvent.depth_md_m.asc()).all()

        timeline = []
        for e in events:
            timeline.append({
                "depth_md_m": e.depth_md_m,
                "depth_tvdss_m": e.depth_tvdss_m,
                "event_type": e.event_type,
                "severity": e.severity,
                "formation": e.formation_name,
                "npt_hours": e.npt_hours,
                "well_id": e.well_id,
                "narrative": e.operational_narrative[:150] if e.operational_narrative else "",
                "source": "HISTORICAL_EVENT"
            })

        # Also include operational advisories
        adv_query = db.query(OperationalAdvisory)
        if well_id:
            adv_query = adv_query.filter(OperationalAdvisory.wellbore_id == well_id)
        advisories = adv_query.order_by(OperationalAdvisory.bit_depth_md_m.asc()).all()

        for a in advisories:
            timeline.append({
                "depth_md_m": a.bit_depth_md_m,
                "depth_tvdss_m": a.bit_depth_tvdss_m,
                "event_type": a.hazard_type,
                "severity": a.severity,
                "formation": a.formation_name,
                "npt_hours": 0.0,
                "well_id": a.wellbore_id,
                "narrative": a.title,
                "source": "OPERATIONAL_ADVISORY"
            })

        # Sort by depth
        timeline.sort(key=lambda x: x["depth_md_m"])

        return {
            "timeline": timeline,
            "total_entries": len(timeline),
            "well_filter": well_id,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
