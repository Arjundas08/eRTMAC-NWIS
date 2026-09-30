# NWIS CHRONOS: INDEPENDENT EVALUATION PROTOCOL
**Subsystem:** NWIS Chronos Historical Validation Framework  
**Standard:** Chronological Leave-One-Well-Out (LOWO) Empirical Back-Testing  
**Evaluation Target:** Authentic Historical Drilling Incidents (Equinor Volve Field)  
**Governance Standard:** Zero Information Leakage & Independent Ground-Truth Isolation  

---

## 1. Overview & Objective

The objective of the NWIS Chronos Evaluation Protocol is to establish an unassailable mathematical standard for measuring how accurately an offset-well decision-support system would have alerted drilling engineers to physical subsurface hazards before they occurred.

---

## 2. Chronological Leave-One-Well-Out (LOWO) Standard

In conventional machine learning, random cross-validation randomly shuffles samples. In historical drilling operations, **random shuffling causes catastrophic temporal leakage** because future events are used to predict past operations.

### Protocol Steps:
1. **Target Well Isolation:** Select an eligible historical well $W_{\text{target}}$ with certified spud date $T_{\text{spud}}$.
2. **Point-in-Time Knowledge Freezing:** Freeze the system's memory snapshot to $T \le T_{\text{spud}}$. Any wellbore $W_i$ with $T_{\text{spud}}(W_i) > T_{\text{spud}}(W_{\text{target}})$ is strictly excised.
3. **Target Well History Blindfold:** The target well's own operational outcome, DDRs, and incident records are completely withheld from the advisory engine.
4. **Step-by-Step Chronological Progression:** Advance the target wellbore bit position from surface casing to total depth $(TD)$ in fixed increments (10m).
5. **Advisory Generation:** At each step, execute the formation look-ahead scanner using only eligible prior offset data.
6. **Air-Gapped Adjudication:** Compare the generated advisories against independently adjudicated ground-truth incidents using strict event-matching rules.

---

## 3. Ground-Truth Event Matching & Cooldown Policy

To prevent alert clustering from artificially inflating true positive counts, the evaluation applies explicit matching and suppression rules:

### 3.1 Event Matching Criteria
An advisory $A$ generated at depth $MD_{\text{adv}}$ is scored as a **True Positive (TP)** for ground-truth incident $G$ at depth $MD_{\text{gt}}$ if and only if:
1. **Hazard Category Alignment:** $\text{Category}(A) == \text{Category}(G)$ (e.g., `LOST_CIRCULATION`).
2. **Advance Lead Distance:** The advisory was generated *before* reaching the incident:
   $$0 < (MD_{\text{gt}} - MD_{\text{adv}}) \le \Delta Z_{\text{lookahead}}$$
3. **Stratigraphic Horizon Match:** The advisory correlates to the same stratigraphic formation (e.g., `Hugin FM`).

### 3.2 Cooldown Suppression
To prevent repetitive warnings from artificially multiplying true positives:
* Once an advisory successfully matches a ground-truth incident, subsequent advisories for the same hazard category are placed on cooldown for $\Delta Z_{\text{cooldown}} = 50\text{ meters}$.
* Exactly **one True Positive** is credited per distinct physical incident.

---

## 4. Mathematical Metric Formulations

### 4.1 Event Recall
$$\text{Recall} = \frac{TP}{TP + FN} = \frac{\text{Historical Incidents Successfully Warned}}{\text{Total Documented Ground-Truth Incidents}}$$

### 4.2 Event Precision
$$\text{Precision} = \frac{TP}{TP + FP} = \frac{\text{Valid Early Warnings}}{\text{Total Warning Triggers Generated}}$$

### 4.3 False Alarm Rate (Burden per 100m)
$$\text{FAR}_{100\text{m}} = \frac{FP}{(MD_{\text{TD}} - MD_{\text{start}}) / 100}$$

### 4.4 Early Warning Lead Distance
For each true positive $i$:
$$\text{LeadDistance}_i = MD_{\text{incident}, i} - MD_{\text{warning}, i}$$
$$\overline{\text{LeadDistance}} = \frac{1}{N_{TP}} \sum_{i=1}^{N_{TP}} \text{LeadDistance}_i$$

---

## 5. Summary of Protocol Enforcement

Every evaluation run executed via `/api/v1/chronos/evaluation/run` is permanently recorded in the database `evaluation_runs` table with its exact configuration parameters, execution timestamp, and cryptographic snapshot hash, guaranteeing full reproducibility.
