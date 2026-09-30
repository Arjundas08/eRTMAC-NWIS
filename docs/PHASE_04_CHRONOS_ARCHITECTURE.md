# NWIS CHRONOS: SYSTEM ARCHITECTURE SPECIFICATION
**System Subsystem:** Production-Oriented Historical Replay Laboratory & Independent Validation Engine  
**Target Environment:** Oil India Limited eRTMAC Integration Testbed  
**Document Revision:** 4.0.0-PROD  
**Security Standard:** Strict Point-in-Time Cryptographic Knowledge Isolation  

---

## 1. High-Level Subsystem Architecture

NWIS Chronos operates as an authoritative, reproducible historical drilling replay and validation subsystem adjacent to Oil India Limited's Real-Time Monitoring and Control (eRTMAC) environment.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NWIS CHRONOS ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
     ┌─────────────────────────────────┼─────────────────────────────────┐
     ▼                                 ▼                                 ▼
┌────────────────────────┐   ┌────────────────────────┐   ┌────────────────────────┐
│  REPLAY ELIGIBILITY    │   │  POINT-IN-TIME         │   │  REPRODUCIBLE REPLAY   │
│  REGISTRY              │   │  EVIDENCE FIREWALL     │   │  ENGINE                │
│                        │   │                        │   │                        │
│ - Depth-Indexed        │   │ - Cutoff Timestamp     │   │ - Trajectory Interp.   │
│ - Time-Indexed         │   │ - Offset Isolation     │   │ - Look-Ahead Scanner   │
│ - Daily Report Recons. │   │ - SHA-256 Memory Hash  │   │ - Live Telemetry Stream│
│ - Retrospective Only   │   │ - Transparency Report  │   │ - Event Jump Engine    │
└────────────────────────┘   └────────────────────────┘   └────────────────────────┘
     │                                 │                                 │
     └─────────────────────────────────┼─────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      MULTI-LAYER ADVISORY ENGINE                                │
│                                                                                 │
│   Layer A: Historical Exposure (Stratigraphically Correlated Prior Incidents)  │
│   Layer B: Engineering Rules (Hydrostatic Balance, Fracture Gradient, Margin)   │
│   Layer C: Validated Statistical Models (Disabled unless calibrated)            │
└─────────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   INDEPENDENT EVALUATION & LOWO BENCHMARK                       │
│                                                                                 │
│   - Chronological Leave-One-Well-Out (LOWO) Back-Testing Framework              │
│   - Ground-Truth Air Gap (Zero visibility during advisory generation)           │
│   - Fair 3-Way Baseline Comparison (Proximity vs Formation vs GeoCore+Chronos)   │
│   - False Alarm Accounting & Early Warning Lead-Distance Measurement            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Point-in-Time Evidence Firewall (Signature Innovation 01)

The Point-in-Time Evidence Firewall enforces the fundamental epistemological rule:
> **"What did the system know at the time?"**

### 2.1 Firewall Guarantees
1. **Target Well Exclusion:** The target wellbore being evaluated is completely excluded from historical analogue candidate pools.
2. **Post-Spud Temporal Quarantine:** Any wellbore spudded after the target well's historical evaluation timestamp is completely invisible.
3. **Document Ingestion Cutoff:** Only daily drilling reports, well completion reports, and wireline logs with verified publication timestamps strictly prior to the cutoff date are loaded.
4. **Cryptographic Reproducibility:** Every replay session generates an immutable SHA-256 hash of its frozen knowledge manifest:
   $$\text{Hash} = \text{SHA256}(\text{TargetWell} \parallel \text{CutoffTimestamp} \parallel \text{Offsets} \parallel \text{DocHashes})$$

### 2.2 Transparency Audit: "What the Engineer Could Have Known"
The firewall provides full transparency through `/api/v1/chronos/transparency`:
* Explicit list of accessible prior offset wells.
* Explicit list of strictly excluded future wells with justification (e.g., *"Spud date 2009-01-20 is in the future relative to replay date 2008-08-02"*).
* Inventory of accessible prior verified events.

---

## 3. Replay-Eligibility Registry

Historical wellbores exhibit varying degrees of data completeness. NWIS Chronos implements an explicit eligibility registry:

```
                                WELLBORE AUDIT
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
        Spud & Completion Certified?            Missing Dates/Picks?
                   │                                     │
         ┌─────────┴─────────┐                           ▼
        YES                  NO                  [INSUFFICIENT_DATA]
         │                   │
         ▼                   ▼
Prior Offsets Exist?    [RETROSPECTIVE_ONLY]
         │              (Pioneer Wellbore)
   ┌─────┴─────┐
  YES          NO
   │
   ▼
Definitive Directional Survey (>= 4 stations)?
   │
   ├─► YES: [DEPTH_INDEXED] (Full Continuous Replay Capable)
   └─► NO:  [DAILY_REPORT_RECONSTRUCTION] (Shift-Level Only)
```

---

## 4. Chronos Replay Engine

### 4.1 Trajectory Interpolation & Depth Referencing
At each replay step, the bit position $(MD)$ is transformed to true vertical depth $(TVD)$ and subsea reference $(TVDSS)$ using analytical Minimum Curvature interpolation:

$$DL = 2 \arcsin \sqrt{\sin^2\left(\frac{I_2 - I_1}{2}\right) + \sin(I_1)\sin(I_2)\sin^2\left(\frac{A_2 - A_1}{2}\right)}$$

$$RF = \frac{2}{DL} \tan\left(\frac{DL}{2}\right)$$

$$TVDSS = TVD - \text{KB\_Elevation}$$

### 4.2 Look-Ahead Horizon Scanning
As the bit advances along the trajectory, Chronos projects a user-configurable look-ahead horizon $\Delta Z_{\text{lookahead}}$ (default: 100 meters TVDSS):
$$Z_{\text{target}} \in [TVDSS_{\text{bit}}, TVDSS_{\text{bit}} + \Delta Z_{\text{lookahead}}]$$

Prior verified incidents falling within this geological corridor in eligible prior offset wells are evaluated for stratigraphic relevance and structural correlation.

---

## 5. Multi-Layer Advisory Engine

Advisories generated by NWIS Chronos are strictly structured into three decoupled layers:

* **Layer A (Historical Exposure):** Reports documented offset incidents occurring in the correlated stratigraphic formation within the look-ahead window.
* **Layer B (Engineering Rules):** Evaluates physical drilling limits (e.g., equivalent circulating density exceeding pore-pressure margin or sudden torque escalation).
* **Layer C (Statistical Models):** Disabled by default. Only enabled when a machine-learning model has been calibrated and independently validated on ground-truth training datasets.
* **Language Model Guardrail:** LLMs are strictly prohibited from hallucinating drilling hazards or creating synthetic thresholds. LLM functionality is restricted to summarizing certified evidence.

---

## 6. Database Entity-Relationship Model

The PostgreSQL/PostGIS database is extended with eight dedicated Chronos tables:

1. `replay_sessions`: Active and archived replay executions with status, current depth, and snapshot linkage.
2. `replay_eligibility`: Wellbore suitability classification tiers and audit criteria.
3. `historical_memory_snapshots`: Frozen point-in-time knowledge snapshots with cryptographic checksums.
4. `replay_packets`: High-frequency and depth-indexed historical telemetry records.
5. `ground_truth_events`: Independently adjudicated historical incidents isolated from replay advisory generators.
6. `advisory_events`: Generated historical look-ahead advisories with lead distance accounting.
7. `advisory_evidence`: Cryptographic links binding advisories to source documents and offset wellbores.
8. `evaluation_runs`: Comprehensive Leave-One-Well-Out back-testing metric runs.
