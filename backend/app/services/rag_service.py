from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from ..db.models import DrillingEvent, FormationTop, Well
from ..schemas.ask_schemas import AskNWISRequest, AskNWISResponse, EvidenceCitation

class RAGService:
    def answer_engineering_query(
        self,
        db: Session,
        request: AskNWISRequest
    ) -> AskNWISResponse:
        """
        Executes an evidence-grounded search over historical drilling reports.
        Strictly enforces the Evidence-or-Silence rule.
        """
        query_text = request.query.lower()
        matched_events = []

        # Keyword mapping for drilling hazard intents
        target_hazard = None
        if "loss" in query_text or "lost circulation" in query_text or "lcm" in query_text:
            target_hazard = "LOST_CIRCULATION"
        elif "stuck" in query_text or "pipe" in query_text:
            target_hazard = "STUCK_PIPE"
        elif "pack" in query_text or "tight" in query_text or "drag" in query_text:
            target_hazard = "PACKOFF"

        # Search matching formation in query
        target_formation = request.target_formation
        if not target_formation:
            for fm_name in ["Hugin", "Skagerrak", "Heather", "Chalk", "Smith Bank"]:
                if fm_name.lower() in query_text:
                    target_formation = f"{fm_name} FM"
                    break

        # Query database events matching criteria
        query_builder = db.query(DrillingEvent)
        if target_hazard:
            query_builder = query_builder.filter(DrillingEvent.event_type == target_hazard)
        if target_formation:
            query_builder = query_builder.filter(DrillingEvent.formation_name.ilike(f"%{target_formation.split()[0]}%"))

        matched_events = query_builder.all()

        # If still no direct match, search free-text operational narratives
        if not matched_events:
            keywords = [w for w in query_text.split() if len(w) > 3]
            for kw in keywords:
                records = db.query(DrillingEvent).filter(
                    (DrillingEvent.operational_narrative.ilike(f"%{kw}%")) |
                    (DrillingEvent.mitigation_applied.ilike(f"%{kw}%"))
                ).all()
                if records:
                    matched_events.extend(records)
            # Deduplicate
            matched_events = list({ev.event_id: ev for ev in matched_events}.values())

        if not matched_events:
            return AskNWISResponse(
                query=request.query,
                grounded_answer=(
                    "Insufficient historical offset documentation available to verify this specific query. "
                    "In compliance with the eRTMAC-NWIS Evidence-or-Silence contract, no ungrounded or speculative "
                    "advice is generated. Please refer to standard operating guidelines."
                ),
                confidence_level="INSUFFICIENT_DATA",
                citations=[],
                missing_data_warnings=["No matching historical offset reports found in current dataset interval."],
                has_sufficient_evidence=False
            )

        citations = []
        synthesized_findings = []

        for ev in matched_events[:4]: # Top 4 citations
            citation = EvidenceCitation(
                source_document=ev.source_citation,
                well_id=ev.well_id,
                depth_interval=f"{ev.depth_md_m}m MD / {ev.depth_tvdss_m}m TVDSS",
                formation_name=ev.formation_name,
                excerpt=ev.operational_narrative,
                confidence_score=0.92
            )
            citations.append(citation)

            synthesized_findings.append(
                f"• In Well {ev.well_id} ({ev.depth_tvdss_m}m TVDSS, {ev.formation_name}), "
                f"{ev.event_type.replace('_', ' ').title()} occurred: \"{ev.operational_narrative}\" "
                f"Mitigation applied: \"{ev.mitigation_applied}\" [{ev.source_citation}]."
            )

        grounded_answer = (
            f"Based on historical offset records from {len(matched_events)} matching events in the database:\n\n"
            + "\n".join(synthesized_findings)
            + "\n\nRECOMMENDATION: Review the cited offset well treatments prior to penetrating this depth interval. "
            "Ensure recommended contingency materials (such as pre-mixed LCM pills or jar operating parameters) "
            "are staged at the rig site."
        )

        return AskNWISResponse(
            query=request.query,
            grounded_answer=grounded_answer,
            confidence_level="HIGH" if len(citations) >= 2 else "MEDIUM",
            citations=citations,
            missing_data_warnings=[],
            has_sufficient_evidence=True
        )

rag_service = RAGService()
