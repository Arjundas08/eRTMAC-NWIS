"""
NWIS Atlas Real Performance Benchmarking Script (Phase 08)

Benchmarks genuine operational workloads across all core engines:
1. GeoCore Minimum Curvature trajectory interpolation
2. Stratigraphic formation correlation
3. Sentinel hybrid evidence retrieval
4. Pulse telemetry normalization & quality gating
5. Nexus deep cross-module intelligence fusion
6. Cryptographic HMAC event signing & chain verification

Measures: Median (p50), p95, p99, Min, Max, Throughput (ops/sec).
Distinguishes deterministic retrieval from external LLM synthesis.
"""

import time
import statistics
import sys
from pathlib import Path
from typing import List, Dict, Any

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.db.database import SessionLocal
from backend.app.services.nexus_engine import NexusEngine
from backend.app.services.trajectory_engine import TrajectoryEngine
from backend.app.services.formation_correlation_service import formation_correlation_service
from backend.app.services.telemetry_normalizer import canonicalize_packet
from backend.app.services.telemetry_quality_service import TelemetryQualityEngine
from backend.app.services.crypto_service import crypto_audit_service
from backend.app.services.sentinel_query_planner import SentinelQueryPlanner
from backend.app.services.sentinel_retrieval_engine import SentinelRetrievalEngine


def run_benchmark(name: str, fn, iterations: int = 50) -> Dict[str, Any]:
    latencies_ms: List[float] = []

    # Warmup
    for _ in range(5):
        fn()

    # Measured runs
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        t1 = time.perf_counter()
        latencies_ms.append((t1 - t0) * 1000.0)

    latencies_ms.sort()
    p50 = statistics.median(latencies_ms)
    p95 = latencies_ms[int(iterations * 0.95)]
    p99 = latencies_ms[min(int(iterations * 0.99), iterations - 1)]
    mean = statistics.mean(latencies_ms)
    ops_sec = 1000.0 / mean if mean > 0 else 0.0

    return {
        "operation": name,
        "iterations": iterations,
        "mean_ms": round(mean, 2),
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2),
        "min_ms": round(latencies_ms[0], 2),
        "max_ms": round(latencies_ms[-1], 2),
        "throughput_ops_sec": round(ops_sec, 1)
    }


def main():
    print("=" * 80)
    print("NWIS ATLAS EMPIRICAL PERFORMANCE BENCHMARK SUITE")
    print("=" * 80)
    print("Environment: Python 3.13 / Intel Core / SQLite Local Relational Store")
    print("Workload: Genuine database queries and analytical computations (No mocks)")
    print()

    db = SessionLocal()
    quality_engine = TelemetryQualityEngine()

    benchmarks = [
        (
            "GeoCore Trajectory Calculation (Sawaryn Minimum Curvature)",
            lambda: TrajectoryEngine.minimum_curvature_step(
                md1=2500.0, inc1_deg=28.5, azi1_deg=120.0,
                md2=2965.0, inc2_deg=42.0, azi2_deg=145.0
            )
        ),
        (
            "Stratigraphic Formation Correlation (TVDSS Lookup)",
            lambda: formation_correlation_service.correlate_formations(
                db=db,
                target_well_id="NO-15/9-F-14",
                offset_well_id="NO-15/9-F-12",
                target_depth_md_m=2965.0
            )
        ),
        (
            "Pulse Telemetry Packet Canonicalization & Normalization",
            lambda: canonicalize_packet({
                "DMEA": {"value": 9727.69, "unit": "ft"},
                "ROPA": {"value": 41.0, "unit": "ft/h"},
                "WOBA": {"value": 22.0, "unit": "klbs"},
                "SPPA": {"value": 3200.0, "unit": "psi"}
            })
        ),
        (
            "Pulse Telemetry Quality Assessment & Deduplication",
            lambda: quality_engine.assess_packet(
                packet_id="PKT_BENCH",
                raw_payload='{"MD": 2965.0, "ROP": 12.5}',
                timestamp_str="2026-09-30T00:00:00Z",
                canonical_channels={"MD": 2965.0}
            )
        ),
        (
            "Sentinel Hybrid Evidence Retrieval (Plan + DB Chunks)",
            lambda: SentinelRetrievalEngine.execute_hybrid_retrieval(
                db=db,
                query_plan=SentinelQueryPlanner.parse_query("lost circulation in Hugin formation")
            )
        ),
        (
            "Nexus Deep Cross-Module Fusion (GeoCore+Pulse+Chronos+Sentinel)",
            lambda: NexusEngine.fuse_well_intelligence(db=db, well_id="NO-15/9-F-14")
        ),
        (
            "Nexus Operations Log Aggregation (50 records)",
            lambda: NexusEngine.get_operations_log(db=db, limit=50)
        ),
        (
            "Cryptographic HMAC-SHA256 Signing & Hash-Chain Verification",
            lambda: crypto_audit_service.sign_audit_event(
                payload={"well_id": "NO-15/9-F-14", "action": "BENCHMARK_SIGN"},
                sequence_id=1,
                prev_signature="PREV_SIG_HEX"
            )
        )
    ]

    results = []
    for title, fn in benchmarks:
        print(f"Benchmarking: {title}...")
        res = run_benchmark(title, fn, iterations=50)
        results.append(res)
        print(f"  -> p50: {res['p50_ms']}ms | p95: {res['p95_ms']}ms | p99: {res['p99_ms']}ms | Throughput: {res['throughput_ops_sec']} ops/s")

    db.close()

    print("\n" + "=" * 80)
    print(f"{'Workload Name':<50} | {'p50 (ms)':<8} | {'p95 (ms)':<8} | {'Ops/Sec':<8}")
    print("-" * 80)
    for r in results:
        print(f"{r['operation'][:48]:<50} | {r['p50_ms']:<8} | {r['p95_ms']:<8} | {r['throughput_ops_sec']:<8}")
    print("=" * 80)


if __name__ == "__main__":
    main()
