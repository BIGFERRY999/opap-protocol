import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption


def canonical_bytes(payload: dict[str, Any]) -> bytes:
    """OPAP v0.1 canonical JSON: UTF-8, sorted keys, compact separators, no NaN."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def payload_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def generate_keypair() -> tuple[bytes, bytes]:
    private = Ed25519PrivateKey.generate()
    private_raw = private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    public_raw = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return private_raw, public_raw


def sign_payload(private_key: bytes, payload: dict[str, Any]) -> bytes:
    return Ed25519PrivateKey.from_private_bytes(private_key).sign(canonical_bytes(payload))


def verify_signature(public_key: bytes, payload: dict[str, Any], signature: bytes) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, canonical_bytes(payload))
        return True
    except Exception:
        return False


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64url_decode(data: str) -> bytes:
    """Decodes base64url string with flexible padding."""
    rem = len(data) % 4
    if rem > 0:
        data += "=" * (4 - rem)
    return base64.urlsafe_b64decode(data.encode("ascii"))


def utc_iso(value: datetime | None = None) -> str:
    value = value or datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def compute_merkle_root(leaf_hashes: list[str]) -> str:
    """Computes standard RFC 6962 SHA-256 Merkle root from hex leaf hashes."""
    if not leaf_hashes:
        return hashlib.sha256(b"").hexdigest()
    if len(leaf_hashes) == 1:
        return leaf_hashes[0]

    current_level = [bytes.fromhex(h) for h in leaf_hashes]
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            if i + 1 < len(current_level):
                right = current_level[i + 1]
            else:
                right = left  # duplicate odd leaf
            # RFC 6962 interior node prefix 0x01
            combined = hashlib.sha256(b"\x01" + left + right).digest()
            next_level.append(combined)
        current_level = next_level

    return current_level[0].hex()

