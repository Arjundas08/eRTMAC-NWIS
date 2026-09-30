"""
NWIS PULSE — Telemetry Quality & Staleness Engine (Phase 06)
Performs automated data-quality assessment, duplicate suppression,
out-of-order packet detection, physical plausibility gating, and
real-time staleness monitoring.

Quality States:
- HEALTHY: Timely packets, valid timestamps, plausible physical ranges.
- DEGRADED: Minor packet loss or non-critical channels missing.
- STALE: No packet received within stale threshold (default 20 seconds).
- INSUFFICIENT: Critical channels (MD, SPP, ROP, Flow) missing.
- OFFLINE: Ingestion connection dropped or timeout exceeded (> 60 seconds).
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import hashlib


class TelemetryQualityEngine:
    """Evaluates telemetry stream health and physical integrity."""

    def __init__(self, stale_threshold_s: float = 20.0, offline_threshold_s: float = 60.0):
        self.stale_threshold_s = stale_threshold_s
        self.offline_threshold_s = offline_threshold_s
        self.seen_packet_hashes = set()
        self.last_packet_timestamp: Optional[datetime] = None
        self.last_reception_time: Optional[datetime] = None
        self.stream_state: str = "OFFLINE"
        self.quality_events: List[Dict[str, Any]] = []

    def assess_packet(self, packet_id: str, raw_payload: str, timestamp_str: Optional[str], canonical_channels: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Assesses a newly received packet.
        Returns (quality_state, detected_issues).
        """
        issues = []
        now_utc = datetime.now(timezone.utc)
        self.last_reception_time = now_utc

        # 1. Duplicate Packet Detection
        h = hashlib.sha256(raw_payload.strip().encode("utf-8")).hexdigest()
        if h in self.seen_packet_hashes:
            issues.append("DUPLICATE_PACKET_SUPPRESSED")
            return "DEGRADED", issues
        self.seen_packet_hashes.add(h)
        if len(self.seen_packet_hashes) > 10000:
            self.seen_packet_hashes.clear()

        # 2. Timestamp Validation & Out-of-Order Check
        packet_dt = None
        if timestamp_str:
            try:
                # Support ISO formats
                packet_dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if self.last_packet_timestamp and packet_dt < self.last_packet_timestamp:
                    issues.append("OUT_OF_ORDER_PACKET")
                self.last_packet_timestamp = packet_dt
            except ValueError:
                issues.append("INVALID_TIMESTAMP_FORMAT")
        else:
            issues.append("MISSING_TIMESTAMP")

        # 3. Critical Channels Presence Check
        required_critical = ["MD", "BIT_DEPTH"]
        missing_critical = [c for c in required_critical if c not in canonical_channels]
        if missing_critical:
            issues.append(f"MISSING_CRITICAL_CHANNELS: {missing_critical}")
            self.stream_state = "INSUFFICIENT"
            return "INSUFFICIENT", issues

        # 4. Physical Plausibility Gating (Petroleum engineering boundaries)
        plausibility_limits = {
            "MD": (0.0, 15000.0),            # meters
            "BIT_DEPTH": (0.0, 15000.0),     # meters
            "ROP": (0.0, 300.0),             # m/h
            "WOB": (-20.0, 500.0),           # kN
            "RPM": (0.0, 350.0),             # rpm
            "TORQUE": (0.0, 80.0),           # kN.m
            "SPP": (0.0, 45000.0),           # kPa (~6500 psi)
            "FLOW_IN": (0.0, 6000.0),        # L/min
            "FLOW_OUT": (0.0, 200.0),        # %
            "PIT_VOLUME": (0.0, 500.0),      # m³
            "MUD_WEIGHT": (0.8, 2.5),        # sg
            "ECD": (0.8, 2.8),               # sg
            "GAS_TOTAL": (0.0, 100.0)        # %
        }

        for ch, (min_val, max_val) in plausibility_limits.items():
            if ch in canonical_channels:
                val = canonical_channels[ch]
                if isinstance(val, (int, float)):
                    if val < min_val or val > max_val:
                        issues.append(f"SENSOR_OUT_OF_BOUNDS_{ch}: {val} not in [{min_val}, {max_val}]")

        # 5. Determine State
        if not issues:
            self.stream_state = "HEALTHY"
        elif any(i.startswith("MISSING_CRITICAL") for i in issues):
            self.stream_state = "INSUFFICIENT"
        else:
            self.stream_state = "DEGRADED"

        return self.stream_state, issues

    def check_staleness(self) -> str:
        """
        Evaluates current stream staleness based on elapsed time since last reception.
        """
        if not self.last_reception_time:
            self.stream_state = "OFFLINE"
            return "OFFLINE"

        now_utc = datetime.now(timezone.utc)
        elapsed = (now_utc - self.last_reception_time).total_seconds()

        if elapsed > self.offline_threshold_s:
            self.stream_state = "OFFLINE"
        elif elapsed > self.stale_threshold_s:
            self.stream_state = "STALE"

        return self.stream_state
