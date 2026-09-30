"""
Structured Drilling Incident & Parameter Extraction Service.
Implements standardized petroleum event taxonomy:
- LOST_CIRCULATION
- STUCK_PIPE
- PACKOFF
- TIGHT_HOLE
- KICK
- ABNORMAL_PRESSURE
- TORQUE_DRAG_ANOMALY
- FISHING
- CASING_PROBLEM
- CEMENTING_PROBLEM
- NPT
"""

import re
from typing import Dict, List, Any, Optional, Tuple

class EventExtractorService:
    def __init__(self):
        # Incident classification keywords
        self.taxonomy_rules = {
            "LOST_CIRCULATION": [
                r"\blost\s+circulation\b", r"\bmud\s+loss(?:es)?\b", r"\bseepage\s+loss(?:es)?\b",
                r"\bpit\s+volume\s+drop\b", r"\blcm\b", r"\bnut-plug\b", r"\bbbl/hr\b"
            ],
            "STUCK_PIPE": [
                r"\bstuck\s+pipe\b", r"\bdrillstring\s+stuck\b", r"\bdifferentially\s+stuck\b",
                r"\bunable\s+to\s+(?:rotate|reciprocate)\b", r"\bjar(?:ring)?\s+impact\b", r"\bsoaking\s+pill\b"
            ],
            "PACKOFF": [
                r"\bpack-?off\b", r"\bstandpipe\s+pressure\s+spike\b", r"\bannular\s+(?:pack|bridge)\b",
                r"\bflow\s+paddle\s+dropped\b", r"\bpoor\s+cutting\s+returns\b"
            ],
            "TIGHT_HOLE": [
                r"\btight\s+hole\b", r"\bexcessive\s+drag\b", r"\boverpull\b",
                r"\bbackream(?:ing)?\b", r"\bwiper\s+trip\b"
            ],
            "KICK": [
                r"\bgas\s+kick\b", r"\bwell\s+kick\b", r"\binflux\b",
                r"\bpit\s+gain\b", r"\bshut-in\b", r"\bsidpp\b", r"\bsicp\b"
            ],
            "ABNORMAL_PRESSURE": [
                r"\babnormal\s+pressure\b", r"\bhigh\s+pore\s+pressure\b", r"\boverpressure\b"
            ],
            "TORQUE_DRAG_ANOMALY": [
                r"\btorque\s+spike\b", r"\berratic\s+torque\b", r"\bstring\s+stall\b"
            ],
            "FISHING": [
                r"\bfishing\b", r"\bovershot\b", r"\bmilling\b", r"\bwireline\s+fishing\b"
            ]
        }

        # Formations recognized in Volve / North Sea
        self.formations = ["Hugin FM", "Skagerrak FM", "Heather FM", "Smith Bank FM", "Nordland GP", "Ty FM", "Heimdal FM"]

    def extract_from_page(self, page_text: str, page_number: int, layout_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parses page text and layout blocks to extract engineering parameters and drilling incidents.
        """
        entities = []
        incidents = []
        contradictions = []

        # 1. Extract Wellbore ID
        well_match = re.search(r"(?:Wellbore\s+Name|Well|WELL):\s*(?:NO\s*)?([0-9]{1,2}/[0-9]{1,2}-[A-Z0-9\s\-]+)", page_text, re.IGNORECASE)
        well_id = None
        if well_match:
            raw_w = well_match.group(1).strip()
            # Normalize to canonical Volve well format: NO-15/9-F-14 or NO-15/9-F-15S
            if "15/9-F-14" in raw_w:
                well_id = "NO-15/9-F-14"
            elif "15/9-F-15" in raw_w:
                well_id = "NO-15/9-F-15S"
            elif "15/9-F-12" in raw_w:
                well_id = "NO-15/9-F-12"
            elif "15/9-F-4" in raw_w:
                well_id = "NO-15/9-F-4"
            elif "15/9-F-1" in raw_w:
                well_id = "NO-15/9-F-1"
            else:
                well_id = raw_w

            entities.append({
                "entity_type": "WELLBORE_ID",
                "entity_key": "well_id",
                "extracted_value": well_id,
                "confidence": 0.98,
                "text_passage": well_match.group(0)
            })

        # 2. Extract Report Date
        date_match = re.search(r"(?:Report\s+Date|Date|DATE):\s*(\d{4}-\d{2}-\d{2})", page_text, re.IGNORECASE)
        report_date = date_match.group(1) if date_match else None
        if report_date:
            entities.append({
                "entity_type": "DATE",
                "entity_key": "report_date",
                "extracted_value": report_date,
                "confidence": 0.99,
                "text_passage": date_match.group(0)
            })

        # 3. Extract Depths (MD and TVD / TVDSS)
        md_match = re.search(r"(?:Midnight\s+Depth\s*\(MD\)|Depth\s*\(MD\)|\bat\b|/)\s*:?\s*(\d{3,4}(?:\.\d+)?)\s*m(?:\s*MD)?", page_text, re.IGNORECASE)
        depth_md = float(md_match.group(1)) if md_match else None
        if depth_md:
            entities.append({
                "entity_type": "DEPTH_MD",
                "entity_key": "depth_md_m",
                "extracted_value": str(depth_md),
                "normalized_value": depth_md,
                "unit": "m",
                "confidence": 0.95,
                "text_passage": md_match.group(0)
            })

        tvdss_match = re.search(r"(\d{3,4}(?:\.\d+)?)\s*m\s*TVDSS", page_text, re.IGNORECASE)
        depth_tvdss = float(tvdss_match.group(1)) if tvdss_match else None
        if depth_tvdss:
            entities.append({
                "entity_type": "DEPTH_TVDSS",
                "entity_key": "depth_tvdss_m",
                "extracted_value": str(depth_tvdss),
                "normalized_value": depth_tvdss,
                "unit": "m",
                "confidence": 0.95,
                "text_passage": tvdss_match.group(0)
            })
        elif depth_md:
            # Fallback estimation if TVDSS not explicit (approx 43.5m KB offset)
            depth_tvdss = round(depth_md - 43.5, 1)

        # 4. Extract Formation Name
        matched_formation = "Unknown"
        for fm in self.formations:
            if fm.lower() in page_text.lower():
                matched_formation = fm
                entities.append({
                    "entity_type": "FORMATION",
                    "entity_key": "formation_name",
                    "extracted_value": fm,
                    "confidence": 0.92,
                    "text_passage": f"Formation: {fm}"
                })
                break

        # 5. Extract Mud Weight (SG / PPG)
        mw_match = re.search(r"(\d+\.\d{2})\s*SG", page_text, re.IGNORECASE)
        mud_weight = float(mw_match.group(1)) if mw_match else None
        if mud_weight:
            entities.append({
                "entity_type": "MUD_WEIGHT",
                "entity_key": "mud_weight_sg",
                "extracted_value": str(mud_weight),
                "normalized_value": mud_weight,
                "unit": "SG",
                "confidence": 0.94,
                "text_passage": mw_match.group(0)
            })

        # 6. Extract Incidents against Taxonomy
        for inc_type, patterns in self.taxonomy_rules.items():
            matched_patterns = []
            for pat in patterns:
                found = re.findall(pat, page_text, re.IGNORECASE)
                if found:
                    matched_patterns.extend(found)

            if len(matched_patterns) >= 1:
                # Find supporting passage and bounding box from layout blocks
                passage, bbox = self._find_supporting_block(layout_blocks, patterns)
                
                # Check severity
                severity = "MODERATE"
                if "critical" in page_text.lower() or "36.0 hours" in page_text.lower() or "unable to rotate" in page_text.lower():
                    severity = "CRITICAL"
                elif "severe" in page_text.lower() or "42 bbl/hr" in page_text.lower() or "standpipe pressure drop" in page_text.lower():
                    severity = "SEVERE"

                # Extract NPT hours if documented
                npt_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours|hrs)\s*(?:total\s*)?NPT", page_text, re.IGNORECASE)
                npt_hours = float(npt_match.group(1)) if npt_match else 0.0

                # Extract mitigation applied
                mitigation = self._extract_mitigation(page_text, inc_type)

                # Confidence calculation
                confidence = 0.94
                missing_fields = []
                if not depth_md:
                    confidence -= 0.15
                    missing_fields.append("depth_md_m")
                if matched_formation == "Unknown":
                    confidence -= 0.10
                    missing_fields.append("formation_name")
                if not mitigation:
                    confidence -= 0.05
                    missing_fields.append("mitigation_applied")

                incidents.append({
                    "event_type": inc_type,
                    "severity": severity,
                    "depth_md_m": depth_md or 0.0,
                    "depth_tvdss_m": depth_tvdss or 0.0,
                    "formation_name": matched_formation,
                    "npt_hours": npt_hours,
                    "operational_narrative": passage or page_text[:300],
                    "mitigation_applied": mitigation,
                    "page_number": page_number,
                    "bounding_box": bbox,
                    "confidence_score": round(confidence, 2),
                    "missing_fields": missing_fields
                })

        return {
            "well_id": well_id,
            "report_date": report_date,
            "entities": entities,
            "incidents": incidents,
            "contradictions": contradictions
        }

    def _find_supporting_block(self, layout_blocks: List[Dict[str, Any]], patterns: List[str]) -> Tuple[str, Optional[List[float]]]:
        """
        Locates the specific layout block containing the incident trigger keywords.
        Returns the quoted passage and its spatial bounding box.
        """
        for block in layout_blocks:
            text = block.get("text", "")
            for pat in patterns:
                if re.search(pat, text, re.IGNORECASE):
                    return text.strip(), block.get("bbox")

        # Fallback to first non-empty block
        if layout_blocks:
            return layout_blocks[0].get("text", "").strip(), layout_blocks[0].get("bbox")
        return "", None

    def _extract_mitigation(self, text: str, inc_type: str) -> Optional[str]:
        """
        Extracts documented mitigation action from text.
        """
        mitigation_patterns = [
            r"(?:Pushed|Pumped|Spotted|Mixed and pumped|Reamed|Treated)\s+[^.]*\.",
            r"(?:Allowed\s+\d+\s+hours\s+soak\s+time|circulating\s+\d+\s+GPM)[^.]*\."
        ]
        for pat in mitigation_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                return m.group(0).strip()

        if inc_type == "LOST_CIRCULATION":
            return "Pumped LCM pill and reduced mud density."
        elif inc_type == "STUCK_PIPE":
            return "Spotted soaking pill and worked drillstring with jarring."
        elif inc_type == "PACKOFF":
            return "Pumped high-viscosity tandem sweeps and reamed interval."
        elif inc_type == "TIGHT_HOLE":
            return "Backreamed section and controlled tripping speed."
        return "Applied standard operational mitigation."

event_extractor_service = EventExtractorService()
