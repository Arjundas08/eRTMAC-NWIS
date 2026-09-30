# eRTMAC-NWIS — Phase 1 Repository Audit
**Document ID:** AUDIT-PHASE01-2026-09-29  
**Evaluation Standard:** Production Readiness, Geological Validity & Data Provenance  
**Auditor Roles:** Principal Software Architect, Senior Petroleum Data Engineer, Drilling Specialist, Geological Specialist, ML Validation Engineer, Industrial Cybersecurity Engineer, QA Engineer  

---

## 1. Executive Summary

This audit independently reviews the initial Phase 1 implementation of `eRTMAC-NWIS` located at:
`C:\Users\DELL\.gemini\antigravity-ide\scratch\ertmac-nwis`

### Key Audit Findings:
1. **Critical Flaw Detected (Temporal Leakage in Back-Test):** The previously reported Leave-One-Well-Out (LOWO) back-test evaluated held-out well `NO-15/9-F-12` (drilled April–July 2008) against historical offset incidents from `NO-15/9-F-14` (drilled August–November 2008) and `NO-15/9-F-15S` (drilled January–May 2009). The retrieval query filtered only by `well_id != active_well_id` without an `as_of_timestamp` cutoff. **This constitutes future-information leakage.** The claimed 66.7% recall for F-12 was invalid because the system looked forward into future wells that had not yet been spudded.
2. **Geological Integrity:** Stratigraphic depth conversion (TVDSS = TVD - KB) and Minimum Curvature math are mathematically sound. However, the system lacked a strict fail-safe check to reject incompatible or missing vertical datums with an explicit `INSUFFICIENT_GEOLOGICAL_EVIDENCE` status.
3. **Data Provenance:** The 5 wells, 35 surveys, 34 formation tops, and 10 DDR incidents represent genuine historical Volve field records. However, a machine-readable provenance manifest detailing official NPD/Equinor download URLs, licensing text, and extraction methods was missing.
4. **Backend Architecture:** FastAPI structure, Pydantic v2 schemas, SQLAlchemy models, and dual SQLite/PostgreSQL abstractions are well-engineered, modular, and functional.
5. **Averaging Inconsistency:** The reported 45.1m lead distance resulted from averaging across multiple continuous depth step warnings rather than reporting exact first-horizon detection lead distances.

---

## 2. Component-by-Component Classification

Every subsystem is classified into one of five rigorous engineering categories:
- **`[VERIFIED]`**: Code and data independently checked, tested, and verified to be correct.
- **`[IMPLEMENTED BUT UNVALIDATED]`**: Code functions mechanically but requires empirical/field calibration.
- **`[INCOMPLETE]`**: Code exists in part but lacks essential edge-case or production features.
- **`[INCORRECT]`**: Implementation contains conceptual, chronological, or mathematical flaws that must be repaired.
- **`[NOT IMPLEMENTED]`**: Planned capabilities not yet written.

```
┌──────────────────────────────────────┬───────────────────────────────┬───────────────────────────────────────────┐
│ Component / Subsystem                │ Audit Classification          │ Findings & Required Remediation           │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 1. Backend Microservices (FastAPI)   │ VERIFIED                      │ Clean routing, CORS, typed endpoints,     │
│                                      │                               │ dual-engine database session management.  │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 2. Dual Database Engine              │ VERIFIED                      │ SQLite local mode functional; PostgreSQL  │
│                                      │                               │ DDL schema fully specified in SQL files.  │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 3. Raw Volve Source Datasets         │ IMPLEMENTED BUT UNVALIDATED   │ Real data present, but lacked machine-    │
│                                      │                               │ readable provenance manifest & URLs.      │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 4. Data Ingestion Scripts            │ VERIFIED                      │ Ingests headers, surveys, tops, events;   │
│                                      │                               │ SHA-256 checks verified on disk.          │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 5. Stratigraphic Math (TVDSS/MinCurv)│ VERIFIED                      │ Minimum curvature & TVDSS math correct;   │
│                                      │                               │ lacks explicit missing-datum exception.   │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 6. Offset Well Similarity Algorithm  │ IMPLEMENTED BUT UNVALIDATED   │ Explainable weighted formulation working; │
│                                      │                               │ needs baseline comparison vs geo-only.    │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 7. Look-Ahead Horizon Engine         │ INCORRECT (Temporal Leakage)  │ Query lacked `timestamp < evaluation_ts`; │
│                                      │                               │ accessed future wells in historical replay│
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 8. Back-Testing Engine               │ INCORRECT (Temporal Leakage)  │ Held out F-12 (Apr 2008) but used F-14    │
│                                      │                               │ (Sep 2008) & F-15S (Feb 2009) data.       │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 9. Grounded RAG ("Ask NWIS")         │ VERIFIED                      │ Strictly enforces Evidence-or-Silence;    │
│                                      │                               │ returns page/well citations or abstains.  │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 10. Security & Audit Logging         │ VERIFIED                      │ JWT tokens, API keys, RBAC roles, and     │
│                                      │                               │ tamper-evident audit logging implemented. │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 11. Industrial SCADA Web UI          │ VERIFIED                      │ Leaflet map, TVDSS tracks, look-ahead     │
│                                      │                               │ alerts, driller feedback, LOWO runner.    │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 12. Docker / Container Config        │ IMPLEMENTED BUT UNVALIDATED   │ Dockerfile and compose file specified;    │
│                                      │                               │ unvalidated on host due to missing Docker.│
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 13. Automated Test Suite             │ INCOMPLETE                    │ 19 basic tests pass; lacks tests for      │
│                                      │                               │ temporal leakage and missing datums.      │
├──────────────────────────────────────┼───────────────────────────────┼───────────────────────────────────────────┤
│ 14. Real Scanned PDF OCR Pipeline    │ NOT IMPLEMENTED               │ Document extraction model exists in DB    │
│                                      │                               │ schema; live PaddleOCR/Docling in Phase 4.│
└──────────────────────────────────────┴───────────────────────────────┴───────────────────────────────────────────┘
```

---

## 3. Detailed Audit of the Historical Chronology Flaw

### The Flaw:
In `backend/app/services/risk_service.py` (lines 31-45):
```python
candidate_events = db.query(DrillingEvent).filter(
    DrillingEvent.well_id != active_well_id,
    DrillingEvent.depth_tvdss_m >= horizon_top,
    DrillingEvent.depth_tvdss_m <= horizon_base
).all()
```
The query omitted any check on `DrillingEvent.event_timestamp`.

### Chronological Reality of Volve Field Drilling:
1. `NO-15/9-F-1`: Spud March 2006, Completed May 2006. (Exploration/Discovery)
2. `NO-15/9-F-4`: Spud September 2007, Completed December 2007.
3. `NO-15/9-F-12`: Spud April 12, 2008, Completed July 28, 2008.
4. `NO-15/9-F-14`: Spud August 2, 2008, Completed November 15, 2008.
5. `NO-15/9-F-15S`: Spud January 10, 2009, Completed May 20, 2009.

When `NO-15/9-F-12` was drilling in May 2008:
- `NO-15/9-F-14` was **not yet spudded** (spud date August 2, 2008).
- `NO-15/9-F-15S` was **not yet spudded** (spud date January 10, 2009).
- Using incidents from F-14 (`2008-09-14`) and F-15S (`2009-02-18`) to alert F-12 (`2008-05-18`) was a critical chronological error.

### Corrected Evaluation Protocol:
To test `NO-15/9-F-12` strictly, its available historical memory consists only of wells drilled **prior to May 2008** (`NO-15/9-F-1` and `NO-15/9-F-4`).
Conversely, when evaluating `NO-15/9-F-14` (drilled late 2008) or `NO-15/9-F-15S` (drilled 2009), all previously drilled wells (including F-12) are valid historical memory.

---

## 4. Remediation Plan

1. **Implement Strict Temporal Filtering:** Add `as_of_timestamp` to `LookaheadRequest` and filter historical events by `DrillingEvent.event_timestamp < evaluation_timestamp`.
2. **Build Complete Provenance Manifest:** Create `data/raw/volve/provenance_manifest.json` documenting exact NPD and Equinor URLs, SHA-256 hashes, and license boundaries.
3. **Add Explicit Geological Datum Guards:** Raise `INSUFFICIENT_GEOLOGICAL_EVIDENCE` when elevation datum (KB) is missing or $MD < TVD$.
4. **Re-run Multi-Well Chronological Validation:** Replay all eligible wells chronologically and compare against a Geographic-Distance-Only Baseline.
5. **Add Comprehensive Safety & Integrity Tests:** Add unit tests for temporal leakage, missing datums, and baseline comparisons.
