# NWIS PULSE — INDUSTRIAL DATA QUALITY & TRANSPARENCY
**Phase:** 06 — Industrial Drilling Telemetry & Integration  
**Standard:** SIH26121 Section 6 & 15  
**Status:** IMPLEMENTED & VERIFIED  

---

## 1. Data Quality Hierarchy

NWIS PULSE classifies telemetry stream health into five operational states:

| Quality State | Criteria | Operational Meaning | Action Required |
|---|---|---|---|
| `HEALTHY` | Timely arrival ($< 15\,\text{s}$), valid ISO timestamps, all critical channels present, physical values within sanity limits. | Stream is high-fidelity and fully trusted. | Advisory engine active. |
| `DEGRADED` | Non-critical sensor missing, duplicate packet suppressed, or single minor outlier. | Partial telemetry available. | Display amber badge; compute available rules. |
| `STALE` | No packet received within staleness threshold ($> 20\,\text{s}$). | Stream frozen or telemetry transmission delayed. | Invalidate real-time alarms; alert operator. |
| `INSUFFICIENT` | Missing critical channels (MD, Bit Depth, SPP, Flow). | Telemetry insufficient for safety analysis. | **Abstain from advisory generation.** |
| `OFFLINE` | No packet received for $> 60\,\text{s}$ or connection reset. | Ingestion stream completely disconnected. | Alert control room; preserve last valid state. |

---

## 2. Integrity Checks & Defense Mechanisms

### 2.1 Cryptographic Duplicate Suppression
Every raw packet is hashed using SHA-256 upon arrival. If the hash has been processed within the rolling cache window ($10,000$ packets), the packet is flagged as `DUPLICATE_PACKET_SUPPRESSED`, stored in the raw table for provenance, and prevented from causing duplicate advisory evaluations.

### 2.2 Out-of-Order Packet Handling
Packets arriving with timestamps earlier than the current monotonic high-water mark are tagged as `OUT_OF_ORDER_PACKET` and routed into the re-sequencing buffer to ensure historical trends remain strictly monotonic.

### 2.3 Physical Bounds Gating
Before measurements enter mathematical models or advisory rules, they must pass physical sanity boundaries established by senior petroleum engineers:
- Mud Weight: $0.80 - 2.50\,\text{sg}$
- RPM: $0 - 350\,\text{rpm}$
- Torque: $0 - 80\,\text{kN}\cdot\text{m}$
- SPP: $0 - 45,000\,\text{kPa}$
- Flow Out: $0 - 200\,\%$

Sensors reporting values outside these credible boundaries trigger `SENSOR_OUT_OF_BOUNDS` quality events and are excluded from kick/loss algorithms.

---

## 3. Telemetry Transparency Inspector

Available at `/api/v1/pulse/quality-inspector/{wellbore_id}` and rendered interactively in the PULSE Command Centre:
- Channel mnemonic & human-readable sensor name.
- Sensor hardware type (Drawworks encoder, Coriolis densitometer, Ultrasonic pit sensor).
- Current sampling frequency (e.g., $1.0\,\text{s}$, $2.0\,\text{s}$, $5.0\,\text{s}$).
- Freshness lag timer (seconds elapsed since last sensor measurement).
- Data quality flag (`HEALTHY`, `CALCULATED`, `DEGRADED`).
