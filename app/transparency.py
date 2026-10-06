"""OPAP Key Transparency, JWKS (RFC 7517), and Merkle Audit Registry.

Provides verifiable, cryptographically auditable transparency logs for manufacturer
keys, certificate revocation lists (CRL), and open JWKS key distribution for
federated verifiers, customs APIs, and supply-chain partners.
"""

from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from .crypto import b64url, compute_merkle_root, utc_iso
from .models import Manufacturer, ManufacturerKey, Status, Product


def export_jwks_keys(db: Session, manufacturer_id: str | None = None) -> dict[str, Any]:
    """Exports active manufacturer public keys in RFC 7517 / RFC 8037 JWKS (JSON Web Key Set) format."""
    query = select(ManufacturerKey).join(Manufacturer).where(
        Manufacturer.status == Status.ACTIVE,
        ManufacturerKey.status == Status.ACTIVE,
    )
    if manufacturer_id:
        query = query.where(ManufacturerKey.manufacturer_id == manufacturer_id)

    keys = db.scalars(query).all()
    jwk_list = []

    for k in keys:
        # Ed25519 in JWK (RFC 8037)
        # kty: OKP, crv: Ed25519, x: base64url(public_key_32_bytes)
        x_coord = b64url(k.public_key)
        jwk_list.append({
            "kty": "OKP",
            "crv": "Ed25519",
            "kid": f"{k.manufacturer_id}:{k.key_id}",
            "use": "sig",
            "alg": "EdDSA",
            "x": x_coord,
            "mfr": k.manufacturer_id,
            "created_at": utc_iso(k.created_at),
        })

    return {
        "keys": jwk_list,
        "valid_at": utc_iso(),
        "total_active_keys": len(jwk_list),
    }


def export_key_revocation_list(db: Session) -> dict[str, Any]:
    """Exports Certificate Revocation List (CRL) of all revoked manufacturer keys."""
    revoked_keys = db.scalars(
        select(ManufacturerKey).where(ManufacturerKey.status == Status.REVOKED)
    ).all()

    revocation_entries = []
    for rk in revoked_keys:
        revocation_entries.append({
            "key_id": rk.key_id,
            "manufacturer_id": rk.manufacturer_id,
            "revoked_at": utc_iso(rk.revoked_at) if rk.revoked_at else utc_iso(),
            "public_key_fingerprint": hashlib.sha256(rk.public_key).hexdigest(),
        })

    # CRL root hash
    crl_hash = hashlib.sha256(
        ",".join(e["key_id"] for e in revocation_entries).encode("utf-8")
    ).hexdigest()

    return {
        "crl_version": "1.0",
        "issuer": "OPAP Key Transparency Authority",
        "generated_at": utc_iso(),
        "revoked_count": len(revocation_entries),
        "crl_fingerprint": crl_hash,
        "revoked_keys": revocation_entries,
    }


def compute_transparency_merkle_state(db: Session) -> dict[str, Any]:
    """Builds an RFC 6962 SHA-256 Merkle Transparency Tree over all registered keys and active products."""
    all_keys = db.scalars(select(ManufacturerKey).order_by(ManufacturerKey.id.asc())).all()
    all_products = db.scalars(select(Product).order_by(Product.product_id.asc())).all()

    leaf_hashes = []
    # 1. Add keys to leaves
    for k in all_keys:
        leaf_content = f"KEY:{k.manufacturer_id}:{k.key_id}:{k.status.value}:{k.public_key.hex()}".encode("utf-8")
        leaf_hash = hashlib.sha256(b"\x00" + leaf_content).hexdigest()  # RFC 6962 leaf prefix 0x00
        leaf_hashes.append(leaf_hash)

    # 2. Add products to leaves
    for p in all_products:
        prod_content = f"PROD:{p.product_id}:{p.manufacturer_id}:{p.status.value}:{p.signature.hex()}".encode("utf-8")
        leaf_hash = hashlib.sha256(b"\x00" + prod_content).hexdigest()
        leaf_hashes.append(leaf_hash)

    root_hash = compute_merkle_root(leaf_hashes) if leaf_hashes else hashlib.sha256(b"").hexdigest()

    return {
        "tree_size": len(leaf_hashes),
        "root_hash": root_hash,
        "key_leaves_count": len(all_keys),
        "product_leaves_count": len(all_products),
        "timestamp": utc_iso(),
        "algorithm": "RFC6962_SHA256",
    }
