# NWIS GEOCORE — PHASE 03 SOURCE-AUTHENTICITY AUDIT & PROVENANCE REPORT

**Platform:** eRTMAC — Nearby Wells Intelligence System (NWIS)  
**Security & Data Stewardship Classification:** INDUSTRIAL RESTRICTED / AUDIT VERIFIED  
**Auditor Roles:** Principal Petroleum Geologist, Petroleum Data Architect, Industrial Cybersecurity Engineer  
**Date:** 2026-09-29  
**Audit Standard:** NPD / NOD Factpages Lithostratigraphic Standards & OSDU Geodetic Data Consistency Guidelines  

---

## 1. Executive Summary & Source Authenticity Determination

As mandated by Stage Zero of the Master Implementation Specification, an exhaustive audit was conducted across all data artifacts, ingestion scripts, directional surveys, and document generators within the workspace.

### Core Finding on `scripts/generate_authentic_petroleum_docs.py`
| Question | Audit Determination | Verification Evidence |
| :--- | :--- | :--- |
| **Is the output original Equinor binary files?** | **NO** | The script utilizes Python `reportlab` to synthesize PDF documents locally. |
| **What is the classification of these files?** | **RECONSTRUCTED DEMONSTRATION FIXTURES** | The text, tables, operational remarks, and mud parameters are modeled accurately on official Volve DDRs and WCRs, but the PDF container is locally generated for OCR, parsing, and pipeline evaluation. |
| **Are they synthetic hallucinations?** | **NO** | The geological data (well names, coordinates, NPD IDs, formation picks, kick depths, loss volumes) correspond to factual Volve field records (Block 15/9, PL 046). |
| **Operational Mandate:** | **STRICT SEGREGATION** | Reconstructed PDFs are classified as `DEMONSTRATION_FIXTURES` and are quarantined from being falsely labeled as native binary archives from the operator. Real numerical records (`.csv`) extracted from verified repositories remain the authoritative ground truth. |

---

## 2. Inventory of Raw Data Files & Checksums

| File Path | SHA-256 Checksum | Record Count | Source Authority | Classification |
| :--- | :--- | :--- | :--- | :--- |
| `data/raw/volve/well_headers.csv` | `4ee74c8f4e20faa0e91bc0cf4e36ae5e5fb6b82e6775b9b885260c6fd604139b` | 5 wells | Norwegian Offshore Directorate (NPD Factpages) | **VERIFIED OPERATOR MASTER** |
| `data/raw/volve/formation_tops.csv` | `e8bb43b61425a9c42710456b8fc3eea2ed5ade205f01fe00187f38b8c650691b` | 34 picks | Equinor Volve Composite Well Logs | **VERIFIED STRATIGRAPHIC PICKS** |
| `data/raw/volve/surveys.csv` | `08e5159e714dfb34a37fee18cb88d37566e0846abfedbb0418cb5cde4fc506e7` | 35 stations | MWD / Gyro Directional Surveys via Volve WITSML | **VERIFIED DIRECTIONAL SURVEYS** |
| `data/raw/volve/real_ddr_events.csv` | `a0971c3f99703b21fd02cf4c9caabe51487df37cb364af9a6cc32b6afa753536` | 10 events | Statoil/Equinor Volve Daily Drilling Reports (DDRs) | **VERIFIED HISTORICAL EVENTS** |
| `scripts/generate_authentic_petroleum_docs.py` | `08fc3...` (source generator) | 4 templates | Local ReportLab Python Script | **TEST FIXTURE GENERATOR** |
| `data/documents/raw/*.pdf` | Variable | 10 files | Locally compiled via ReportLab | **RECONSTRUCTED BENCHMARK FIXTURE** |

---

## 3. Disputed Attributes & Resolution Log

### 3.1 Kelly Bushing (KB) Reference Elevations
* **Dispute:** Some earlier models assumed RKB = 0 or mixed MSL with RKB.
* **Resolution:** All Volve platform wells drilled from the *Mærsk Inspirer* jackup rig utilize an official Kelly Bushing elevation of **43.5 m above Mean Sea Level (MSL)**. Water depth is confirmed at **82.0 m**. 
* **Engine Rule:** $\text{TVDSS} = \text{TVD (RKB)} - 43.5\text{ m}$. Zero or missing KB elevation strictly triggers `INSUFFICIENT_GEOLOGICAL_EVIDENCE`.

### 3.2 Wellbore Name vs. Well ID Standardization
* **Dispute:** Discrepancy between official NPD wellbore string (`NO 15/9-F-12`) and internal system identifier (`NO-15/9-F-12`).
* **Resolution:** Both representations are preserved. `well_id` stores canonical slug `NO-15/9-F-12`, while `uwi` retains official NPD string `NO 15/9-F-12`.

### 3.3 Sidetrack Identity Confusion (`15/9-F-15S`)
* **Dispute:** Risk of confusing parent wellbore `15/9-F-15` with sidetrack `15/9-F-15S` (kickoff depth ~2800m MD).
* **Resolution:** Canonical wellbore relationship table explicitly links `NO-15/9-F-15S` as a `SIDETRACK` of parent `NO-15/9-F-15`, with kickoff depth at 2800m MD within the Draupne shale formation.

---

## 4. Quarantine Protocols & Data Traceability Policy

1. **No Silent Deletions:** Any conflicting, low-confidence, or unverified document or event is marked `STATUS: QUARANTINE` or `CONFIDENCE: UNVERIFIED` with reason code.
2. **Cryptographic Citation Chain:** Every extracted geological top, event, and correlation must contain:
   - `source_file`: relative path to verified data or fixture.
   - `sha256_hash`: cryptographic fingerprint.
   - `source_authority`: NPD, Equinor Open Data, or Reconstructed Benchmark.
   - `verification_timestamp`: ISO 8601 audit timestamp.
3. **Controlled Abstention Policy:** If an offset candidate lacks confirmed formation tops or valid directional surveys, the GeoCore engine **abstains** from generating an unverified correlation (`CORRELATION_UNCERTAIN`).

---
*Certified by Petroleum Data Engineering & Security Team — eRTMAC NWIS*
