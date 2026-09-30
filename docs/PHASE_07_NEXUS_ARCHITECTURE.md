# NWIS NEXUS — Unified Operations Command Center Architecture (Phase 07)
## eRTMAC Platform — Real-Time Monitoring & Advisory Center for Oil India Limited

**Author:** Industrial Integration Architect & Principal Drilling Systems Engineer  
**Date:** 2026-09-30  
**Status:** IMPLEMENTED & OPERATIONAL  
**Target:** Production Command Center Deployment  

---

## 1. Executive Summary

NWIS NEXUS (Nearby Wells Intelligence System — Unified Operations Command Center) serves as the apex operational tier of the eRTMAC platform. It synthesizes and orchestrates the distributed outputs of:
1. **NWIS GeoCore (Phase 03):** 3D stratigraphy, TVDSS normalization, Minimum Curvature wellbore trajectories, and 4-tier explainable analogue similarity.
2. **NWIS Chronos (Phase 04):** Temporal firewall-enforced time-machine replay, pre-spud what-if branching, and counterfactual mitigation validation.
3. **NWIS Sentinel (Phase 05):** Strict Evidence-or-Silence hybrid RAG retrieval, citation graph validation, and prompt injection defense.
4. **NWIS Pulse (Phase 06):** Real-time WITSML 1.4.1.1/2.1 and ETP 1.2 telemetry ingestion, data quality quarantine, and live formation boundary look-ahead.
5. **Document AI & Core NWIS (Phases 01–02):** DDR/WCR extraction, SHA-256 evidence passports, offset radar, and LOWO back-testing.

NEXUS eliminates the operational fragmentation inherent in multi-dashboard monitoring by unifying all intelligence vectors into a single coherent, explainable, and deterministic operational picture.

```
                           +----------------------------------------+
                           |       NWIS NEXUS COMMAND CENTER        |
                           |   (Unified Web Dashboard & API v1)    |
                           +-------------------+--------------------+
                                               |
                     +-------------------------+-------------------------+
                     |                         |                         |
          +----------v----------+   +----------v----------+   +----------v----------+
          |  SYSTEM HEALTH &    |   | INTELLIGENCE FUSION |   |  OPERATIONS LOG &   |
          |  MODULE STATUS      |   |   & RISK SCORING    |   |  SHIFT HANDOVER     |
          +----------+----------+   +----------+----------+   +----------+----------+
                     |                         |                         |
                     +-------------------------+-------------------------+
                                               |
     +-------------------+---------------------+-------------------+-------------------+
     |                   |                     |                   |                   |
+----v-----+       +-----v----+          +-----v----+        +-----v----+        +-----v----+
| GeoCore  |       | Chronos  |          | Sentinel |        |  Pulse   |        | Document |
| Engine   |       | Time-Mac |          | RAG Gate |        | Telemet. |        | AI Engine|
+----------+       +----------+          +----------+        +----------+        +----------+
```

---

## 2. Core Architectural Pillars

### 2.1 Unified System Health Aggregation
The NEXUS Health Engine queries the operational health of each subsystem via a non-blocking diagnostic pass:
- **GeoCore:** Validates trajectory interpolators, formation horizon models, and similarity index caches.
- **Chronos:** Checks temporal firewall integrity, replay session states, and branch tree memory.
- **Sentinel:** Verifies vector database readiness, prompt injection shield status, and evidence contract enforcement.
- **Pulse:** Evaluates live stream status, adapter connection health, and data quality quarantine event counts.
- **Document AI:** Confirms OCR engine status, PDF parser availability, and SHA-256 hash store.

The global status is resolved deterministically:
- `OPERATIONAL`: All critical subsystems report operational health with 0 critical alarms.
- `DEGRADED`: One or more optional subsystems report latency warnings or non-critical quality anomalies.
- `OFFLINE`: Core database or essential telemetry ingestion is unreachable.

### 2.2 Explainable Cross-Module Intelligence Fusion
For any target wellbore, the `fuse_well_intelligence()` engine performs multi-dimensional synthesis:
1. **Geological Layer:** Current TVDSS depth, penetrated formation, formation boundary distance, and offset similarity rankings from GeoCore.
2. **Telemetry Layer:** Normalized instantaneous parameters (ROP, WOB, RPM, SPP, Torque, Pit Volume, Gas, ECD) and data quality state from Pulse.
3. **Hazard Layer:** Active operational advisories, look-ahead pre-bit warnings, and historical incident matches within +/-150m TVDSS window.
4. **Knowledge Layer:** Verified document evidence passports, geological fingerprint citations, and operator handover notes from Sentinel.
5. **Simulation Layer:** Active Chronos replay session or counterfactual branch trajectory.

Every fused intelligence packet contains an immutable SHA-256 integrity hash:
$$\text{Hash} = \text{SHA256}(\text{WellID} \parallel \text{Timestamp} \parallel \text{TVDSS} \parallel \text{ActiveAdvisories} \parallel \text{DQState})$$

### 2.3 Deterministic Operational Risk Scoring
Drilling risk is quantified using an open, non-black-box weighted composite formula:

$$R_{\text{total}} = \min\left(100, \; w_a R_a + w_g R_g + w_t R_t + w_q R_q\right)$$

Where:
- $R_a$: Active Advisory Risk (Critical advisory = 40 pts, Warning = 20 pts, Caution = 10 pts).
- $R_g$: Geological Hazard Proximity Risk (approaching fault or unconformity within 50m = up to 30 pts).
- $R_t$: Telemetry Delta Risk (WOB/Torque/SPP deviation from offset baseline = up to 20 pts).
- $R_q$: Data Quality Penalty (Stale data = 15 pts, Degraded = 10 pts).

Risk classifications:
- **0–24:** `LOW` (Green) — Nominal drilling parameters, no offset hazards.
- **25–49:** `MODERATE` (Amber) — Geological boundary transition or minor baseline divergence.
- **50–74:** `ELEVATED` (Orange) — Verified offset incident within 100m TVDSS or active advisory.
- **75–100:** `CRITICAL` (Red) — Active kick, severe mud loss, or packoff indicators with offset precedent.

### 2.4 Operations Log & Shift Handover Audit
NEXUS unifies all human and machine operational events into an append-only chronological log:
- Advisory generation, acknowledgment, and resolution.
- Driller feedback inputs and parameter adjustments.
- Data quality state transitions (e.g., sensor failure, quarantine entry).
- Shift supervisor handover notes and sign-offs.

Every entry records: `timestamp`, `well_id`, `event_type`, `severity`, `author_role`, `details`, and `parent_hash`.

### 2.5 Multi-Well Comparative Matrix
Enables operations superintendents to compare multiple wells simultaneously across:
- Trajectory progress (MD, TVD, Inclination, Azimuth).
- Geological interval penetration.
- NPT (Non-Productive Time) incident density.
- Active advisory burden and data stream freshness.

---

## 3. API Contract & Endpoint Specification

| Endpoint | Method | Response Model | Description |
|---|---|---|---|
| `/api/v1/nexus/health` | GET | `SystemHealthResponse` | Aggregated subsystem operational health |
| `/api/v1/nexus/kpis` | GET | `KPIMetricsResponse` | Enterprise operational KPIs and uptime |
| `/api/v1/nexus/operations-log` | GET | `OperationsLogResponse` | Append-only shift handover & audit trail |
| `/api/v1/nexus/fuse/{well_id:path}` | GET | `FusedIntelligenceResponse` | Deep intelligence fusion across all modules |
| `/api/v1/nexus/compare` | POST | `MultiWellComparisonResponse`| Multi-well comparative benchmarking |
| `/api/v1/nexus/timeline` | GET | `AlertTimelineResponse` | Chronological severity-graded alert sequence |
| `/api/v1/nexus/summary` | GET | `LandingSummaryResponse` | Executive summary for high-level monitoring |
| `/app/nexus` | GET | Redirect (`/nexus.html`) | Single-command access to NEXUS Web UI |

---

## 4. Safety & Governance Boundary

1. **Read-Only Supervisory Command:** NEXUS does not write setpoints to rig control PLCs. All actions are human-in-the-loop advisories.
2. **Evidence-or-Silence:** Fused recommendations require verifiable historical citations or validated physical sensor evidence.
3. **Traceability:** Shift handover logs and risk score snapshots are cryptographically hashed to prevent post-incident tampering.
