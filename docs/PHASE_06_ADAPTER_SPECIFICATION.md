# NWIS PULSE — UNIVERSAL INDUSTRIAL DATA ADAPTER SPECIFICATION
**Phase:** 06 — Industrial Drilling Telemetry & Integration  
**Standard:** SIH26121 Signature Innovation 01  
**Author:** Industrial Integration Architect & Petroleum Data Engineer  
**Status:** IMPLEMENTED & VERIFIED  

---

## 1. Overview & Objectives

NWIS PULSE provides an industrial-grade, standards-compliant ingestion and telemetry normalization layer connecting real-time surface and downhole measurements to the NWIS intelligence ecosystem.

To maintain strict operational boundaries, NWIS adheres to a **read-only ingestion contract**. It does not control rig equipment, mud pumps, or top drives.

---

## 2. Implemented Protocol Adapters

| Adapter | Standard / Version | Transport | Data Mode | Supported Objects / Schemas |
|---|---|---|---|---|
| `WITSML1411Adapter` | Energistics WITSML 1.4.1.1 | HTTP POST / SOAP XML | `AUTHORIZED_LIVE` / `GENUINE_RECORDED_REPLAY` | `<log>`, `<logCurveInfo>`, `<data>`, `<trajectory>`, `<wellbore>` |
| `WITSML21Adapter` | Energistics WITSML 2.1 | REST / JSON & XML | `AUTHORIZED_LIVE` / `GENUINE_RECORDED_REPLAY` | Log `ChannelSet`, `Channel`, Energistics UOMs |
| `ETP12Adapter` | Energistics ETP 1.2 | WebSocket (RFC 6455) | `AUTHORIZED_LIVE` | Protocol 1 (Core), Protocol 2 (ChannelStreaming), Protocol 3 (Store) |
| `HistoricalReplayAdapter` | Volve Traceable Dataset | Internal Stream | `GENUINE_RECORDED_REPLAY` | Time-indexed, depth-indexed continuous logs (Equinor Volve open data) |
| `SyntheticDemoAdapter` | Isolated Simulation | In-Memory Generator | `SYNTHETIC_DEMO` | Fault injection, packet drop, sensor drift, jitter stress testing |

---

## 3. Strict Source-Mode Separation

NWIS PULSE visually and architecturally segregates telemetry into three mutually exclusive modes:

1. **Mode 1 (`AUTHORIZED_LIVE`):**
   - Active external connection to operator/service company WITSML servers or ETP streaming brokers.
   - Requires verified API keys or bearer credentials.
   - Watermark: Blue Industrial Indicator (`LIVE RIG STREAM`).
2. **Mode 2 (`GENUINE_RECORDED_REPLAY`):**
   - Replay of authentic, verified historical drilling logs (Equinor Volve field: wells 15/9-F-12, 15/9-F-14, 15/9-F-11).
   - Preserves original chronological timestamps and sampling frequencies.
   - Watermark: Cyan/Teal Indicator (`HISTORICAL RECORDED REPLAY`).
3. **Mode 3 (`SYNTHETIC_DEMO`):**
   - Procedurally generated data designed solely for software resilience testing (fault injection, network disconnection, sensor jitter).
   - Strictly tagged in every database record and UI view.
   - Watermark: Amber / Orange High-Visibility Badge (`SYNTHETIC DEMONSTRATION — NOT REAL DATA`).

---

## 4. WITSML Parsing Details

### 4.1 WITSML 1.4.1.1 Engine
- Extracts mnemonics and engineering units from `<logCurveInfo>` blocks.
- Strips XML namespaces dynamically to prevent parsing failures on vendor schema variants.
- Parses comma-separated values from `<data>` records and aligns them with curve headers.

### 4.2 WITSML 2.1 Capability Subset
- Full support for Energistics 2.1 JSON and XML channel payloads.
- Validates standard Energistics unit-of-measure (UOM) strings (e.g., `m/s`, `m/h`, `kPa`, `N`, `kN`, `kg/m3`).

### 4.3 ETP 1.2 Capability Contract
- Implements ETP 1.2 session negotiation sub-protocols:
  - Protocol 1 (Core): Version negotiation, max data object size ($10\,\text{MB}$).
  - Protocol 2 (ChannelStreaming): Streaming channel descriptors and point payloads.
  - Read-Only Enforcement: Enforced at the protocol handshake layer (`is_read_only=True`).

---

## 5. Verification & Testing

The adapter subsystem is thoroughly tested in `backend/tests/test_pulse.py`:
- `test_witsml_1411_adapter_parsing`: Validates XML curve extraction and row parsing.
- `test_witsml_21_adapter_json`: Validates JSON ChannelSet ingestion.
- `test_etp_12_adapter_capabilities_negotiation`: Validates protocol negotiation and read-only enforcement.
