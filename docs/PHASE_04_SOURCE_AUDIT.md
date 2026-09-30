# NWIS CHRONOS: PHASE 4 HISTORICAL SOURCE DATA & PROVENANCE AUDIT
**Subsystem:** NWIS Chronos Historical Replay Laboratory  
**Operator Evaluation Target:** Oil India Limited (eRTMAC Adjacent Subsystem)  
**Historical Dataset:** Equinor Volve Field (North Sea Block 15/9, Licence PL 046)  
**Audit Standard:** Strict Point-in-Time Temporal Causality & Evidence Provenance  
**Date of Audit:** September 2026

---

## 1. Executive Summary & Audit Mandate

During Stage Zero of Phase 4 implementation, an exhaustive provenance and data-integrity audit was executed across all wellbores, directional surveys, formation tops, daily drilling reports (DDRs), and historical incident labels in the NWIS knowledge repository.

The primary objective was to eliminate any risk of **temporal data leakage** (using future records to predict past events) and **synthetic contamination** (mixing ReportLab demonstration fixtures with authentic operator ground truth).

---

## 2. Adjudicated Source Classification Standards

Every historical record ingested into NWIS Chronos is assigned one of six immutable provenance tiers:

| Tier Code | Classification Name | Permitted in Prospective Replay? | Permitted in Retrospective Discovery? | Description |
|:---|:---|:---:|:---:|:---|
| `ORIGINAL_VERIFIED` | Primary Operator Record | **YES** (if prior to cutoff) | **YES** | Unaltered Equinor/NOD official logs, directional surveys, daily drilling reports. |
| `DERIVED_FROM_VERIFIED_SOURCE` | Normalized Analytical Output | **YES** (if prior to cutoff) | **YES** | Deterministic Minimum Curvature TVDSS calculations, stratigraphic interpolations. |
| `RECONSTRUCTED_FIXTURE` | Historical Synthetic Fixture | **NO** (Strictly Quarantined) | Retrospective Demo Only | ReportLab demonstration PDFs reconstructed for OCR pipeline testing. |
| `SYNTHETIC_FIXTURE` | Parametric Test Vector | **NO** (Strictly Quarantined) | CI/CD Unit Tests Only | Mathematical unit test mocks for edge cases and exception handling. |
| `UNVERIFIED` | Pending Review Record | **NO** | Flagged | Records awaiting secondary engineer adjudication. |
| `REJECTED` | Incompatible / Tainted Record | **NO** | **NO** | Corrupted datums, mismatched wellbore IDs, or uncalibrated timestamps. |

---

## 3. Detailed Field Timeline & Causality Ledger

The Volve field development followed a strict chronological sequence from exploration (1993) to decommissioning (2016). Drilling operations relevant to NWIS Chronos occurred between 2006 and 2009:

```
[1993-02-14] 15/9-19 SR (Discovery Well)
       │
[2006-05-15] NO-15/9-F-1 (Pioneer Well, Vertical, 3210m TD)
       │       └── REPLAY TIER: RETROSPECTIVE_ONLY (Zero prior offsets in field)
       │
[2007-08-20] NO-15/9-F-4 (Production Well, 3420m TD)
       │       └── REPLAY TIER: DEPTH_INDEXED (Prior offset: F-1)
       │
[2008-04-10] NO-15/9-F-12 Spud Date
       │       └── Severe Lost Circulation encountered in Hugin FM (2910m MD) on May 18, 2008
       │       └── Completed: 2008-07-28 (TD: 3415m MD)
       │
[2008-08-02] NO-15/9-F-14 Spud Date  <--- [CHRONOS TARGET EVALUATION POINT]
       │       └── FIREWALL FROZEN AT: 2008-08-02T00:00:00
       │       └── ACCESSIBLE OFFSETS: F-1, F-4, F-12
       │       └── EXCLUDED OFFSETS: F-15S (Drilled Jan 2009)
       │       └── Real Event: Lost Circulation in Hugin FM at 2965m MD (42 bbl/hr)
       │
[2009-01-20] NO-15/9-F-15S Spud Date
               └── STRONGLY EXCLUDED from F-14 historical memory by Point-in-Time Firewall.
```

---

## 4. Specific Audit Findings & Remediations

### Finding A: Analogue Temporal Inversion in Previous Demonstrations
* **Observation:** Early Phase 3 similarity demonstrations displayed F-15S as a candidate analogue for F-12.
* **Audit Determination:** F-12 was drilled from April to July 2008. F-15S was spudded on January 20, 2009. F-15S did not physically exist when F-12 was being drilled.
* **Remediation Implemented:** The Point-in-Time Evidence Firewall (`backend/app/services/chronos_firewall.py`) now dynamically excludes any wellbore with `spud_date >= evaluation_cutoff`. When replaying F-12, F-15S is permanently invisible to the candidate selection engine.

### Finding B: Segregation of ReportLab Reconstructed Fixtures
* **Observation:** During Phase 2 document pipeline testing, several demonstration PDFs (`DDR_F14_Demo.pdf`) were generated locally using ReportLab.
* **Audit Determination:** Demonstration PDFs must never enter the authentic empirical benchmark as genuine operator evidence.
* **Remediation Implemented:** Demonstration files are tagged `provenance_tier: RECONSTRUCTED_FIXTURE`. In `ChronosEvaluationService`, SQL queries filter strictly for `verification_status IN ('VERIFIED', 'ORIGINAL_VERIFIED')`.

### Finding C: Rotary Kelly Bushing (KB) Elevation Audit
* **Observation:** A flat 43.5 m KB elevation was previously referenced across all wellbores.
* **Audit Determination:** In offshore drilling, different jack-up rigs (e.g., Mærsk Inspirer) and drilling phases can have minor KB datum variations.
* **Remediation Implemented:** Every wellbore survey and formation top stores its individual `kb_elevation_m`. TVDSS calculations use each well's certified datum (`TVDSS = TVD - Well.kb_elevation_m`).

---

## 5. Audit Conclusion

The NWIS Chronos data repository conforms strictly to historical causality and engineering data-isolation standards. All evaluations reported in subsequent documents derive exclusively from verified historical sources under point-in-time cryptographic constraints.
