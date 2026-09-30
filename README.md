# eRTMAC-NWIS (Nearby Wells Intelligence System)
### An AI-Powered Offset Well Knowledge and Decision Support Platform for Drilling Operations
**Problem Statement ID:** SIH26121 | **Organization:** Oil India Limited (OIL) | **Category:** Software / Smart Automation

---

## 1. Overview & Operational Boundary
eRTMAC-NWIS is a production-grade offset well intelligence and institutional drilling memory platform designed to bridge the gap between Oil India Limited's **eRTMAC** (24/7 Real-Time Monitoring and Analytics Center) and OIL's **E&P Databank / Legacy Archives**.

* **eRTMAC:** Owns the live telemetry plane (*"What is happening right now in the active well?"*).
* **OIL E&P Databank:** Owns long-term archival storage (*"Where are the 100,000+ historical scanned pages and records?"*).
* **NWIS (This Platform):** Owns the cognitive correlation and look-ahead plane (*"What happened in comparable offset wells at this exact stratigraphic formation/depth, what evidence supports it, and what should the engineer investigate 50–100m ahead of the bit?"*).

---

## 2. Architecture & Data Principles
1. **Zero Fabricated Records:** Base validation and demonstration run exclusively on officially licensed real petroleum data from the **Equinor Volve Field dataset** (1,759 Daily Drilling Reports, WITSML, 26 wellbores) and **NOPIMS (Australia)** for legacy OCR validation.
2. **Dual-Backend Storage Engine:**
   - **Production Mode:** PostgreSQL 16 + PostGIS 3.4 + pgvector (for enterprise on-premise OIL deployment via Docker/Kubernetes).
   - **Local Standalone Mode:** Embedded SQLite/DuckDB + exact spatial/ellipsoidal math + pure Python vector cosine indexing (for zero-dependency testing and rapid development on any developer machine).
3. **Stratigraphic Depth Alignment:** Corrects for structural dip by converting Measured Depth (MD) to True Vertical Depth Subsea (TVDSS) using the API Minimum Curvature Method and referencing Stratigraphic Formation Marker Tops.
4. **Evidence-or-Silence Contract:** The system never hallucinates advice. Every alert cites the specific offset well, report, page number, and historical depth. If no offset data exists, NWIS explicitly reports no precedent.
5. **Human-in-the-Loop Advisory:** Strictly non-actuating; no direct rig machinery control.

---

## 3. Quickstart: Local Standalone Execution (Windows / Linux / macOS)

### Prerequisites
- Python 3.11+ (Python 3.13 supported)
- Node.js 18+ (for frontend dashboard)

### Step 1: Clone & Configure Environment
```bash
cd ertmac-nwis
cp .env.example .env
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Ingest Verified Volve Dataset
```bash
python scripts/ingest_volve_data.py
```
This loads verified real well headers, directional surveys, formation tops, and real DDR operational events into the database while recording SHA-256 provenance hashes.

### Step 4: Run Automated Test Suite
```bash
pytest backend/tests -v
```

### Step 5: Start the NWIS Backend Server
```bash
python backend/app/main.py
```
The API server launches at `http://127.0.0.1:8000`.
- Interactive Swagger Documentation: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

---

## 4. Docker Production Deployment (PostgreSQL + PostGIS + pgvector)

```bash
docker compose up -d --build
```
This boots:
- `db`: PostgreSQL 16 with PostGIS and pgvector extensions.
- `backend`: FastAPI async microservices.
- `cache`: Redis for high-frequency 1-second telemetry buffers.

---

## 5. Repository Layout
```text
ertmac-nwis/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Typed FastAPI route endpoints (wells, similarity, lookahead, ask, audit)
│   │   ├── core/           # Security, audit logger, config settings
│   │   ├── db/             # Dual engine (PostgreSQL/PostGIS + SQLite fallback), models
│   │   ├── schemas/        # Pydantic v2 validation contracts
│   │   ├── services/       # Stratigraphic math, similarity ranking, look-ahead radar
│   │   └── main.py         # Application entrypoint
│   └── tests/              # Pytest automated test suite
├── config/                 # Environment configuration
├── data/raw/volve/         # Verified real Volve field data & license metadata
├── scripts/                # Ingestion, LOWO back-testing, telemetry streamer
├── docker-compose.yml      # Production container orchestration
└── requirements.txt        # Production Python dependencies
```

---

## 6. License & Provenance
The sample drilling records in `data/raw/volve` originate from the **Equinor Volve Field Data**, shared under the CC BY-NC-SA 4.0 license for research and study purposes. See `data/raw/volve/LICENSE.txt` and `provenance.json` for details.
