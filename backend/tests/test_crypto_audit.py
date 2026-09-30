"""
Phase 08 Cryptographic Integrity & Tamper-Evident Audit Verification Tests
Tests for:
1. Canonical serialization invariance
2. Authenticated HMAC-SHA256 signing
3. Payload modification detection
4. Timestamp tampering detection
5. Sequence reordering & injection attack prevention
6. Cryptographic hash-chain continuity
7. Key rotation & unauthorized signing key rejection
"""

import pytest
import copy
from backend.app.services.crypto_service import CryptographicAuditService, crypto_audit_service


def test_canonical_serialization_order_invariance():
    """Different key orders must produce identical canonical byte streams."""
    payload1 = {"well_id": "NO-15/9-F-14", "depth_md_m": 2965.0, "hazard": "LOST_CIRCULATION"}
    payload2 = {"hazard": "LOST_CIRCULATION", "well_id": "NO-15/9-F-14", "depth_md_m": 2965.0}

    bytes1 = CryptographicAuditService.canonical_serialize(payload1)
    bytes2 = CryptographicAuditService.canonical_serialize(payload2)

    assert bytes1 == bytes2
    assert b"NO-15/9-F-14" in bytes1


def test_sign_and_verify_valid_audit_event():
    """A cleanly signed event must verify successfully."""
    payload = {
        "event_id": "EVT-TEST-001",
        "action": "ADVISORY_ACKNOWLEDGED",
        "operator": "DELL_RIG_SUPERVISOR",
        "well_id": "NO-15/9-F-14"
    }

    signed = crypto_audit_service.sign_audit_event(payload, sequence_id=1)
    assert "signature" in signed
    assert len(signed["signature"]) == 64

    is_valid, msg = crypto_audit_service.verify_audit_event(
        signed["envelope"],
        signed["signature"]
    )
    assert is_valid is True
    assert msg == "VERIFIED_AUTHENTIC"


def test_detect_deliberate_payload_tampering():
    """Modifying even one character in the signed payload must be caught by signature verification."""
    payload = {
        "event_id": "EVT-TEST-002",
        "action": "WELL_STATUS_UPDATE",
        "severity": "CRITICAL",
        "bit_depth_m": 3105.0
    }

    signed = crypto_audit_service.sign_audit_event(payload, sequence_id=2)

    # Attacker attempts to downgrade severity from CRITICAL to MINOR
    tampered_envelope = copy.deepcopy(signed["envelope"])
    tampered_envelope["payload"]["severity"] = "MINOR"

    is_valid, msg = crypto_audit_service.verify_audit_event(
        tampered_envelope,
        signed["signature"]
    )
    assert is_valid is False
    assert "SIGNATURE_MISMATCH" in msg


def test_detect_timestamp_tampering():
    """Modifying the signing timestamp must invalidate the cryptographic signature."""
    payload = {"event_id": "EVT-TEST-003", "action": "SHIFT_HANDOVER"}
    signed = crypto_audit_service.sign_audit_event(payload, sequence_id=3)

    tampered_envelope = copy.deepcopy(signed["envelope"])
    tampered_envelope["signed_at"] = "2020-01-01T00:00:00Z"

    is_valid, msg = crypto_audit_service.verify_audit_event(
        tampered_envelope,
        signed["signature"]
    )
    assert is_valid is False
    assert "SIGNATURE_MISMATCH" in msg


def test_cryptographic_hash_chain_continuity():
    """A series of sequentially chained records must verify cleanly."""
    chain = []
    prev_sig = None

    for i in range(1, 6):
        payload = {"step": i, "remark": f"Rig operations log entry #{i}"}
        rec = crypto_audit_service.sign_audit_event(
            payload=payload,
            sequence_id=i,
            prev_signature=prev_sig
        )
        chain.append(rec)
        prev_sig = rec["signature"]

    is_valid, errors = crypto_audit_service.verify_audit_chain(chain)
    assert is_valid is True
    assert len(errors) == 0


def test_detect_chain_record_deletion_attack():
    """Dropping a record from the middle of the chain must be caught by sequence and linkage checks."""
    chain = []
    prev_sig = None

    for i in range(1, 6):
        payload = {"step": i, "event": f"Audit step {i}"}
        rec = crypto_audit_service.sign_audit_event(payload, sequence_id=i, prev_signature=prev_sig)
        chain.append(rec)
        prev_sig = rec["signature"]

    # Delete record #3 (index 2)
    tampered_chain = [chain[0], chain[1], chain[3], chain[4]]

    is_valid, errors = crypto_audit_service.verify_audit_chain(tampered_chain)
    assert is_valid is False
    assert any("Expected sequence" in e or "Broken chain link" in e for e in errors)


def test_detect_chain_reordering_attack():
    """Swapping two records in the chain must be caught immediately."""
    chain = []
    prev_sig = None

    for i in range(1, 5):
        payload = {"step": i}
        rec = crypto_audit_service.sign_audit_event(payload, sequence_id=i, prev_signature=prev_sig)
        chain.append(rec)
        prev_sig = rec["signature"]

    # Swap record 2 and record 3
    tampered_chain = [chain[0], chain[2], chain[1], chain[3]]

    is_valid, errors = crypto_audit_service.verify_audit_chain(tampered_chain)
    assert is_valid is False
    assert len(errors) > 0


def test_reject_unauthorized_signing_key():
    """Signing with an unauthorized key must fail verification against the trusted system key."""
    payload = {"event_id": "EVT-TEST-ROGUE", "action": "FORGE_REPORT"}
    rogue_key = "ROGUE_UNAUTHORIZED_PRIVATE_KEY_12345"

    signed = crypto_audit_service.sign_audit_event(
        payload, sequence_id=1, secret_key=rogue_key, key_id="rogue-key"
    )

    # Verify against authorized system settings.SECRET_KEY
    is_valid, msg = crypto_audit_service.verify_audit_event(
        signed["envelope"],
        signed["signature"]
    )
    assert is_valid is False
    assert "SIGNATURE_MISMATCH" in msg
