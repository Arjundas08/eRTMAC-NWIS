# NWIS PULSE — INDUSTRIAL CYBERSECURITY & SAFETY BOUNDARIES
**Phase:** 06 — Industrial Drilling Telemetry & Integration  
**Standard:** SIH26121 Section 18  
**Author:** Industrial Cybersecurity Architect & Reliability Engineer  
**Status:** IMPLEMENTED & ENFORCED  

---

## 1. The Strict Read-Only Integration Boundary

A fundamental cybersecurity and industrial safety requirement of the Nearby Wells Intelligence System (NWIS) is the **strict, unidirectional read-only boundary**:

1. **Zero Equipment Control:** Under no circumstances does NWIS transmit control packets, commands, setpoints, or override signals to programmable logic controllers (PLCs), mud pumps, top drives, drawworks, iron roughnecks, or blowout preventers (BOPs).
2. **Software Enforcement:**
   - In `TelemetrySource`, the flag `is_read_only = Column(Boolean, default=True)` is immutable.
   - In `ETP12Adapter`, capability negotiation enforces `is_read_only: True` and rejects write operations.
   - The REST API contains no setpoint or control endpoints.

---

## 2. Authentication, Authorization & RBAC

NWIS PULSE adheres to least-privilege role-based access control (RBAC):

| Role | Telemetry Streaming | Quality Inspector | Advisory Acknowledgment | Rule Editing | Source Registration |
|---|---|---|---|---|---|
| `DRILLING_ENGINEER` | View Only | View Only | Review & Comment | View Only | Forbidden |
| `DRILLING_SUPERINTENDENT` | View Only | View Only | **Acknowledge / Resolve / Suppress** | View Only | Forbidden |
| `CHIEF_DRILLING_ENGINEER` | View Only | View Only | Full Review Authority | **Approve Rule Versions** | Forbidden |
| `SYSTEM_ADMINISTRATOR` | Monitor | Full Audit | Audit Trail Only | Audit Trail Only | **Register Sources** |

---

## 3. Cryptographic Audit Trail & Non-Repudiation

All human interactions with operational advisories (acknowledgements, suppressions, reviews, resolutions) are captured in `AdvisoryReviewEvent`:
- Immutable event records with UTC timestamps.
- Records `actor_id`, `actor_role`, `old_state`, `new_state`, and engineering justification comments.
- Tamper-evident logging protects against retrospective operational disputes.

---

## 4. Source Isolation & Cross-Well Boundaries

- **Cross-Well Tenant Isolation:** Ingestion pipelines validate wellbore ownership before persisting packets.
- **Source Mode Integrity:** Synthetic demonstration packets are strictly quarantined and cannot overwrite genuine historical baseline metrics.
