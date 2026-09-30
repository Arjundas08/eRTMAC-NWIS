"""NWIS SENTINEL — ENGINEERING QUERY PLANNER
Translates complex petroleum engineering questions into validated, typed query plans.
Enforces depth datum verification (never silently substitute MD for TVDSS), parameterization,
and zero raw SQL execution.
"""

import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class EngineeringQueryPlan(BaseModel):
    raw_query: str
    target_well_id: Optional[str] = None
    target_formation: Optional[str] = None
    event_category: Optional[str] = None
    depth_min_m: Optional[float] = None
    depth_max_m: Optional[float] = None
    depth_datum: str = "MD" # MD, TVD, TVDSS
    temporal_cutoff: Optional[str] = None
    intent_type: str = "HAZARD_LOOKUP" # HAZARD_LOOKUP, OFFSET_COMPARISON, FORMATION_EXPERIENCE, EVIDENCE_INSPECTION, CHRONOS_EXPLANATION, WHY_THIS_WELL, PARAMETER_CHECK
    answer_mode: str = "TEXT" # TEXT, TABLE, GEOLOGICAL, EVIDENCE, CHRONOS
    is_datum_ambiguous: bool = False
    requires_verified_only: bool = True
    caveats: List[str] = []

class SentinelQueryPlanner:
    """
    Understands petroleum engineering syntax, terminology, formation names,
    and depth references without hallucinating unmentioned constraints.
    """

    KNOWN_WELLS = [
        "NO-15/9-F-12", "NO-15/9-F-14", "NO-15/9-F-15S", "NO-15/9-F-4", "NO-15/9-F-1"
    ]
    WELL_ALIASES = {
        "f-12": "NO-15/9-F-12",
        "f12": "NO-15/9-F-12",
        "f-14": "NO-15/9-F-14",
        "f14": "NO-15/9-F-14",
        "f-15s": "NO-15/9-F-15S",
        "f15s": "NO-15/9-F-15S",
        "f-4": "NO-15/9-F-4",
        "f4": "NO-15/9-F-4",
        "f-1": "NO-15/9-F-1",
        "f1": "NO-15/9-F-1"
    }

    FORMATIONS = [
        "Nordland GP", "Utsira FM", "Hordaland GP", "Rogaland GP",
        "Balder FM", "Sele FM", "Lista FM", "Shetland GP",
        "Cromer Knoll GP", "Viking GP", "Draupne FM", "Heather FM",
        "Vestland GP", "Hugin FM", "Sleipner FM", "Skagerrak FM", "Smith Bank FM"
    ]

    HAZARD_PATTERNS = {
        "LOST_CIRCULATION": [
            r"lost circulation", r"mud loss", r"losses", r"seepage", r"thief zone", r"lcm"
        ],
        "STUCK_PIPE": [
            r"stuck pipe", r"pipe stuck", r"differential sticking", r"mechanical sticking", r"drag"
        ],
        "PACKOFF": [
            r"packoff", r"pack-off", r"tight hole", r"bridging", r"annular restriction"
        ],
        "KICK_GAS_INFLUX": [
            r"kick", r"gas influx", r"influx", r"pit gain", r"flow show", r"well control"
        ],
        "TORQUE_DRAG_ANOMALY": [
            r"torque", r"high torque", r"erratic torque", r"excessive drag"
        ]
    }

    @classmethod
    def parse_query(cls, query: str, active_well_id: Optional[str] = None) -> EngineeringQueryPlan:
        q = query.strip()
        q_lower = q.lower()
        caveats = []

        # 1. Target Well Extraction
        target_well = None
        for alias, well_id in cls.WELL_ALIASES.items():
            if re.search(rf"\b{re.escape(alias)}\b", q_lower):
                target_well = well_id
                break
        if not target_well:
            for w in cls.KNOWN_WELLS:
                if w.lower() in q_lower:
                    target_well = w
                    break
        if not target_well and active_well_id:
            target_well = active_well_id

        # 2. Formation Extraction
        target_formation = None
        for fm in cls.FORMATIONS:
            fm_clean = fm.lower().replace(" fm", "").replace(" gp", "")
            if re.search(rf"\b{re.escape(fm_clean)}\b", q_lower):
                target_formation = fm
                break

        # Fallback: capture any named "X formation" or "X FM" even if not in Volve catalog
        if not target_formation:
            fm_match = re.search(r"\b([a-zA-Z]+)\s+(?:formation|fm|group|gp)\b", q_lower)
            if fm_match:
                cand = fm_match.group(1).capitalize()
                if cand.lower() not in ["this", "that", "the", "any", "which", "each"]:
                    target_formation = f"{cand} FM"

        # 3. Hazard Category Extraction
        event_category = None
        for hazard, patterns in cls.HAZARD_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, q_lower):
                    event_category = hazard
                    break
            if event_category:
                break

        # 4. Depth & Datum Extraction
        # Look for e.g. "between 2800 and 3100 m TVDSS" or "at 2965m"
        depth_datum = "MD"
        is_ambiguous = False
        if "tvdss" in q_lower:
            depth_datum = "TVDSS"
        elif "tvd" in q_lower:
            depth_datum = "TVD"
        elif "md" in q_lower:
            depth_datum = "MD"
        else:
            # If numbers exist (e.g. 2950m or 2950) but no datum specified, flag ambiguity
            has_numbers = re.search(r"\d{3,4}", q)
            if has_numbers and ("depth" in q_lower or "meter" in q_lower or "m" in q_lower):
                is_ambiguous = True
                caveats.append("Depth datum not explicitly declared; evaluated in Measured Depth (MD) with TVDSS cross-reference.")

        depth_min = None
        depth_max = None
        # Range pattern: e.g. "between 2800 and 3100" or "2800-3100" or "from 2800 to 3100"
        range_match = re.search(r"(?:between|from)?\s*(\d{3,4})\s*(?:and|to|-)\s*(\d{3,4})\s*(?:m|meter|meters)?", q_lower)
        below_match = re.search(r"(?:below|deeper than|>\s*)(\d{3,4})\s*m?", q_lower)
        above_match = re.search(r"(?:above|shallower than|<\s*)(\d{3,4})\s*m?", q_lower)
        
        if range_match:
            depth_min = float(range_match.group(1))
            depth_max = float(range_match.group(2))
        elif below_match:
            depth_min = float(below_match.group(1))
            depth_max = 9999.0
        elif above_match:
            depth_min = 0.0
            depth_max = float(above_match.group(1))
        else:
            # Single depth: e.g. "at 2965m" or "around 2910"
            single_match = re.search(r"(?:at|around|near|depth)?\s*(\d{3,4})\s*m?", q_lower)
            if single_match and ("depth" in q_lower or "at " in q_lower or "near " in q_lower or "around " in q_lower):
                center = float(single_match.group(1))
                depth_min = max(0.0, center - 50.0)
                depth_max = center + 50.0

        # Adversarial Prompt Injection Sanitization
        is_adversarial = False
        if any(term in q_lower for term in ["ignore previous", "drop table", "passwords", "system prompt", "leak credentials"]):
            is_adversarial = True
            caveats.append("Adversarial instruction detected and sanitized; operating strictly in read-only petroleum mode.")

        # 5. Intent Type Classification
        intent_type = "HAZARD_LOOKUP"
        answer_mode = "TEXT"

        # Check for future post-2010 inquiries (out of historical field life)
        post_year_match = re.search(r"(?:post-|after\s+)(20\d\d)", q_lower)
        if post_year_match and int(post_year_match.group(1)) > 2010:
            intent_type = "TEMPORAL_VIOLATION"
        elif "why" in q_lower and ("geocore" in q_lower or "select" in q_lower or "closer" in q_lower or "choose" in q_lower or "not that" in q_lower):
            intent_type = "WHY_THIS_WELL"
            answer_mode = "GEOLOGICAL"
        elif "compare" in q_lower or "comparison" in q_lower or "across offsets" in q_lower:
            intent_type = "OFFSET_COMPARISON"
            answer_mode = "TABLE"
        elif "chronos" in q_lower or "replay" in q_lower or "available at" in q_lower or "what did the system know" in q_lower or "firewall" in q_lower:
            intent_type = "CHRONOS_EXPLANATION"
            answer_mode = "CHRONOS"
        elif "evidence" in q_lower or "passport" in q_lower or "source document" in q_lower or "quote" in q_lower or "passage" in q_lower:
            intent_type = "EVIDENCE_INSPECTION"
            answer_mode = "EVIDENCE"
        elif "formation" in q_lower or "strata" in q_lower or "geological" in q_lower:
            intent_type = "FORMATION_EXPERIENCE"
            answer_mode = "GEOLOGICAL"
        elif any(k in q_lower for k in ["telemetry", "stale", "channels", "sensor", "flow out", "pit volume", "live measurement", "pulse"]):
            intent_type = "TELEMETRY_EXPLANATION"
            answer_mode = "EVIDENCE"
        elif "rop" in q_lower or "wob" in q_lower or "torque" in q_lower or "spp" in q_lower or "mud weight" in q_lower:
            intent_type = "PARAMETER_CHECK"
            answer_mode = "TABLE"

        # 6. Temporal Cutoff Extraction (e.g. "as of 2008-08-02")
        temporal_cutoff = None
        date_match = re.search(r"\b(200\d[-/]\d{2}[-/]\d{2})\b", q)
        if date_match:
            temporal_cutoff = date_match.group(1).replace("/", "-") + "T00:00:00"

        return EngineeringQueryPlan(
            raw_query=query,
            target_well_id=target_well,
            target_formation=target_formation,
            event_category=event_category,
            depth_min_m=depth_min,
            depth_max_m=depth_max,
            depth_datum=depth_datum,
            temporal_cutoff=temporal_cutoff,
            intent_type=intent_type,
            answer_mode=answer_mode,
            is_datum_ambiguous=is_ambiguous,
            requires_verified_only=True,
            caveats=caveats
        )
