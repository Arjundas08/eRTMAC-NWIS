# SIH26121 — PHASE 08 NEXUS RISK-SCORING AUDIT
## Deconstruction, Sensitivity Analysis & Reclassification to Context Priority Index (CPI)

**Audit Date:** 2026-09-30  
**Audit Team:** Senior Drilling Engineer & Petroleum Data Validation Engineer  
**Component:** `backend/app/services/nexus_engine.py` (`_calculate_risk_score`)  
**Status:** AUDITED, REFACTORED & VALIDATED  

---

## 1. Executive Summary & Defect Finding

During Phase 07, the composite scoring formulation was presented under the terminology of "Drilling Risk Score" with output tiers `LOW`, `MODERATE`, `ELEVATED`, and `CRITICAL`.

### Critical Findings:
1. **Lack of Calibrated Probability:** The mathematical formulation is a weighted linear composite ($0.40$ historical event density, $0.30$ active advisories, $0.30$ telemetry quality). It was **not** fitted against an empirical Bayesian probability distribution of actual well control incidents across global drilling datasets.
2. **Ambiguity with Certified Well Control:** In industrial drilling engineering (API RP 59, IADC WellCAP, NORSOK D-010), "Critical Risk" denotes an imminent barrier impairment or loss of well control. Presenting an algorithmic heuristic as a certified "Critical Risk" creates dangerous confusion in operational environments.
3. **Missing Data Vulnerability:** When telemetry feeds are unmonitored or offline, arbitrary penalty assignment could either falsely elevate or suppress the resulting score.

---

## 2. Re-Alignment: NWIS Context Priority Index (CPI)

As directed by Section 5 of Prompt 08, the metric has been officially refactored and reclassified:
- **Canonical Term:** **NWIS Context Priority Index (CPI)**
- **Formula Identifier:** `NWIS-CPI-v1.1-HEURISTIC`
- **Purpose:** A deterministic, explainable supervisory triage heuristic designed to rank and prioritize multi-well monitoring attention.
- **Explicit Boundary:** **NOT a calibrated probability of kick, blowout, or equipment failure, and NOT a replacement for certified Well Control safety systems or engineering supervision.**

### Mathematical Formulation:
$$\text{CPI} = \min\left(100.0, \; \max\left(0.0, \; w_h S_h + w_a S_a + w_t S_t\right)\right)$$

Where:
- $w_h = 0.40$ (Historical event density weight)
- $w_a = 0.30$ (Active advisory burden weight)
- $w_t = 0.30$ (Telemetry sensor quality weight)
- $S_h = \min\left(100.0, \; \sum_{i} \text{SevWeight}_i \cdot \text{Count}_i\right)$
  - Critical: $25\text{ pts}$ | Severe: $15\text{ pts}$ | Moderate: $5\text{ pts}$ | Minor: $1\text{ pt}$
- $S_a = \min\left(100.0, \; \text{ActiveAdvisories} \times 20.0\right)$
- $S_t$: Telemetry Quality Score:
  - `HEALTHY`: $0.0\text{ pts}$ (nominal)
  - `DEGRADED`: $40.0\text{ pts}$
  - `STALE`: $60.0\text{ pts}$
  - `INSUFFICIENT`: $80.0\text{ pts}$
  - `OFFLINE`: $100.0\text{ pts}$
  - `MISSING_TELEMETRY`: $30.0\text{ pts}$ (neutral unmonitored baseline, avoids false alarms)

### Priority Tiers:
| CPI Score Range | Canonical CPI Label | Legacy Tier Alias | Operational Action Guideline |
|---|---|---|---|
| **0.0 – 24.9** | `MONITOR_NOMINAL` | `LOW` | Standard automated telemetry monitoring; no supervisory intervention needed. |
| **25.0 – 49.9** | `ATTENTION_ADVISORY` | `MODERATE` | Review advisory recommendations; verify mud weight & offset lithology. |
| **50.0 – 74.9** | `PRIORITY_REVIEW` | `ELEVATED` | Operations supervisor review required; verify ECD and offset hazard correlations. |
| **75.0 – 100.0** | `URGENT_OPERATIONAL_CHECK`| `CRITICAL` | Immediate engineering check; inspect active advisory causes and telemetry health. |

---

## 3. Sensitivity & Extreme Value Testing

| Scenario | Inputs ($S_h, S_a, S_t$) | Raw Composite | Clamped CPI | Assigned Tier | Behavior Verification |
|---|---|---|---|---|---|
| **Best Case (Clean Well)** | $S_h=0, S_a=0, S_t=0$ (Healthy) | $0.0$ | $0.0$ | `MONITOR_NOMINAL` | PASS: Zero false positives |
| **Worst Case (Severe Multiple)**| $S_h=150 \to 100, S_a=120 \to 100, S_t=100$ | $100.0$ | $100.0$ | `URGENT_OPERATIONAL_CHECK`| PASS: Bounded at 100.0 |
| **No Telemetry Feeds** | $S_h=20, S_a=0, S_t=\text{Missing} (30)$ | $8.0 + 0 + 9.0 = 17.0$| $17.0$ | `MONITOR_NOMINAL` | PASS: Missing data does not panic |
| **Stale Telemetry Only** | $S_h=0, S_a=0, S_t=\text{Stale} (60)$ | $0 + 0 + 18.0 = 18.0$ | $18.0$ | `MONITOR_NOMINAL` | PASS: Sensor delay alone doesn't trigger emergency |
| **Active Kick Advisory** | $S_h=25, S_a=60, S_t=40$ | $10 + 18 + 12 = 40.0$ | $40.0$ | `ATTENTION_ADVISORY` | PASS: Immediate advisory elevation |

---

## 4. Code & API Backward Compatibility

The implementation in `nexus_engine.py` maintains dual fields:
1. `context_priority_index` and `priority_tier` (Canonical Phase 08 standard)
2. `composite_score` and `risk_tier` (Phase 07 backwards compatibility)
3. Full transparency dictionary (`formula_version`, `weights`, `sensitivity_bounds`, `disclaimer`).
