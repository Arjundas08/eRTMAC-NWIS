# NWIS GEOCORE — ADVANCED GEOLOGICAL INTELLIGENCE ARCHITECTURE

**System:** eRTMAC — Nearby Wells Intelligence System (NWIS)  
**Module:** NWIS GeoCore Engine (Phase 03 Specification)  
**Classification:** Enterprise Petroleum Subsurface Architecture  
**Author:** Integrated Multidisciplinary Engineering Team  

---

## 1. Architectural Mission & Philosophy

NWIS GeoCore replaces naive 2D geographical nearest-neighbor matching with deterministic geological correlation and multi-attribute operational compatibility:

> **The Core Problem:** A wellbore drilled 300 meters away across an impermeable sealing fault block or penetrating an entirely different stratigraphic sequence is geologically irrelevant—and often operationally dangerous—compared to a well 1.5 km away in the exact same fault block and dipping sandstone reservoir.

GeoCore implements four signature innovations:
1. **Geological Fingerprint:** Transparent multi-parameter representation distinguishing *Verified*, *Derived*, *Missing*, and *Uncertain* subsurface features.
2. **Formation-Relative Depth Correlation:** Subsurface depth normalization relative to formation tops and bases ($\Delta TVDSS$, penetration percentage, and structural shift) rather than raw measured depth.
3. **Subsurface Spatial Corridor:** 3D Minimum Curvature trajectory volume analysis with pinned historical incidents, depth horizons, and explicit safety clearance notices.
4. **Explainable Similarity & "Why This Well, Not That Well?":** 4-stage candidate screening and head-to-head comparative analysis against distance-only baselines.

---

## 2. System Architecture & Component Diagram

```text
[ Drilling Engineer / RTOC Console ]
                │
                ▼
[ NWIS GeoCore Workspace: /geocore.html ]
   ├── View A: Geological Overview & Summary
   ├── View B: Interactive Geospatial Well Map (Leaflet)
   ├── View C: Formation-Relative Correlation Track
   ├── View D: Geological Fingerprint (Verified vs. Missing)
   ├── View E: Why This Well, Not That Well?
   ├── View F: 3D Subsurface Corridor & Proximity
   └── View G: Specialist Review & Cryptographic Audit
                │
                ▼ (REST API: /api/v1/geocore/...)
┌─────────────────────────────────────────────────────────────┐
│                   NWIS GEOCORE ENGINE                       │
├──────────────────────────────┬──────────────────────────────┤
│  Trajectory Engine           │  Geological Fingerprint      │
│  - Minimum Curvature         │  - Verified vs Missing Audit │
│  - DLS (deg/30m)             │  - Isopach Penetration %     │
│  - Strict KB Datum Guard     │  - Completeness Scoring      │
├──────────────────────────────┼──────────────────────────────┤
│  Formation Correlation       │  Subsurface Corridor         │
│  - Structural Shift (TVDSS)  │  - 3D Minimum Separation     │
│  - Variable Thickness Guard  │  - Pinned Incident Markers   │
│  - Controlled Abstention     │  - ISCWSA Safety Notice      │
├──────────────────────────────┴──────────────────────────────┤
│  Explainable Similarity & Comparative Ranking Engine        │
│  Stage A: Discovery ──> Stage B: Geology ──> Stage C: Ops   │
│  ──> Stage D: Weighted Scoring & Evidence-Linked Rationale  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
[ Evidence Passport & SHA-256 Tamper-Evident Audit Chain ]
   ├── Verified DDR Incidents (Volve Real CSV Records)
   ├── Cryptographic Citation Hashes
   └── Specialist Human Review Sign-Off (HMAC Verification)
```

---

## 3. Core Engine Specifications

### 3.1 Industrial Depth & Trajectory Engine (`trajectory_engine.py`)
- **Algorithm:** Minimum Curvature Method (SPE 8424 / API RP 78).
- **Datum Enforcement:** Enforces valid Kelly Bushing ($KB$) reference datum ($43.5\text{ m}$ for Volve jackup *Mærsk Inspirer*).
- **Safety Policy:** Missing KB elevation raises `INSUFFICIENT_GEOLOGICAL_EVIDENCE`. Zero elevation substitution is strictly prohibited.
- **Interpolation:** Strict piecewise interpolation between verified survey stations. Extrapolation beyond Total Depth (TD) is blocked.

### 3.2 Geological Fingerprint Engine (`geological_fingerprint_service.py`)
- **Inspection Structure:**
  - `VERIFIED_FEATURES`: Surface coordinates, RKB datum, composite log tops, definitive surveys, operational OBM mud weight.
  - `DERIVED_FEATURES`: TVDSS conversion, Minimum Curvature inclination/azimuth, relative formation penetration fraction.
  - `MISSING_FEATURES`: Missing formation base picks, unrecorded mud rheology, missing casing shoe depths.
  - `UNCERTAIN_INTERPRETATIONS`: Seismic picks, low-confidence boundaries.
- **Completeness Meter:** Percent of verified ground truth vs total expected parameters.

### 3.3 Formation-Relative Correlation Engine (`formation_correlation_service.py`)
- **Structural Shift:** $\Delta TVDSS = \text{Top}_{\text{active}} - \text{Top}_{\text{offset}}$.
- **Proportional Depth Alignment:** Maps active bit position into offset interval percentage without assuming constant formation thickness.
- **Controlled Abstention:** If target formation is unpicked or missing in candidate well, returns `UNCORRELATED_FORMATION` and abstains from asserting erroneous hazard correlations.

### 3.4 Explainable Analogue Engine & Comparative Rationale (`geocore_similarity_service.py`)
- **4-Stage Pipeline:**
  1. *Stage A: Discovery* — Haversine spatial radius filtering.
  2. *Stage B: Geological Compatibility* — Formation presence, stratigraphic succession overlap (Jaccard index).
  3. *Stage C: Operational Similarity* — Trajectory inclination deviation delta, mud system compatibility.
  4. *Stage D: Weighted Composite Scoring* — Explicit penalty for missing data, natural language engineering explanation.
- **Why This Well, Not That Well:** Generates side-by-side engineering contrast highlighting formation availability, distance differential, trajectory deviation, and baseline rank divergence.

### 3.5 Human-in-the-Loop Review & Audit Engine (`geocore_review_service.py`)
- Enables Principal Geologists to record review decisions (`APPROVED`, `REJECTED`, `MODIFIED`, `UNCERTAIN`).
- Generates an immutable SHA-256 HMAC for every review event stored in `audit_events`.
