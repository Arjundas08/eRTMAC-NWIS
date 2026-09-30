# NWIS SENTINEL — FORMATION-AWARE HYBRID RETRIEVAL DESIGN
## Multi-Modal Petroleum Engineering Retrieval Engine

### 1. The Core Limitation of Naive Vector RAG in Petroleum Engineering
Standard semantic retrieval (Vector RAG) retrieves text based solely on sentence embedding cosine similarity. In petroleum engineering, this approach fails disastrously due to:
1. **Stratigraphic Incoherence**: Naive vector similarity retrieves passages mentioning "Hugin formation" from distant sub-basins with completely different structural stress regimes and pressure profiles.
2. **Depth Datum Confusion**: Generic embeddings treat `3040m MD` (driller measured depth along wellbore) and `3040m TVDSS` (true vertical depth subsea) as semantically equivalent, ignoring the severe trajectory inclination of directional wells.
3. **Temporal Leakage**: Standard RAG embeds entire document corpora into a static index, retrieving post-incident investigations and root-cause analyses conducted months after an active drilling incident.
4. **Disconnection from Physical Metrics**: Naive RAG separates numerical measurements (e.g., `1.52 SG mud weight`, `450 gpm flow rate`) from their measurement units and wellbore context.

---

### 2. The Four Sentinel Retrieval Modalities

Sentinel overcomes these limitations by orchestrating four fused retrieval modes:

```
                                  [ ENGINEERING QUESTION ]
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
             [ STRUCTURED RETRIEVAL ]                    [ GEOSPATIAL RETRIEVAL ]
             - Table: drilling_events                    - PostGIS ST_Distance
             - Filtering: MD/TVDSS, Severity             - Subsurface 3D Trajectory
             - Parameterized SQL (Allowlisted)           - Surface Spacing (0-15 km)
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
             [ GEOLOGICAL RETRIEVAL ]                     [ SEMANTIC RETRIEVAL ]
             - GeoCore Stratigraphic Alignment           - pgvector Chunk Embeddings
             - Fault-block dip compensation              - PostgreSQL tsvector Full-Text
             - Facies correlation (Pearson > 0.8)        - Exact Bounding Box Metadata
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             │
                                             ▼
                             [ FUSED RETRIEVAL SYNTHESIS ]
                             - Temporal Firewall Gating
                             - Access Control Filtering
                             - Quarantine Future Passages
```

#### A. Structured Relational Retrieval
- Directly queries certified operational records in PostgreSQL (`drilling_events`, `wellbores`).
- Filters strictly on validated wellbore identity, event category (`LOST_CIRCULATION`, `STUCK_PIPE`, `GAS_KICK`, `PACK_OFF`), and numerical depth intervals.
- Safe allowlisted parameterized query building: **LLM is never permitted to execute unconstrained SQL directly.**

#### B. Geospatial Retrieval (PostGIS)
- Leverages spatial indexing to rank offset wells by geographic proximity and subsurface collision risks.
- Computes surface wellhead distance using haversine formulations and 3D subsurface trajectory separation.

#### C. Geological Stratigraphic Retrieval (GeoCore Integration)
- Reuses verified GeoCore services (`geocore_service.py`):
  - Geological Fingerprints (GR, Resistivity, Sonic log signatures).
  - True Vertical Depth Subsea (TVDSS) normalization.
  - Formation tops correlation and fault-block dip alignment.
  - Directional trajectory Minimum Curvature interpolation.

#### D. Semantic & Lexical Passage Retrieval (pgvector + FTS)
- Uses dense embeddings alongside PostgreSQL full-text search (`tsvector`) to retrieve descriptive tour sheet narratives, driller remarks, and mitigation procedures.
- Every chunk maintains exact physical provenance:
  - Document ID (`DDR-2008-04-18-NO-15-9-F-14-DDR-016`)
  - Page number (`Page 1`, `Page 2`)
  - Bounding box coordinates (`[x0, y0, x1, y1]`)
  - SHA-256 integrity checksum

---

### 3. Petroleum-Aware Technical Document Chunking

Rather than splitting technical reports arbitrarily by character count (e.g., 500 characters), Sentinel implements engineering-aware chunking:
1. **Preservation of Table Integrity**: Technical parameter tables (bit records, mud properties, survey sheets) are kept as contiguous units, preventing the detachment of numerical values from units (e.g., `1.52 SG`, `3800 psi`).
2. **Contextual Metadata Binding**: Every extracted chunk is tagged with its associated wellbore, formation name, depth interval, report date, and verification status at extraction time.
3. **Versioned Embeddings**: When a report is updated or re-ingested with higher-resolution OCR, older embeddings are marked obsolete and purged, preventing index staleness.

---

### 4. Point-in-Time Temporal Firewall Enforcement

When a query relates to an active drilling horizon or historical Chronos replay session:
- The temporal cutoff date $T_{cutoff}$ is strictly enforced.
- Any document with `report_date > T_cutoff` is **quarantined and excluded** from retrieval.
- The retrieval summary explicitly reports the number of quarantined future documents to provide complete transparency.
