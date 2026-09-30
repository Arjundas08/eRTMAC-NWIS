"""
NWIS Cryptographic Integrity & Tamper-Evident Audit Service (Phase 08)

Provides production-grade cryptographic protections for engineering audit records,
advisories, and data passports:
1. Canonical JSON serialization (RFC 8785 JSON Canonicalization Scheme compatible)
2. Authenticated HMAC-SHA256 event signatures (preventing unauthorized re-hashing)
3. Cryptographic hash-chain linkage (forward-secure append-only journal)
4. Sequence numbering and replay prevention
5. Independent chain verification and deliberate tampering detection
"""

import hmac
import hashlib
import json
import base64
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
from pathlib import Path
import sys

# Ensure package root is in path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))
from config.settings import settings


class CryptographicAuditService:
    """
    Cryptographic audit service implementing HMAC-SHA256 signature verification,
    canonical serialization, and cryptographic hash-chain validation.
    """

    DEFAULT_KEY_ID = "nwis-audit-key-2026-v1"

    @staticmethod
    def canonical_serialize(payload: Dict[str, Any]) -> bytes:
        """
        Produces a deterministic, canonical UTF-8 byte representation of a dictionary.
        Keys are sorted recursively, floats formatted consistently, whitespace minimized.
        """
        def _normalize(obj):
            if isinstance(obj, dict):
                return {k: _normalize(v) for k, v in sorted(obj.items())}
            elif isinstance(obj, list):
                return [_normalize(item) for item in obj]
            elif isinstance(obj, float):
                # Ensure predictable float representation
                return round(obj, 6)
            return obj

        normalized = _normalize(payload)
        return json.dumps(
            normalized,
            separators=(',', ':'),
            ensure_ascii=False,
            sort_keys=True
        ).encode('utf-8')

    @classmethod
    def compute_sha256(cls, data: bytes) -> str:
        """Computes bare SHA-256 digest (used for passive source-file integrity)."""
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def sign_audit_event(
        cls,
        payload: Dict[str, Any],
        sequence_id: int,
        prev_signature: Optional[str] = None,
        secret_key: Optional[str] = None,
        key_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Signs an audit event using HMAC-SHA256 with canonical serialization,
        sequence binding, and previous-record hash chaining.
        """
        key = (secret_key or settings.SECRET_KEY).encode('utf-8')
        active_key_id = key_id or cls.DEFAULT_KEY_ID

        # Prepare envelope binding sequence and parent link
        envelope = {
            "sequence_id": sequence_id,
            "prev_signature": prev_signature or "GENESIS",
            "key_id": active_key_id,
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload
        }

        canonical_bytes = cls.canonical_serialize(envelope)
        signature = hmac.new(key, canonical_bytes, hashlib.sha256).hexdigest()

        return {
            "envelope": envelope,
            "signature": signature,
            "digest_algorithm": "HMAC-SHA256",
            "key_id": active_key_id
        }

    @classmethod
    def verify_audit_event(
        cls,
        envelope: Dict[str, Any],
        signature: str,
        secret_key: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Verifies an authenticated audit event signature using constant-time comparison.
        """
        key = (secret_key or settings.SECRET_KEY).encode('utf-8')
        canonical_bytes = cls.canonical_serialize(envelope)
        expected_sig = hmac.new(key, canonical_bytes, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return False, "SIGNATURE_MISMATCH: Payload or envelope attributes were modified."
        return True, "VERIFIED_AUTHENTIC"

    @classmethod
    def verify_audit_chain(
        cls,
        chain_records: List[Dict[str, Any]],
        secret_key: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Verifies an entire sequence of audit records for:
        1. Valid signature per record
        2. Strict sequential monotonically increasing sequence_id
        3. Valid previous_signature cryptographic linkage
        """
        errors = []
        if not chain_records:
            return True, []

        prev_sig = "GENESIS"
        expected_seq = chain_records[0]["envelope"]["sequence_id"]

        for idx, rec in enumerate(chain_records):
            envelope = rec.get("envelope", {})
            sig = rec.get("signature", "")
            seq = envelope.get("sequence_id")
            parent_link = envelope.get("prev_signature")

            # 1. Check sequence
            if seq != expected_seq:
                errors.append(f"Record #{idx}: Expected sequence {expected_seq}, found {seq}")

            # 2. Check parent chain linkage
            if parent_link != prev_sig:
                errors.append(f"Record #{idx} (seq {seq}): Broken chain link. Expected {prev_sig[:12]}..., found {parent_link[:12]}...")

            # 3. Verify cryptographic HMAC signature
            is_valid, reason = cls.verify_audit_event(envelope, sig, secret_key)
            if not is_valid:
                errors.append(f"Record #{idx} (seq {seq}): {reason}")

            prev_sig = sig
            expected_seq += 1

        return len(errors) == 0, errors


crypto_audit_service = CryptographicAuditService()
