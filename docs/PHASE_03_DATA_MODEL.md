# NWIS GEOCORE — CANONICAL SUBSURFACE DATA MODEL

**Architecture Classification:** Petroleum Geological & Subsurface Engineering Specification  
**Version:** 3.0.0 (Production Architecture)  
**Standard Compliance:** OSDU Subsurface Trajectory Spec & NPD / Equinor Stratigraphic Schema  

---

## 1. Domain Entities & Subsurface Hierarchy

GeoCore enforces strict separation between physical wellheads, individual wellbores, sidetrack relationships, directional survey versions, and geological interpretations:

```text
[Field] (PL 046 Volve)
   │
   ├── [FaultBlock] (Central Graben Horst)
   │
   ├── [Reservoir] (Hugin Sandstone Reservoir)
   │
   └── [Well] (Platform Slot F-12, F-14, F-15...)
         │
         ├── [DepthDatum] (RKB 43.5m, Water Depth 82.0m)
         │
         └── [Wellbore] (NO-15/9-F-12, NO-15/9-F-15S)
               │
               ├── [WellboreRelationship] (Parent: F-15 -> Sidetrack: F-15S @ 2800m MD)
               │
               ├── [SurveyVersion] (Definitive MWD/Gyro Run #1)
               │     └── [SurveyStation] (MD, Inc, Azim, TVD, TVDSS, Northing, Easting, DLS)
               │
               ├── [FormationInterpretation] (Volve Composite Log Interpretation)
               │     ├── [FormationTop] (Verified Top MD / TVDSS)
               │     └── [FormationBottom] (Base MD / TVDSS, is_proven flag)
               │
               ├── [LithologyInterval] (Sandstone, Shale, Limestone intervals)
               │
               ├── [OperationalInterval] (Hole Size, Casing Shoe, Mud System)
               │
               └── [DrillingEvent] (Historical DDR Incidents linked to Evidence Passport)
```

---

## 2. Table Specifications

### 2.1 Spatial & Wellbore Architecture
- **`fields`**: Regional field boundary, country, basin, operator.
- **`wells`**: Surface location (latitude, longitude), RKB elevation, spud date.
- **`wellbores`**: Unique drill stem identity, sidetrack kickoff depth, type (`ORIGINAL`, `SIDETRACK`, `BYPASS`).
- **`wellbore_relationships`**: Sidetrack parent-child linkages, kickoff formation.
- **`depth_datums`**: Verified RKB, MSL, and Ground elevations. Enforces `INSUFFICIENT_GEOLOGICAL_EVIDENCE` if datum missing.

### 2.2 Directional Trajectory & Minimum Curvature
- **`survey_versions`**: Survey tool lineage (MWD/Gyro), calculation method (`MINIMUM_CURVATURE`), `is_definitive` flag.
- **`survey_stations`**: Measured Depth ($MD$), Inclination ($\theta$), Azimuth ($\phi$), True Vertical Depth ($TVD$), True Vertical Depth Subsea ($TVDSS$), Northing, Easting, Dogleg Severity ($DLS$).

### 2.3 Geological Horizons & Stratigraphy
- **`formations`**: Regional stratigraphic master record (Nordland GP, Utsira FM, Hordaland GP, Rogaland GP, Chalk GP, Heather FM, Hugin FM, Skagerrak FM, Smith Bank FM).
- **`formation_interpretations`**: Versioned geological picks with confidence levels (`CONFIRMED`, `PROBABLE`, `INFERRED`, `UNCERTAIN`) and uncertainty bounds ($\pm\text{m}$).
- **`formation_bottoms`**: Validated base picks; prevents assuming constant thickness.
- **`fault_blocks`**: Structural domain, compartment, and fault throw.

### 2.4 Correlation & Explainable Analogue Engines
- **`geological_correlations`**: Relative formation alignment, depth shift ($\Delta TVDSS$), correlation uncertainty, abstention flags (`FAULT_DISCONTINUITY`, `INSUFFICIENT_EVIDENCE`).
- **`correlation_reviews`**: Human-in-the-loop expert geological sign-off with audit trail.
- **`analogue_candidates`**: Candidate screening records with explicit exclusion reasons.
- **`analogue_evaluations`**: Explainable multi-factor similarity scores (Geological, Operational, Proximity) and JSON rationale.
