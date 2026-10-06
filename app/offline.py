"""OPAP Offline Verification Protocol (V-Pass & Compact Attestation Capsules).

Enables 100% air-gapped, offline cryptographic verification of physical items
by customs officers, warehouse inspectors, and retail terminals using local
cached public keys or JWKS keyrings without active internet or database connections.
"""

from __future__ import annotations

import base64
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from .crypto import b64url, b64url_decode, canonical_bytes, verify_signature, utc_iso
from .models import VerificationEvent, VerificationLane, Lane, LaneStatus, Status, Product


class OfflineVerificationError(Exception):
    """Raised when an offline verification token fails parsing or verification."""
    pass


def create_offline_token(
    product_id: str,
    manufacturer_id: str,
    key_id: str,
    signature_bytes: bytes,
    gtin: str | None = None,
    batch_id: str | None = None,
    serial_number: str | None = None,
    expiry_date: str | None = None,
    issued_at: str | None = None,
) -> str:
    """Generates a compact, URL-safe self-contained Offline Verification Token (V-Pass).
    
    Format: OPAP.V1.<payload_b64url>.<signature_b64url>
    """
    payload = {
        "v": 1,
        "pid": product_id,
        "mfr": manufacturer_id,
        "kid": key_id,
        "gtin": gtin or "",
        "bat": batch_id or "",
        "ser": serial_number or "",
        "iss": issued_at or utc_iso(),
        "exp": expiry_date or "",
    }
    
    payload_raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    payload_b64 = b64url(payload_raw)
    sig_b64 = b64url(signature_bytes)
    return f"OPAP.V1.{payload_b64}.{sig_b64}"


def parse_offline_token(token_str: str) -> dict[str, Any]:
    """Parses and decodes an Offline Verification Token without verifying signature."""
    parts = token_str.strip().split(".")
    if len(parts) != 4 or parts[0] != "OPAP" or parts[1] != "V1":
        raise OfflineVerificationError("Invalid OPAP offline token structure. Expected 'OPAP.V1.<payload>.<sig>'")
    
    try:
        payload_bytes = b64url_decode(parts[2])
        payload = json.loads(payload_bytes.decode("utf-8"))
        signature = b64url_decode(parts[3])
    except Exception as e:
        raise OfflineVerificationError(f"Failed to decode offline token components: {e}")
    
    return {
        "header": {"alg": "Ed25519", "typ": "OPAP-V1"},
        "payload": payload,
        "signature": signature,
        "signature_b64": parts[3],
        "payload_b64": parts[2],
    }


def verify_offline_token_locally(
    token_str: str,
    public_key_bytes: bytes,
    canonical_payload: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Performs 100% offline cryptographic verification against a known public key."""
    parsed = parse_offline_token(token_str)
    payload = parsed["payload"]
    signature = parsed["signature"]
    current_time = now or datetime.now(timezone.utc)

    # 1. Expiry check
    exp_str = payload.get("exp")
    if exp_str:
        try:
            exp_dt = datetime.fromisoformat(exp_str.replace("Z", "+00:00"))
            if current_time > exp_dt:
                return {
                    "valid": False,
                    "reason": "EXPIRED",
                    "details": f"Product expired on {exp_str}",
                    "payload": payload,
                }
        except ValueError:
            pass

    # 2. Cryptographic signature check
    # If canonical_payload is provided (full original payload), verify against it;
    # otherwise, verify against the minimal self-attested token payload structure
    target_payload = canonical_payload if canonical_payload is not None else {
        "product_id": payload["pid"],
        "manufacturer_id": payload["mfr"],
        "key_id": payload["kid"],
        "gtin": payload.get("gtin") or None,
        "batch_id": payload.get("bat") or "",
        "serial_number": payload.get("ser") or "",
    }

    # Verify signature
    is_valid = verify_signature(public_key_bytes, target_payload, signature)
    if not is_valid:
        # Fallback check on raw payload bytes
        is_valid = verify_signature(public_key_bytes, payload, signature)

    return {
        "valid": is_valid,
        "reason": "AUTHENTIC_OFFLINE" if is_valid else "INVALID_SIGNATURE",
        "product_id": payload.get("pid"),
        "manufacturer_id": payload.get("mfr"),
        "key_id": payload.get("kid"),
        "gtin": payload.get("gtin"),
        "batch_id": payload.get("bat"),
        "serial_number": payload.get("ser"),
        "issued_at": payload.get("iss"),
        "expiry_date": payload.get("exp"),
        "verified_at": utc_iso(current_time),
    }


def create_offline_proof_receipt(
    token_str: str,
    inspector_id: str,
    verification_result: str,
    geo_lat: float | None = None,
    geo_lon: float | None = None,
    location_name: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Generates a tamper-evident offline inspection proof receipt for later cloud sync."""
    parsed = parse_offline_token(token_str)
    receipt_id = str(uuid.uuid4())
    timestamp = utc_iso()
    
    receipt_data = {
        "receipt_id": receipt_id,
        "inspector_id": inspector_id,
        "product_id": parsed["payload"]["pid"],
        "token_payload": parsed["payload"],
        "token_signature_b64": parsed["signature_b64"],
        "result": verification_result,
        "geo_lat": geo_lat,
        "geo_lon": geo_lon,
        "location_name": location_name or "Air-Gapped Field Inspection",
        "notes": notes or "Offline V-Pass inspection completed",
        "timestamp": timestamp,
    }
    
    # Generate receipt tamper-evident checksum
    receipt_hash = hashlib.sha256(canonical_bytes(receipt_data)).hexdigest()
    receipt_data["receipt_hash"] = receipt_hash
    return receipt_data
