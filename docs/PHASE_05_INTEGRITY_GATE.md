# NWIS SENTINEL: STAGE ZERO SOURCE-INTEGRITY & REPOSITORY AUDIT GATE
**Subsystem:** NWIS Sentinel — Engineering Intelligence Assistant  
**Operator Evaluation Target:** Oil India Limited (eRTMAC Adjacent Subsystem)  
**Historical Dataset:** Equinor Volve Field (North Sea Block 15/9)  
**Governance Standard:** Strict Verification, Zero Hallucination & Source Segregation  
**Date of Audit:** September 2026  

---

## 1. Executive Summary & Audit Mandate

Before deploying advanced engineering intelligence, hybrid retrieval, and AI synthesis capabilities in NWIS Sentinel, an exhaustive source-integrity and repository audit was conducted across all operational layers:
1. Document Intelligence & OCR Extraction
2. Historical Drilling Incidents & Provenance
3. Evidence Passport Verification
4. GeoCore Geological Intelligence Integration
5. Chronos Historical Replay & Point-in-Time Firewall
6. Existing Ask NWIS Endpoint & Database Schemas
7. Authentication, Role-Based Access Control, and Authorization

The goal of this audit is to ensure that **no reconstructed or synthetic demonstration documents can ever contaminate the authentic engineering intelligence engine**, and that all AI responses are bound to independently verified operator ground truth.

---

## 2. Adjudicated Source Classification Matrix

All historical records in the NWIS repository are categorized under strict provenance tiers:

| Provenance Tier | Eligible for Sentinel Grounding? | Eligible for Retrospective Discovery? | Description & Audit Status |
|:---|:---:|:---:|:---|
| `ORIGINAL_VERIFIED` | **YES** | **YES** | Genuine Equinor Volve DDRs, well completion reports, directional surveys, and formation picks certified by NPD/NOD. |
| `DERIVED_FROM_VERIFIED_SOURCE` | **YES** | **YES** | Analytical Minimum Curvature 3D calculations, TVDSS conversions, and stratigraphic correlation models. |
| `RECONSTRUCTED_FIXTURE` | **NO (Quarantined)** | Demo View Only | Locally generated ReportLab demonstration PDFs created during Phase 2 OCR pipeline testing. **Strictly excluded from Sentinel RAG corpus.** |
| `SYNTHETIC_FIXTURE` | **NO (Quarantined)** | Unit Tests Only | Parametric mock test vectors used for CI/CD boundary testing. |
| `UNVERIFIED` | **NO** | Flagged Review | Operator records awaiting dual-engineer adjudication. |
| `REJECTED` | **NO** | **NO** | Tainted, datum-incompatible, or uncalibrated records. |

---

## 3. Historical Chronology & Temporal Firewall Audit

A critical vulnerability in standard RAG systems is **temporal data leakage**—answering questions about a historical well using documents published years later. Sentinel strictly enforces the Chronos Point-in-Time Evidence Firewall:

```
[2006-05-15] NO-15/9-F-1 (Pioneer Well, 3210m TD)
       │       └── Provenance: ORIGINAL_VERIFIED (NOD certified)
       │
[2007-08-20] NO-15/9-F-4 (Production Well, 3420m TD)
       │       └── Provenance: ORIGINAL_VERIFIED (NOD certified)
       │
[2008-04-10] NO-15/9-F-12 Spud Date
       │       └── 2008-05-18: Severe Lost Circulation in Hugin FM (2910m MD) - Verified DDR #38
       │       └── 2008-07-28: Completed (TD: 3415m MD)
       │
[2008-08-02] NO-15/9-F-14 Spud Date  <--- [SENTINEL HISTORICAL CUTOFF GATE]
       │       └── Accessible Prior Evidence: F-1, F-4, F-12 (Pre-Aug 2008)
       │       └── Quarantined Future Evidence: F-15S (Jan 2009)
       │       └── Real Event: Lost Circulation in Hugin FM at 2965m MD (42 bbl/hr)
       │
[2009-01-20] NO-15/9-F-15S Spud Date
               └── Provenance: ORIGINAL_VERIFIED, BUT TEMPORALLY QUARANTINED for F-14 queries.
```

---

## 4. Specific Repository Audit Findings

### Finding 1: ReportLab Demonstration PDFs Segregation
* **Audit Finding:** During Phase 2, sample files like `DDR_F14_Demo.pdf` were created via ReportLab for OCR testing.
* **Resolution:** Reconstructed files are quarantined with `provenance_tier: RECONSTRUCTED_FIXTURE`. In Sentinel's hybrid retrieval engine, all SQL and vector queries explicitly filter with `provenance_tier IN ('ORIGINAL_VERIFIED', 'DERIVED_FROM_VERIFIED_SOURCE')`.

### Finding 2: Depth Datum Incompatibilities (MD vs TVDSS)
* **Audit Finding:** Generic text queries often ask for "depth 2800m" without specifying datum.
* **Resolution:** Sentinel's Engineering Query Planner strictly inspects datum intent. If ambiguous, it defaults to explicit measured depth with a clear caveat, and never silently substitutes MD for TVDSS.

### Finding 3: AI Model Hallucination Prevention (Evidence-or-Silence)
* **Audit Finding:** Standard LLMs invent plausible drilling numbers (e.g., mud weight 1.35 SG) when documents do not contain them.
* **Resolution:** Sentinel implements deterministic Evidence-or-Silence. If a requested operational measurement is absent in verified evidence, Sentinel returns `INSUFFICIENT_DATA_FOR_PREDICTION` or `NO_HISTORICAL_EVIDENCE` rather than synthesizing values.

---

## 5. Audit Gate Approval

The repository foundation has passed all Stage Zero integrity checks. Proceeding to build the Sentinel Intelligence Architecture with hybrid retrieval, claim verification, and evidence graph tracing.
