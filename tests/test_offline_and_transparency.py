"""Test suite for OPAP Offline Verification (V-Pass), Key Transparency (JWKS / CRL / Merkle Tree), and Graph Forensics.
"""

import base64
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

from app.main import app
from app.database import get_db
from app.models import Manufacturer, ManufacturerKey, Product, Status
from app.crypto import generate_keypair, sign_payload, canonical_bytes
from app.offline import (
    create_offline_token,
    parse_offline_token,
    verify_offline_token_locally,
    create_offline_proof_receipt,
)
from app.transparency import export_jwks_keys, export_key_revocation_list, compute_transparency_merkle_state

client = TestClient(app)


def test_offline_token_generation_and_local_verification():
    """Verify 100% air-gapped cryptographic token generation and client-side verification."""
    priv_raw, pub_raw = generate_keypair()
    
    prod_payload = {
        "product_id": "PROD-OFFLINE-001",
        "manufacturer_id": "MFR-OFFLINE-TEST",
        "key_id": "KEY-OFFLINE-1",
        "gtin": "07612345678900",
        "batch_id": "LOT-OFFLINE-A",
        "serial_number": "SER-OFFLINE-99",
    }
    sig = sign_payload(priv_raw, prod_payload)

    # 1. Create compact V-Pass token
    token = create_offline_token(
        product_id="PROD-OFFLINE-001",
        manufacturer_id="MFR-OFFLINE-TEST",
        key_id="KEY-OFFLINE-1",
        signature_bytes=sig,
        gtin="07612345678900",
        batch_id="LOT-OFFLINE-A",
        serial_number="SER-OFFLINE-99",
    )
    assert token.startswith("OPAP.V1.")

    # 2. Parse token
    parsed = parse_offline_token(token)
    assert parsed["payload"]["pid"] == "PROD-OFFLINE-001"
    assert parsed["payload"]["mfr"] == "MFR-OFFLINE-TEST"
    assert parsed["signature"] == sig

    # 3. Verify purely offline with public key
    res = verify_offline_token_locally(token, pub_raw, canonical_payload=prod_payload)
    assert res["valid"] is True
    assert res["reason"] == "AUTHENTIC_OFFLINE"

    # 4. Verify tampering detection (wrong public key)
    _, wrong_pub = generate_keypair()
    tampered_res = verify_offline_token_locally(token, wrong_pub, canonical_payload=prod_payload)
    assert tampered_res["valid"] is False


def test_offline_token_expiry_enforcement():
    """Verify expired token rejection during offline inspection."""
    priv_raw, pub_raw = generate_keypair()
    past_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

    prod_payload = {
        "product_id": "PROD-EXP-001",
        "manufacturer_id": "MFR-EXP",
        "key_id": "KEY-1",
        "gtin": None,
        "batch_id": "LOT-EXP",
        "serial_number": "SER-EXP",
    }
    sig = sign_payload(priv_raw, prod_payload)

    expired_token = create_offline_token(
        product_id="PROD-EXP-001",
        manufacturer_id="MFR-EXP",
        key_id="KEY-1",
        signature_bytes=sig,
        expiry_date=past_date,
    )

    res = verify_offline_token_locally(expired_token, pub_raw, canonical_payload=prod_payload)
    assert res["valid"] is False
    assert res["reason"] == "EXPIRED"


def test_offline_receipt_and_api_recording():
    """Verify offline inspection receipt generation and submission to server."""
    priv_raw, pub_raw = generate_keypair()
    prod_payload = {
        "product_id": "PROD-RECEIPT-001",
        "manufacturer_id": "MFR-REC",
        "key_id": "KEY-1",
        "gtin": None,
        "batch_id": "LOT-1",
        "serial_number": "SER-1",
    }
    sig = sign_payload(priv_raw, prod_payload)
    token = create_offline_token("PROD-RECEIPT-001", "MFR-REC", "KEY-1", sig)

    receipt = create_offline_proof_receipt(
        token_str=token,
        inspector_id="AGENT-CUSTOMS-ZURICH",
        verification_result="AUTHENTIC",
        geo_lat=47.3769,
        geo_lon=8.5417,
        location_name="Zurich Airport Customs Hub",
        notes="All physical security seals verified intact.",
    )
    assert receipt["inspector_id"] == "AGENT-CUSTOMS-ZURICH"
    assert "receipt_hash" in receipt

    # Register manufacturer & product in DB for API receipt submission
    db_factory = app.dependency_overrides.get(get_db, get_db)
    with next(db_factory()) as db:
        mfr = db.get(Manufacturer, "MFR-REC")
        if not mfr:
            mfr = Manufacturer(id="MFR-REC", name="Receipt Logistics Ltd", status=Status.ACTIVE)
            db.add(mfr)
        prod = db.get(Product, "PROD-RECEIPT-001")
        if not prod:
            prod = Product(
                product_id="PROD-RECEIPT-001",
                manufacturer_id="MFR-REC",
                product_code="REC-01",
                product_name="Customs Cargo Unit",
                batch_id="LOT-1",
                serial_number="SER-1",
                issued_at=datetime.now(timezone.utc),
                canonical_payload=prod_payload,
                key_id="KEY-1",
                signature=sig,
                status=Status.ACTIVE,
            )
            db.add(prod)
        db.commit()

    res = client.post("/v1/verify/offline/receipt", json={
        "token": token,
        "inspector_id": "AGENT-CUSTOMS-ZURICH",
        "result": "AUTHENTIC",
        "geo_lat": 47.3769,
        "geo_lon": 8.5417,
        "location_name": "Zurich Airport Customs Hub",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == "PROD-RECEIPT-001"


def test_jwks_and_merkle_transparency():
    """Verify standard RFC 7517 JWKS key set and Merkle root calculation."""
    # 1. JWKS
    res_jwks = client.get("/.well-known/jwks.json")
    assert res_jwks.status_code == 200
    jwks_data = res_jwks.json()
    assert "keys" in jwks_data
    assert isinstance(jwks_data["keys"], list)

    # 2. Open Discovery config
    res_conf = client.get("/.well-known/opap-configuration")
    assert res_conf.status_code == 200
    assert res_conf.json()["protocol_version"] == "0.1.0-enterprise"

    # 3. Merkle root
    res_merkle = client.get("/v1/transparency/merkle-root")
    assert res_merkle.status_code == 200
    merkle_data = res_merkle.json()
    assert "root_hash" in merkle_data
    assert len(merkle_data["root_hash"]) == 64

    # 4. CRL
    res_crl = client.get("/v1/transparency/crl")
    assert res_crl.status_code == 200
    assert "revoked_keys" in res_crl.json()


def test_forensics_graph_endpoint():
    """Verify interactive topology graph dataset generation."""
    db_factory = app.dependency_overrides.get(get_db, get_db)
    with next(db_factory()) as db:
        mfr = db.get(Manufacturer, "MFR-GRAPH")
        if not mfr:
            mfr = Manufacturer(id="MFR-GRAPH", name="Graph Test Corp", status=Status.ACTIVE)
            db.add(mfr)
        prod = db.get(Product, "PROD-GRAPH-001")
        if not prod:
            prod = Product(
                product_id="PROD-GRAPH-001",
                manufacturer_id="MFR-GRAPH",
                product_code="GR-01",
                product_name="Graph Traceable Asset",
                batch_id="LOT-G1",
                serial_number="SER-G1",
                issued_at=datetime.now(timezone.utc),
                canonical_payload={"product_id": "PROD-GRAPH-001"},
                key_id="KEY-1",
                signature=b"0" * 64,
                status=Status.ACTIVE,
            )
            db.add(prod)
        db.commit()

    res = client.get("/v1/products/PROD-GRAPH-001/forensics/graph")
    assert res.status_code == 200
    graph = res.json()
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["nodes"]) >= 1
