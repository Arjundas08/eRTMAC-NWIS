# SIH26121 — WINNING SIH GRAND FINALE DEMONSTRATION SCRIPT
## eRTMAC-NWIS: Nearby Wells Intelligence System for Oil India Limited
### Timed 8-Minute High-Impact Live Demonstration & Presentation Script

**Target Event:** Smart India Hackathon 2026 Grand Finale  
**Problem Statement:** SIH26121 — Nearby Wells Intelligence System (eRTMAC)  
**Presented To:** Oil India Limited Executive Evaluators & Technical Jury  
**Demonstration Time:** 8 Minutes Sharp (with 2 Minutes Buffer for Q&A)  
**System URL:** `http://localhost:8000` (or Rig-Floor Edge Workstation)  

---

## Pre-Flight Checklist (T-Minus 5 Minutes)

Before calling the judges to the screen:
1. Ensure FastAPI backend is running: `uvicorn backend.app.main:app --port 8000`
2. Open Chrome/Edge in Full Screen (`F11`) with three pinned tabs:
   - **Tab 1 (Primary):** `http://localhost:8000/nexus.html` (Unified Cross-Module Dashboard)
   - **Tab 2 (Sentinel):** `http://localhost:8000/sentinel.html` (Document Intelligence & Evidence Graph)
   - **Tab 3 (Chronos):** `http://localhost:8000/chronos.html` (Historical Replay Laboratory)
3. Have terminal open in background to verify real API response times ($< 5\text{ms}$).
4. Keep `SIH26121_eRTMAC_NWIS_Winning_Pitch.pptx` open in presentation view.

---

## Timed Demonstration Script

### [00:00 - 01:15] ACT 1: THE HOOK & THE INDUSTRIAL REALITY
**Speaker Stance:** Confident, direct, empathetic to drilling engineers.  
**Visual:** Slide 1 & 2 ("The Measured Depth Trap across Dipping Formations").

> *"Respected Jury and Engineers from Oil India Limited:*
>
> *Every day, drilling an exploration well in Assam or Rajasthan costs over ₹25 Lakhs per hour in rig operating expenses. When a drill string gets stuck or mud circulation is lost, operations halt for days, causing crores in Non-Productive Time (NPT).*
>
> *Oil India has drilled thousands of wells over six decades. The solutions to almost every drilling hazard are already documented—buried inside more than 100,000 pages of scanned Daily Drilling Reports, mud logs, and end-of-well reports.*
>
> *Why do drilling engineers still hit avoidable hazards?*
>
> *Because of two fatal engineering flaws in conventional software:*
> 1. **The Measured Depth Trap:** In dipping geological strata, 2,800 meters Measured Depth in Well-A can be in a completely different formation than 2,800 meters in Well-B. Comparing wells by surface distance and raw depth is not just inaccurate—it causes catastrophic drilling surprises.
> 2. **The Hallucination Danger of Generic AI:** A generic LLM will confidently fabricate mud weights or pull forces. In petroleum engineering, an unverified AI guess can blow out a well.*
>
> *Today, we present **eRTMAC-NWIS**—an empirical, formation-aware, evidence-first intelligence system built strictly on petroleum physics and verified historical records."*

---

### [01:15 - 02:45] ACT 2: GEOCORE & STRATIGRAPHIC FORMATION CORRELATION
**Action:** Switch to browser Tab 1 (`/nexus.html`), navigate to Geological Correlation section.  
**Visual:** 3D Subsurface Trajectories and TVDSS Correlation View.

> *"Let us look at real drilling data. Here on screen are five real wells from the North Sea Volve field dataset, licensed from Equinor and the Norwegian Offshore Directorate.*
>
> *Look at Well 15/9-F-14 and its offset Well 15/9-F-12. If a drilling superintendent looks only at raw Measured Depth, Well F-14 hits the permeable Hugin sandstone at 2,965 meters MD. But Well F-12 penetrates the same formation at 2,780 meters MD—an apparent offset of nearly 200 meters!*
>
> *Watch what NWIS GeoCore does:*
> *It computes the Sawaryn minimum-curvature trajectory in under 0.05 milliseconds, calculates true vertical depth subsea (TVDSS), and correlates structural tops.*
>
> *In TVDSS, the two formation boundaries match within 5 meters!*
>
> *As our bit advances, NWIS projects a **50-to-100 meter Look-Ahead Horizon Radar**. It does not look at what is directly beside the bit—it looks at what the bit is about to penetrate in the next 4 hours of drilling. The superintendent sees hazards before the bit touches the formation."*

---

### [02:45 - 04:15] ACT 3: SENTINEL DOCUMENT AI & THE EVIDENCE PASSPORT
**Action:** Switch to browser Tab 2 (`/sentinel.html`).  
**Interaction:** Type into the engineering query box:  
`"Which offset wells experienced severe mud losses in the Hugin formation?"`  
Click **Execute Query**.

> *"Now let us interrogate the historical reports. We ask Sentinel: 'Which offset wells experienced severe mud losses in the Hugin formation?'*
>
> *Notice what happens in less than half a millisecond:*
> *NWIS does not blindly send this question to a cloud AI.*
> 1. *It parses the stratigraphic intent via the Sentinel Query Planner.*
> 2. *It runs a 4-mode hybrid search—filtering by formation top, spatial offset radius, and historical incident taxonomy.*
> 3. *It retrieves the exact paragraph from DDR Report #44 of Well 15/9-F-14.*
>
> *(Click on Evidence Passport icon in the UI)*
>
> *Look at this: Here is the **Evidence Passport**. It displays the original document name, the page number, the exact bounding box coordinates where OCR extracted the text, and the SHA-256 cryptographic hash of the PDF file.*
>
> *And most importantly: **The Evidence-or-Silence Invariant**. If no offset well has documented an incident in that formation, NWIS does not guess. It explicitly reports: 'NO HISTORICAL EVIDENCE DOCUMENTED IN THIS STRATUM.' In high-consequence drilling, silence is infinitely safer than speculation."*

---

### [04:15 - 05:45] ACT 4: CHRONOS HISTORICAL REPLAY & ZERO-LEAKAGE BACKTEST
**Action:** Switch to browser Tab 3 (`/chronos.html`).  
**Interaction:** Select Well `NO-15/9-F-14`. Click **Start Historical Replay** at Depth 2,850m MD.

> *"Any team can claim their AI works on paper. But how do you prove it to an Oil India rig superintendent?*
>
> *We built **NWIS Chronos**—an empirical time-travel validation laboratory.*
>
> *Here, we replay the historical drilling of Well F-14 on September 14, 2008. Notice the **Temporal Firewall**: All data from after September 14, 2008 is cryptographically frozen. The system has zero future-well knowledge.*
>
> *(Click 'Step Forward +25m')*
>
> *At 2,910 meters MD—55 meters before the actual kick occurred—NWIS fires a predictive advisory: 'Proximity Warning: Offset Well F-12 recorded 45 m³/hr total mud loss in Hugin sandstone at 2,860m TVDSS. Recommended action: Stage 25 ppb LCM pill.'*
>
> *We ran an automated Leave-One-Well-Out back-test across 1,759 Volve daily drilling reports. NWIS achieved a **75.0% operational precision** with an average advance warning lead time of **84.1 meters** ahead of the bit, eliminating over 80% of false alarms produced by raw distance-based matching."*

---

### [05:45 - 07:15] ACT 5: PULSE & NEXUS UNIFIED DRILLING INTELLIGENCE
**Action:** Switch to browser Tab 1 (`/nexus.html`).  
**Visual:** Show live WITSML telemetry feed, Context Priority Index (CPI) gauge, and Operations Log.

> *"On the live rig floor, drilling is dynamic. NWIS Pulse ingests real-time WITSML telemetry streams at up to 100 Hz—monitoring Standpipe Pressure, Torque, ROP, Flow In, and Flow Out.*
>
> *(Point to the Telemetry Quality Bar)*
> *Notice our data quality guard: If a sensor freezes or drops packets, Pulse instantly flags it as 'DEGRADED' and does not trigger false alarms.*
>
> *(Point to the Context Priority Index)*
> *In **NWIS Nexus**, all four systems fuse into a single real-time decision dashboard:*
> - *Geological Strata from GeoCore*
> - *Historical Precedents from Chronos*
> - *Verified Evidence from Sentinel*
> - *Live Sensor Anomalies from Pulse*
>
> *Nexus calculates the **Context Priority Index (CPI)**—a deterministic, explainable heuristic that ranks operational urgency without black-box neural networks.*
>
> *(Scroll down to Operations Journal)*
> *At the bottom, every advisory, query, and handover event is recorded in a tamper-evident cryptographic log with SHA-256 signatures, ready for regulatory compliance and shift handover."*

---

### [07:15 - 08:00] ACT 6: ARCHITECTURAL RIGOR, SECURITY & OIL INDIA IMPACT
**Visual:** Switch to Slide 10 ("Production Hardening & Deployment Architecture").

> *"To conclude, eRTMAC-NWIS is not a student prototype. It is an industrial-grade software platform:*
> - **177 automated tests** passing at 100%.
> - **37 REST API contract tests** validating every schema.
> - **Sub-5 millisecond response times** across all core engines.
> - **Air-Gapped Edge Ready:** Runs completely offline on remote rigs without cloud dependencies.
> - **Enterprise Security:** Multi-stage non-root Docker builds, sliding-window rate limiting, and cryptographic request tracing.
>
> *eRTMAC-NWIS turns Oil India's paper archives into an active, protective shield over every drilling bit.*
>
> *Thank you. We welcome your technical scrutiny and questions."*

---

## Contingency Playbook (What to Do If...)

| Scenario | Immediate Action | Explanation to Jury |
|---|---|---|
| **Internet Disconnected** | Continue seamlessly. | *"NWIS is designed for remote Assam drill sites; all data, embeddings, and models run 100% locally in-process."* |
| **Jury Asks for Raw Code** | Open VS Code / IDE. | Show `backend/app/services/stratigraphic_service.py` (minimum curvature) and `backend/tests/` (177 passing tests). |
| **Jury Doubts Data Authenticity** | Open `data/provenance_ledger_phase08.json`. | Show official NOD/Equinor open data licenses and SHA-256 file hashes. |
| **Jury Asks About Hallucinations** | Submit an invalid query in Sentinel: `"Which well drilled into volcanic basalt at 1000m?"` | Show the immediate, strict **Evidence-or-Silence** rejection message. |
