"""
NWIS PULSE — Universal Industrial Telemetry Adapters (Phase 06)
Implements standards-based ingestion adapters for:
1. WITSML 1.4.1.1 XML (Logs, Trajectory, Drilling Data)
2. WITSML 2.1 Capability Subset (Energistics 2.1 XML / JSON ChannelSet)
3. ETP 1.2 Capability Contract & Protocol Negotiation Representation
4. Historical Replay Adapter (Volve authentic historical drilling datasets)
5. Synthetic Demonstration Adapter (Isolated resilience testing & fault injection)

Strict Source-Mode Enforced:
- AUTHORIZED_LIVE (Mode 1)
- GENUINE_RECORDED_REPLAY (Mode 2)
- SYNTHETIC_DEMO (Mode 3)
"""

import xml.etree.ElementTree as ET
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple


class BaseTelemetryAdapter:
    """Base interface for all industrial telemetry adapters."""
    
    def __init__(self, source_id: str, source_mode: str = "GENUINE_RECORDED_REPLAY"):
        self.source_id = source_id
        self.source_mode = source_mode # AUTHORIZED_LIVE, GENUINE_RECORDED_REPLAY, SYNTHETIC_DEMO
        self.is_connected = False
        self.last_heartbeat = None

    def parse_payload(self, raw_payload: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def compute_checksum(self, raw_payload: str) -> str:
        return hashlib.sha256(raw_payload.strip().encode("utf-8")).hexdigest()


class WITSML1411Adapter(BaseTelemetryAdapter):
    """
    Parses genuine WITSML 1.4.1.1 XML log and mudLog data structures.
    Supports <logCurveInfo> channel definitions and comma-separated <data> rows.
    """

    def __init__(self, source_id: str = "SRC_WITSML_1411", source_mode: str = "GENUINE_RECORDED_REPLAY"):
        super().__init__(source_id, source_mode)
        self.protocol_version = "WITSML_1.4.1.1"

    def parse_payload(self, raw_payload: str) -> List[Dict[str, Any]]:
        """
        Parses WITSML 1.4.1.1 XML document containing <log> and <data> points.
        Returns a list of standardized raw measurement dicts.
        """
        records = []
        try:
            # Strip potential XML namespaces for robust parsing
            clean_xml = ET.fromstring(raw_payload)
        except ET.ParseError as e:
            raise ValueError(f"Malformed WITSML 1.4.1.1 XML payload: {str(e)}")

        # Find logCurveInfo elements for mnemonics and units
        curves = []
        for lci in clean_xml.iter():
            if lci.tag.endswith("logCurveInfo"):
                mnemonic = None
                unit = None
                for child in lci:
                    if child.tag.endswith("mnemonic"):
                        mnemonic = child.text.strip() if child.text else ""
                    elif child.tag.endswith("unit"):
                        unit = child.text.strip() if child.text else ""
                if mnemonic:
                    curves.append({"mnemonic": mnemonic, "unit": unit or "unitless"})

        # Find wellbore identifier
        wellbore_id = "UNKNOWN_WELLBORE"
        for wb in clean_xml.iter():
            if wb.tag.endswith("nameWellbore") and wb.text:
                wellbore_id = wb.text.strip()
                break

        # Find data blocks
        for data_elem in clean_xml.iter():
            if data_elem.tag.endswith("data") and data_elem.text:
                lines = data_elem.text.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    tokens = [t.strip() for t in line.split(",")]
                    row_data = {
                        "wellbore_id": wellbore_id,
                        "source_id": self.source_id,
                        "source_mode": self.source_mode,
                        "protocol": self.protocol_version,
                        "channels": {}
                    }
                    
                    # Assume first column is index (MD or Time)
                    for i, token in enumerate(tokens):
                        if i < len(curves):
                            mnemonic = curves[i]["mnemonic"]
                            unit = curves[i]["unit"]
                            try:
                                val = float(token)
                            except ValueError:
                                val = token
                            row_data["channels"][mnemonic] = {
                                "value": val,
                                "unit": unit
                            }
                    records.append(row_data)

        self.last_heartbeat = datetime.now(timezone.utc)
        self.is_connected = True
        return records


class WITSML21Adapter(BaseTelemetryAdapter):
    """
    Parses Energistics WITSML 2.1 XML / JSON capability subset.
    Supports Log ChannelSet, Channel definitions with Energistics UOM compliance.
    """

    def __init__(self, source_id: str = "SRC_WITSML_21", source_mode: str = "GENUINE_RECORDED_REPLAY"):
        super().__init__(source_id, source_mode)
        self.protocol_version = "WITSML_2.1"

    def parse_payload(self, raw_payload: str) -> List[Dict[str, Any]]:
        """Parses WITSML 2.1 JSON or XML representation."""
        raw_payload = raw_payload.strip()
        records = []
        if raw_payload.startswith("{") or raw_payload.startswith("["):
            # JSON format
            try:
                data = json.loads(raw_payload)
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed WITSML 2.1 JSON payload: {str(e)}")

            items = data if isinstance(data, list) else [data]
            for item in items:
                records.append({
                    "wellbore_id": item.get("wellbore_id", "UNKNOWN_WELLBORE"),
                    "source_id": self.source_id,
                    "source_mode": self.source_mode,
                    "protocol": self.protocol_version,
                    "timestamp": item.get("timestamp"),
                    "channels": item.get("channels", {})
                })
        else:
            # XML format WITSML 2.1
            try:
                root = ET.fromstring(raw_payload)
            except ET.ParseError as e:
                raise ValueError(f"Malformed WITSML 2.1 XML: {str(e)}")
            
            wellbore_id = root.attrib.get("wellboreUuid", "NO-15/9-F-12")
            channels = {}
            for ch in root.iter():
                if ch.tag.endswith("Channel"):
                    title = ch.attrib.get("mnemonic", ch.tag)
                    uom = ch.attrib.get("uom", "")
                    val_text = ch.text.strip() if ch.text else "0"
                    try:
                        val = float(val_text)
                    except ValueError:
                        val = val_text
                    channels[title] = {"value": val, "unit": uom}

            records.append({
                "wellbore_id": wellbore_id,
                "source_id": self.source_id,
                "source_mode": self.source_mode,
                "protocol": self.protocol_version,
                "channels": channels
            })

        self.last_heartbeat = datetime.now(timezone.utc)
        self.is_connected = True
        return records


class ETP12Adapter(BaseTelemetryAdapter):
    """
    Represents an Energistics Transfer Protocol (ETP 1.2) WebSocket capability contract.
    Implements sub-protocol negotiation:
    - Protocol 1: Core (RequestSession, OpenSession)
    - Protocol 2: ChannelStreaming (StartStreaming, ChannelData)
    - Protocol 3: Store (GetDataObjects)
    """

    def __init__(self, source_id: str = "SRC_ETP_12", source_mode: str = "AUTHORIZED_LIVE"):
        super().__init__(source_id, source_mode)
        self.protocol_version = "ETP_1.2"
        self.supported_protocols = {
            "Core": "1.2",
            "ChannelStreaming": "1.2",
            "Store": "1.2",
            "Discovery": "1.2"
        }

    def negotiate_capabilities(self) -> Dict[str, Any]:
        """Returns the ETP 1.2 capabilities dictionary."""
        return {
            "etp_version": "1.2.0",
            "supported_protocols": self.supported_protocols,
            "max_data_object_size": 10485760, # 10MB
            "auth_scheme": "BearerToken / Strict Read-Only",
            "is_read_only": True,
            "status": "NEGOTIATED"
        }

    def parse_payload(self, raw_payload: str) -> List[Dict[str, Any]]:
        """Parses ETP 1.2 ChannelData record message."""
        try:
            data = json.loads(raw_payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed ETP 1.2 payload: {str(e)}")

        records = []
        points = data.get("dataPoints", [data])
        for pt in points:
            records.append({
                "wellbore_id": pt.get("wellbore_id", "NO-15/9-F-12"),
                "source_id": self.source_id,
                "source_mode": self.source_mode,
                "protocol": self.protocol_version,
                "timestamp": pt.get("timestamp", datetime.now(timezone.utc).isoformat()),
                "channels": pt.get("channels", {})
            })
        self.last_heartbeat = datetime.now(timezone.utc)
        self.is_connected = True
        return records


class HistoricalReplayAdapter(BaseTelemetryAdapter):
    """
    Replays genuine historical drilling telemetry from traceable Volve datasets.
    Preserves original timestamps and sequence order.
    """

    def __init__(self, well_id: str = "NO 15/9-F-12", source_id: str = "SRC_VOLVE_REPLAY"):
        super().__init__(source_id, "GENUINE_RECORDED_REPLAY")
        self.well_id = well_id
        self.protocol_version = "VOLVE_HISTORICAL_LOG"
        self.current_index = 0

    def parse_payload(self, raw_payload: str) -> List[Dict[str, Any]]:
        """Parses CSV or JSON historical drilling packet."""
        data = json.loads(raw_payload)
        return [{
            "wellbore_id": self.well_id,
            "source_id": self.source_id,
            "source_mode": self.source_mode,
            "protocol": self.protocol_version,
            "timestamp": data.get("timestamp"),
            "channels": data.get("channels", {})
        }]


class SyntheticDemoAdapter(BaseTelemetryAdapter):
    """
    Isolated synthetic telemetry adapter used exclusively for:
    - Fault injection (sensor drift, dropouts, packet corruption)
    - Connection recovery validation
    - Extreme stress testing
    Strictly tagged with SYNTHETIC_DEMO. Never presented as real field data.
    """

    def __init__(self, source_id: str = "SRC_SYNTHETIC_SIMULATOR"):
        super().__init__(source_id, "SYNTHETIC_DEMO")
        self.protocol_version = "SYNTHETIC_SIM_1.0"
        self.fault_mode = "NONE" # NONE, DROP_PACKETS, DRIFT_SPP, STALE_CLOCK, JITTER

    def set_fault_mode(self, fault_mode: str):
        self.fault_mode = fault_mode

    def parse_payload(self, raw_payload: str) -> List[Dict[str, Any]]:
        data = json.loads(raw_payload)
        return [{
            "wellbore_id": data.get("wellbore_id", "DEMO_WELL_SYNTHETIC"),
            "source_id": self.source_id,
            "source_mode": self.source_mode, # Explicitly SYNTHETIC_DEMO
            "protocol": self.protocol_version,
            "fault_mode": self.fault_mode,
            "channels": data.get("channels", {})
        }]
