# SIH26121 — PHASE 08 SOURCE PROVENANCE AUDIT
## Evidence Authenticity Lock & Master Provenance Register

**Audit Date:** 2026-09-30  
**Data Validation Lead:** Petroleum Data Validation Engineer & Independent QA Architect  
**Authority Standards:**
- Norwegian Offshore Directorate (NOD / NPD Factpages): `https://factpages.sodir.no/`
- Equinor Volve Open Data Sharing License: `https://www.equinor.com/energy/volve-data-sharing`
- IADC Daily Drilling Report Schema Guidelines

---

## 1. Provenance Hierarchy Standard

To prevent data contamination, synthetic leakage, or false historical attribution, all records in the eRTMAC-NWIS system are categorized into six strict tiers:

1. **`ORIGINAL_VERIFIED`**: Primary source documents/files directly retrieved from official government registries or operating company archival repositories with verified digital signatures or immutable origin records.
2. **`DERIVED_FROM_VERIFIED_SOURCE`**: Tabular and structured records extracted programmatically or through audited manual transcription from verified primary documents, with exact field-level traceability.
3. **`RECONSTRUCTED_FIXTURE`**: Documents or datasets reconstructed using authentic historical operational parameters (exact depths, formation names, dates, and event narratives) to replicate archival layouts for testing document ingestion and OCR pipelines.
4. **`SYNTHETIC_FIXTURE`**: Artificially generated fixtures created to test edge conditions, negative cases (e.g. routine drilling with zero incidents), corrupt formats, or extreme stress tests.
5. **`UNVERIFIED`**: Third-party or user-submitted records lacking cross-referencing against primary government or operator archives.
6. **`REJECTED`**: Contradictory, fabricated, or mathematically physically impossible records barred from operational or evaluation datasets.

---

## 2. Comprehensive Provenance Ledger

| Artifact Identifier | Tier Classification | SHA-256 Digest | Records | Primary Source Authority | Purpose & Usage |
|---|---|---|---|---|---|
| `well_headers.csv` | `DERIVED_FROM_VERIFIED_SOURCE` | `4ee74c8f4e20faa0...` | 5 wells | NPD Factpages (`PL 046`) | Well coordinate reference & metadata |
| `formation_tops.csv` | `DERIVED_FROM_VERIFIED_SOURCE` | `e8bb43b61425a9c4...` | 34 tops | Equinor Composite Well Logs | Stratigraphic TVDSS reference |
| `surveys.csv` | `DERIVED_FROM_VERIFIED_SOURCE` | `08e5159e714dfb34...` | 35 stations | Schlumberger MWD Gyro | 3D wellbore trajectory calculation |
| `real_ddr_events.csv`| `DERIVED_FROM_VERIFIED_SOURCE` | `a0971c3f99703b21...` | 10 events | Equinor Volve DDR & NPT Logs | Historical incident ground truth |
| `VOLVE_DDR_20080914_F14.pdf` | `RECONSTRUCTED_FIXTURE` | `a7ee3dbf87c9f809...` | 2 incidents | Reconstructed via ReportLab | OCR & Evidence Passport test fixture |
| `VOLVE_DDR_20080922_F14.pdf` | `RECONSTRUCTED_FIXTURE` | `b3fe80a9117f69f2...` | 1 incident | Reconstructed via ReportLab | Stuck pipe extraction pipeline test |
| `VOLVE_DDR_20090218_F15S.pdf` | `RECONSTRUCTED_FIXTURE` | `222384a8677c77c6...` | 1 incident | Reconstructed via ReportLab | High-depth packoff extraction test |
| `VOLVE_DDR_ROUTINE_DRILLING_CLEAN.pdf` | `SYNTHETIC_FIXTURE` | `646f91b790d56c80...` | 0 incidents | Synthetic clean baseline | Negative case testing (no false alerts) |
| `VOLVE_DDR_SCANNED_MUD_REPORT.pdf` | `SYNTHETIC_FIXTURE` | `11d615e4f4fb0ca7...` | 1 table | Synthetic rasterized image | OCR noise and skew resilience test |

---

## 3. Disputed Source Audit & Adjudication

### 3.1 Wellbore Depth Datums (KB vs MSL)
- **Official NOD Record:** Well 15/9-F-14 has a Kelly Bushing (KB) elevation of $43.5\text{ m}$ above Mean Sea Level (MSL), and sea water depth is $82.0\text{ m}$.
- **Verification Rule:** All subsurface TVD values in `formation_tops.csv` and `surveys.csv` are referenced to KB unless explicitly converted to TVDSS via the formula:
  $$\text{TVDSS} = \text{TVD}_{\text{KB}} - \text{KB\_Elevation}$$
- **Audit Result:** PASSED. All GeoCore and Stratigraphic calculations adhere to strict TVDSS normalization.

### 3.2 Spud Chronology & Historical Leakage Protection
- `NO-15/9-F-1`: Spudded 2006-03-01. Pioneer discovery well.
- `NO-15/9-F-4`: Spudded 2007-09-14.
- `NO-15/9-F-12`: Spudded 2008-04-12.
- `NO-15/9-F-14`: Spudded 2008-08-02.
- `NO-15/9-F-15S`: Spudded 2009-01-20.

**Temporal Integrity Policy:** Under no circumstances may an advisory or simulation for Well F-12 reference incidents from F-14 or F-15S that occurred chronologically after F-12 reached total depth. This is programmatically enforced by `chronos_firewall.py` and validated by `test_audit_integrity.py`.

---

## 4. Machine-Readable Export

The complete ledger is saved in machine-readable JSON format at:  
`data/provenance_ledger_phase08.json`
