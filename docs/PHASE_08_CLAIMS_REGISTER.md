# SIH26121 — PHASE 08 CLAIMS REGISTER
## Unified Register of Technical, Algorithmic & Performance Claims (Phases 01–07)

**Date of Audit:** 2026-09-30  
**Audit Lead:** Independent QA Lead & Senior Drilling Systems Architect  
**Classification Standard:**
- `REPRODUCED`: Claim independently verified via executable automated test against real data.
- `SUPPORTED_WITH_LIMITATIONS`: Claim is technically valid within a documented, bounded operational envelope.
- `DEMONSTRATION_ONLY`: Feature operates as a functional prototype or synthetic fixture for demonstration.
- `UNVERIFIED`: Claim lacks reproducible automated test or independent external benchmark.
- `CONTRADICTED`: Observed behavior does not match documented claim.

---

## 1. Master Claims Verification Matrix

| Claim ID | Claim Summary | Source Document | Test Execution Command | Expected Result | Observed Result | Classification | Operational Limitations |
|---|---|---|---|---|---|---|---|
| **CLM-01** | Minimum Curvature trajectory complies with Sawaryn & Thorogood (2005) reference. | `docs/PHASE_03_GEOCORE_ARCHITECTURE.md` | `pytest backend/tests/test_geocore.py::test_trajectory_minimum_curvature_analytical_reference` | $\Delta \text{TVD} < 0.1\text{m}$, $\Delta \text{Northing} < 0.1\text{m}$ | Exact analytical match ($< 0.001\text{m}$ deviation) | `REPRODUCED` | Valid for dogleg severity $< 15^\circ/30\text{m}$; vertical wells handled via straight-line limit. |
| **CLM-02** | TVDSS normalization resolves KB vs MSL datum discrepancies. | `docs/PHASE_01_AUDIT.md` | `pytest backend/tests/test_stratigraphy.py::test_compute_tvdss` | $\text{TVDSS} = \text{TVD} - \text{KB}$ | Correct conversion across all 34 formation picks | `REPRODUCED` | Requires accurate KB elevation metadata; throws `GeologicalDatumError` if KB missing. |
| **CLM-03** | LOWO Back-Testing achieves 100% recall on verified mud loss & stuck pipe events. | `docs/PHASE_02_COMPLETION_REPORT.md` | `pytest backend/tests/test_backtest.py` | Recall = 1.0 (10/10 events flagged) | 100% recall on 10 verified Volve DDR events | `SUPPORTED_WITH_LIMITATIONS` | Evaluated on 5 Volve development wellbores; larger field-wide variance requires OIL databank testing. |
| **CLM-04** | Pre-bit look-ahead warning provides average lead distance of 72m. | `docs/PHASE_02_COMPLETION_REPORT.md` | `python scripts/run_lowo_backtest.py` | Mean lead $\ge 50\text{m}$ ahead of bit | Mean lead observed = $71.8\text{m}$ | `SUPPORTED_WITH_LIMITATIONS` | Lookahead window parameter configured to $75\text{m}$ nominal; maximum configured radius $150\text{m}$. |
| **CLM-05** | Strict Evidence-or-Silence abstains when no verified evidence exists. | `docs/PHASE_05_SENTINEL_ARCHITECTURE.md` | `pytest backend/tests/test_sentinel.py::test_evidence_or_silence_abstains_on_unsupported_data` | Return `ABSTAIN` / `INSUFFICIENT_EVIDENCE` | System explicitly returns structured abstention | `REPRODUCED` | Prevents hallucination; requires human review queue fallback for unverified queries. |
| **CLM-06** | Temporal firewall completely prevents future incident leakage during historical replay. | `docs/PHASE_04_CHRONOS_ARCHITECTURE.md` | `pytest backend/tests/test_chronos.py::test_temporal_firewall_blocks_future_data` | Zero future events accessible | 100% isolation of post-spud data | `REPRODUCED` | Filter operates strictly on ISO-8601 timestamps and well spud chronologies. |
| **CLM-07** | Universal Telemetry Adapter parses genuine WITSML 1.4.1.1 XML and WITSML 2.1 JSON. | `docs/PHASE_06_ADAPTER_SPECIFICATION.md` | `pytest backend/tests/test_pulse.py::test_witsml_1411_adapter_parsing` | Normalized canonical packet with valid engineering UOMs | Valid packet parsed with depth, ROP, WOB, torque | `REPRODUCED` | Real-time rig connection requires external VPN/network authorization to rig site. |
| **CLM-08** | Full test suite regression passes with 100% success rate. | `docs/PHASE_07_COMPLETION_REPORT.md` | `pytest backend/tests/ -v --tb=short` | 118 passed in $< 5\text{s}$ | 118 passed in $3.95\text{s}$ (100% pass) | `REPRODUCED` | Executed against SQLite local database with in-memory fixtures. |
| **CLM-09** | Composite Risk Score represents certified drilling incident probability. | `docs/PHASE_07_NEXUS_ARCHITECTURE.md` | N/A (Methodological Inspection) | Bayesian calibrated failure rate | **CONTRADICTED / MISLABELED** | `SUPPORTED_WITH_LIMITATIONS` (Post-Reclassification) | Heuristic weighting ($0.40/0.30/0.30$) is an operational prioritization index, NOT certified incident probability. Renamed to **NWIS Context Priority Index (CPI)**. |
| **CLM-10** | System is certified and approved for field deployment by Oil India Limited. | N/A (Proposal / Scope) | N/A (Governance Check) | OIL Executive Authorization | **UNVERIFIED / PROPOSED** | `DEMONSTRATION_ONLY` | System is a field-pilot-ready candidate demonstrated on open Volve data. Requires formal OIL sandbox trial. |

---

## 2. Claims Reclassification Actions

1. **Risk Scoring Terminology:**
   - *Old Documented Claim:* "Certified composite drilling risk calculation."
   - *Corrected Formal Definition:* **"NWIS Context Priority Index (CPI)"** — a deterministic, configurable prioritization heuristic engineered to rank supervisory attention, NOT a certified Well Control risk certification or statistical probability of blowout/kick.
2. **Evaluation Dataset Population:**
   - All empirical metrics (100% recall, 71.8m lead distance) are explicitly contextualized to the 5-well, 10-incident Volve field open benchmark.
3. **Cryptographic Protection Scope:**
   - Bare SHA-256 digests verify data integrity against accidental bit corruption. Tamper authentication requires HMAC-SHA256 with key management, implemented in Phase 08.
