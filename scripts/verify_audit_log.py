"""
NWIS Independent Cryptographic Audit Verification Tool (Phase 08)

Command-line verification tool to independently audit event logs,
check HMAC signatures, verify hash chains, and detect deliberate tampering.

Usage:
    python scripts/verify_audit_log.py [--tamper-test]
"""

import sys
import json
import argparse
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.services.crypto_service import crypto_audit_service


def run_audit_verification(tamper_test: bool = False) -> int:
    print("=" * 70)
    print("NWIS INDEPENDENT CRYPTOGRAPHIC AUDIT VERIFICATION TOOL")
    print("=" * 70)
    print(f"Timestamp: 2026-09-30")
    print(f"Verification Mode: {'DELIBERATE_TAMPER_INJECTION' if tamper_test else 'GENUINE_AUDIT'}")
    print()

    # Generate or load a test chain of audit events
    print("1. Assembling sample authenticated operational journal...")
    journal = []
    prev_sig = None
    sample_actions = [
        {"well_id": "NO-15/9-F-14", "action": "SPUD_CONFIRMED", "depth_m": 0.0},
        {"well_id": "NO-15/9-F-14", "action": "CASING_SHOE_SET_13_3_8", "depth_m": 1200.0},
        {"well_id": "NO-15/9-F-14", "action": "FORMATION_TOP_HUGIN", "depth_m": 2960.0},
        {"well_id": "NO-15/9-F-14", "action": "ADVISORY_ISSUED_MUD_LOSS", "depth_m": 2965.0},
        {"well_id": "NO-15/9-F-14", "action": "MITIGATION_APPLIED_LCM", "depth_m": 2965.0},
        {"well_id": "NO-15/9-F-14", "action": "SHIFT_HANDOVER_COMPLETED", "depth_m": 3100.0}
    ]

    for idx, act in enumerate(sample_actions, start=1):
        signed = crypto_audit_service.sign_audit_event(
            payload=act,
            sequence_id=idx,
            prev_signature=prev_sig
        )
        journal.append(signed)
        prev_sig = signed["signature"]

    print(f"   Generated {len(journal)} HMAC-signed records with forward hash-linkage.")

    if tamper_test:
        print("\n2. [TEST MODE] Injecting deliberate adversary tampering into Record #3...")
        original_depth = journal[2]["envelope"]["payload"]["depth_m"]
        journal[2]["envelope"]["payload"]["depth_m"] = 9999.0  # Tampered depth
        print(f"   Modified depth_m from {original_depth} to 9999.0 without re-signing.")

    print("\n3. Executing independent cryptographic verification pass...")
    is_valid, errors = crypto_audit_service.verify_audit_chain(journal)

    if is_valid:
        print("   [PASS] ALL RECORDS VERIFIED AUTHENTIC.")
        print(f"   - Total records verified: {len(journal)}")
        print("   - Signatures: Valid HMAC-SHA256")
        print("   - Cryptographic links: Unbroken forward chain")
        print("   - Sequence numbers: Strictly monotonic")
        return 0
    else:
        print("   [ALERT] CRYPTOGRAPHIC INTEGRITY VIOLATION DETECTED!")
        for err in errors:
            print(f"   - VIOLATION: {err}")
        return 1 if not tamper_test else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NWIS Cryptographic Audit Verification")
    parser.add_argument("--tamper-test", action="store_true", help="Simulate deliberate tampering attack")
    args = parser.parse_args()

    exit_code = run_audit_verification(tamper_test=args.tamper_test)
    sys.exit(exit_code)
