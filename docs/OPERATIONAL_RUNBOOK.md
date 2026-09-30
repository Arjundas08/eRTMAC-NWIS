# eRTMAC-NWIS — Operational Runbook (Phase 09)
## Field-Pilot Deployment, Monitoring & Incident Response

**Document Version:** 1.0.0  
**Classification:** INTERNAL — Oil India Limited Engineering Operations  
**Last Updated:** 2026-09-30  

---

## 1. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   eRTMAC Rig-Side Server                     │
│                                                               │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────────────┐  │
│  │PostgreSQL│  │   Redis    │  │   NWIS Backend (FastAPI) │  │
│  │ +PostGIS │  │  (Cache)   │  │   Port 8000              │  │
│  │ Port 5432│  │  Port 6379 │  │   Workers: 2             │  │
│  └──────────┘  └───────────┘  └──────────────────────────┘  │
│                                         │                     │
│                          ┌──────────────┴──────────────┐     │
│                          │   Static Frontend (SPA)     │     │
│                          │   Served from /frontend/    │     │
│                          └─────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Pre-Deployment Checklist

### 2.1 Secrets Configuration
- [ ] Generate production SECRET_KEY: `python -c "import secrets; print(secrets.token_urlsafe(64))"`
- [ ] Set POSTGRES_PASSWORD to a strong random value (min 32 characters)
- [ ] Set REDIS_PASSWORD to a strong random value
- [ ] Create `.env.production` from `.env.example` template
- [ ] Verify `.env.production` is in `.gitignore`
- [ ] Verify no hardcoded secrets in source code: `grep -r "CHANGE_IN_PROD" backend/`

### 2.2 Database Preparation
- [ ] Run PostgreSQL schema: `psql -f deploy/schema_postgres.sql`
- [ ] Verify PostGIS extension: `SELECT PostGIS_Version();`
- [ ] Verify pgvector extension: `SELECT extversion FROM pg_extension WHERE extname='vector';`
- [ ] Run data ingestion: `python scripts/ingest_volve_data.py`
- [ ] Verify well count: `SELECT COUNT(*) FROM wells;` (expect ≥ 5)

### 2.3 Network & Firewall
- [ ] Port 8000 accessible from eRTMAC monitoring stations
- [ ] Port 5432 accessible ONLY from localhost/backend container
- [ ] Port 6379 accessible ONLY from localhost/backend container
- [ ] CORS origins configured for actual deployment domain

---

## 3. Startup Procedures

### 3.1 Docker Compose Deployment (Recommended)

```bash
# Pull latest images
docker compose pull

# Build application image
docker compose build --no-cache

# Start all services
docker compose --env-file .env.production up -d

# Verify all services are healthy
docker compose ps
docker compose logs --tail=50 backend
```

### 3.2 Direct Python Deployment (Development/Testing)

```bash
# Install dependencies
pip install -r requirements.txt

# Ingest data
python scripts/ingest_volve_data.py

# Start server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 3.3 Startup Verification Sequence

```bash
# 1. Health check
curl http://localhost:8000/health
# Expected: {"status": "healthy", "environment": "production", "database_backend": "PostgreSQL_PostGIS"}

# 2. API status
curl http://localhost:8000/api/v1/status
# Expected: {"status": "OPERATIONAL", ...}

# 3. System-wide health (all modules)
curl http://localhost:8000/api/v1/nexus/health
# Expected: All modules show "OPERATIONAL" or "DEGRADED" (never "OFFLINE" after data load)

# 4. Well data loaded
curl http://localhost:8000/api/v1/wells/
# Expected: Array of 5 Volve wells

# 5. KPI dashboard
curl http://localhost:8000/api/v1/nexus/kpis
# Expected: Non-zero evidence quality and event counts
```

---

## 4. Monitoring & Alerting

### 4.1 Health Check Endpoints

| Endpoint | Frequency | Alert If |
|---|---|---|
| `GET /health` | Every 30s | Status ≠ "healthy" |
| `GET /api/v1/nexus/health` | Every 60s | Any module = "OFFLINE" |
| `GET /api/v1/nexus/kpis` | Every 5m | Evidence quality < 50% |

### 4.2 Key Metrics to Monitor

| Metric | Source | Warning Threshold | Critical Threshold |
|---|---|---|---|
| API Response Latency (p95) | Access logs / X-Request-ID correlation | > 500ms | > 2000ms |
| Database Connection Pool | PostgreSQL `pg_stat_activity` | > 80% utilized | > 95% utilized |
| Telemetry Ingestion Rate | Pulse `/api/v1/pulse/sources` | < 1 packet/min | 0 packets/5min |
| Disk Usage (data volume) | `docker system df` | > 80% | > 95% |
| Memory Usage | `docker stats` | > 80% limit | > 95% limit |
| Rate Limit 429s | Access logs | > 10/min | > 50/min |

### 4.3 Log Files

| Log | Location | Purpose |
|---|---|---|
| Application Access Log | stdout (Docker `json-file` driver) | Request tracking |
| Uvicorn Error Log | stderr | Application errors |
| PostgreSQL Log | Docker volume `postgres_data` | Query performance |
| Audit Trail | `audit_events` table + HMAC chain | Compliance |

---

## 5. Shutdown Procedures

### 5.1 Graceful Shutdown

```bash
# Docker Compose
docker compose down

# Direct deployment
# Send SIGTERM to uvicorn process (it will finish in-flight requests)
kill -TERM $(pgrep -f "uvicorn backend.app.main")
```

### 5.2 Emergency Shutdown

```bash
docker compose down --timeout 5
# or
docker compose kill
```

---

## 6. Incident Response

### 6.1 Common Issues

| Symptom | Likely Cause | Resolution |
|---|---|---|
| 500 errors on `/api/v1/nexus/fuse/*` | Database connection timeout | Check PostgreSQL health, restart if needed |
| All requests return 429 | Rate limiter triggered | Verify client IP, increase limit if legitimate |
| "DEGRADED" module status | Missing data or stale telemetry | Re-run `ingest_volve_data.py`, check data files |
| "OFFLINE" Sentinel | No knowledge chunks in DB | Re-run document ingestion pipeline |
| Slow responses (> 1s) | Database index missing | Run `ANALYZE;` in PostgreSQL |

### 6.2 Database Recovery

```bash
# Check database integrity
docker compose exec db pg_isready -U nwis_user -d nwis_db

# Rebuild indexes if needed
docker compose exec db psql -U nwis_user -d nwis_db -c "REINDEX DATABASE nwis_db;"

# Full backup
docker compose exec db pg_dump -U nwis_user nwis_db > backup_$(date +%Y%m%d).sql
```

---

## 7. Testing in Production

### 7.1 Smoke Test Script

```bash
# Run from any machine with network access to the NWIS server
curl -s http://NWIS_HOST:8000/health | python -m json.tool
curl -s http://NWIS_HOST:8000/api/v1/status | python -m json.tool
curl -s http://NWIS_HOST:8000/api/v1/nexus/health | python -m json.tool
curl -s http://NWIS_HOST:8000/api/v1/wells/ | python -m json.tool
```

### 7.2 Contract Test Execution

```bash
# Run the full API contract test suite
python -m pytest backend/tests/test_api_contracts.py -v

# Run all tests (140+ existing + new contract tests)
python -m pytest backend/tests/ -v --tb=short
```

---

## 8. Backup & Recovery

### 8.1 Automated Backup Schedule

| Component | Frequency | Retention |
|---|---|---|
| PostgreSQL (full dump) | Daily at 02:00 UTC | 30 days |
| Data files (`data/`) | Daily incremental | 90 days |
| Configuration (`.env.production`) | On change | Vault versioned |
| Docker volumes | Weekly snapshot | 14 days |

### 8.2 Restore Procedure

```bash
# 1. Stop the application
docker compose down

# 2. Restore database from backup
docker compose up -d db
docker compose exec -T db psql -U nwis_user -d nwis_db < backup_YYYYMMDD.sql

# 3. Restore data files
# Copy backup data files to ./data/

# 4. Start application
docker compose up -d
```
