"""
Unit & Integration Tests for OPAP Pluggable Signer Architecture & EPCIS 2.0 Ingest.
Validates:
1. LocalEnvSigner (Environment Variable Ed25519 key signing & verification)
2. FileKeySigner (Raw 32-byte, Hex, and PEM key files)
3. AwsKmsSigner (Simulated & Hardware Key Signatures)
4. GcpKmsSigner (Google Cloud KMS Asymmetric Ed25519 Signatures)
5. Pkcs11HsmSigner (PKCS#11 Hardware Security Module Simulator)
6. get_signer() Factory and dynamic provider selection
7. Bulk EPCIS 2.0 Document Capture Pipeline (/v1/epcis/capture)
"""

import os
import tempfile
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

from app.signer import (
    LocalEnvSigner,
    FileKeySigner,
    AwsKmsSigner,
    GcpKmsSigner,
    Pkcs11HsmSigner,
    get_signer,
    SignerConfigError,
)
from app.crypto import canonical_bytes, verify_signature
from app.epcis import ingest_epcis2_document


def test_local_env_signer_roundtrip():
    """Verify LocalEnvSigner can sign canonical payloads verifiable with its public key."""
    priv = Ed25519PrivateKey.generate()
    priv_hex = priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()).hex()

    signer = LocalEnvSigner(private_key_hex=priv_hex)
    assert signer.provider_name() == "env"
    pub_bytes = signer.get_public_key()
    assert len(pub_bytes) == 32

    payload = {"product_id": "TEST-PROD-01", "batch": "LOT-99", "serial": "001"}
    sig = signer.sign(payload)
    assert len(sig) == 64

    # Verify signature mathematically
    is_valid = verify_signature(pub_bytes, payload, sig)
    assert is_valid is True


def test_file_key_signer_formats():
    """Verify FileKeySigner handles raw 32-byte binary, hex, and PKCS#8 PEM files."""
    priv = Ed25519PrivateKey.generate()
    raw_bytes = priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    pem_bytes = priv.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    hex_str = raw_bytes.hex()

    # 1. Raw binary file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(raw_bytes)
        f.flush()
        raw_path = f.name
    try:
        s_raw = FileKeySigner(key_path=raw_path)
        assert s_raw.get_public_key() == priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    finally:
        os.unlink(raw_path)

    # 2. PEM file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(pem_bytes)
        f.flush()
        pem_path = f.name
    try:
        s_pem = FileKeySigner(key_path=pem_path)
        assert s_pem.get_public_key() == priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    finally:
        os.unlink(pem_path)

    # 3. Hex text file
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as f:
        f.write(hex_str)
        f.flush()
        hex_path = f.name
    try:
        s_hex = FileKeySigner(key_path=hex_path)
        assert s_hex.get_public_key() == priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    finally:
        os.unlink(hex_path)


def test_aws_kms_signer_simulated():
    """Verify AWS KMS simulated signer produces valid Ed25519 signatures."""
    signer = AwsKmsSigner(key_id="alias/opap-test-key", region="eu-central-1", mock=True)
    assert "aws_kms" in signer.provider_name()
    pub_bytes = signer.get_public_key()
    assert len(pub_bytes) == 32

    payload = {"mfr": "PHARMA", "gtin": "00012345678905", "serial": "SER-101"}
    sig = signer.sign(payload)
    assert len(sig) == 64
    assert verify_signature(pub_bytes, payload, sig) is True

    desc = signer.describe()
    assert desc["mock"] is True
    assert desc["key_id"] == "alias/opap-test-key"


def test_gcp_kms_signer_simulated():
    """Verify Google Cloud KMS simulated signer."""
    signer = GcpKmsSigner(key_name="projects/test/locations/global/keyRings/opap/cryptoKeys/ed25519", mock=True)
    assert "gcp_kms" in signer.provider_name()
    pub = signer.get_public_key()
    payload = {"test": 123}
    sig = signer.sign(payload)
    assert verify_signature(pub, payload, sig) is True


def test_pkcs11_hsm_signer_simulated():
    """Verify PKCS#11 HSM simulated signer."""
    signer = Pkcs11HsmSigner(slot_id=0, key_label="opap-master-hsm", mock=True)
    assert "pkcs11" in signer.provider_name()
    pub = signer.get_public_key()
    payload = {"item": "SECURE_TAG"}
    sig = signer.sign(payload)
    assert verify_signature(pub, payload, sig) is True


def test_signer_factory():
    """Verify get_signer factory handles all provider names."""
    s_aws = get_signer("aws_kms", mock=True)
    assert isinstance(s_aws, AwsKmsSigner)

    s_gcp = get_signer("gcp_kms", mock=True)
    assert isinstance(s_gcp, GcpKmsSigner)

    s_hsm = get_signer("pkcs11", mock=True)
    assert isinstance(s_hsm, Pkcs11HsmSigner)

    with pytest.raises(SignerConfigError):
        get_signer("unknown_provider_xyz")


# --- Bulk EPCIS 2.0 Ingest Endpoint Tests ---

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, get_db
from app.models import Manufacturer, Product, Status
from datetime import datetime, timezone

client = TestClient(app)

def test_bulk_epcis2_capture_endpoint():
    """Verify POST /v1/epcis/capture bulk event ingest."""
    # Set up manufacturer and product in test DB
    db_factory = app.dependency_overrides.get(get_db, get_db)
    with next(db_factory()) as db:
        mfr = db.get(Manufacturer, "MFR-EPCIS-TEST")
        if not mfr:
            mfr = Manufacturer(
                id="MFR-EPCIS-TEST",
                name="EPCIS Test Logistics Ltd",
                status=Status.ACTIVE,
            )
            db.add(mfr)

        prod = db.get(Product, "PROD-EPCIS-001")
        if not prod:
            prod = Product(
                product_id="PROD-EPCIS-001",
                manufacturer_id="MFR-EPCIS-TEST",
                product_code="MED-01",
                product_name="Medical Diagnostic Pack",
                batch_id="LOT-EPCIS-9",
                serial_number="SER-EPCIS-99",
                gtin="00012345678905",
                issued_at=datetime.now(timezone.utc),
                canonical_payload={"product_id": "PROD-EPCIS-001"},
                key_id="KEY-1",
                signature=b"0" * 64,
                status=Status.ACTIVE,
            )
            db.add(prod)
        db.commit()

    epcis_doc = {
        "@context": ["https://ref.gs1.org/standards/epcis/2.0.0/epcis-context.jsonld"],
        "type": "EPCISDocument",
        "schemaVersion": "2.0",
        "creationDate": datetime.now(timezone.utc).isoformat(),
        "epcisBody": {
            "eventList": [
                {
                    "type": "ObjectEvent",
                    "action": "OBSERVE",
                    "bizStep": "urn:epcglobal:cbv:bizstep:receiving",
                    "disposition": "urn:epcglobal:cbv:disp:active",
                    "readPoint": {"id": "urn:epc:id:sgln:7612345000012"},
                    "bizLocation": {"name": "Zurich Central Freight Depot"},
                    "custodian": {"id": "CUST-SWISS-01", "name": "Swiss Post Cargo"},
                    "epcList": ["urn:epc:id:sgtin:00012345678905.SER-EPCIS-99"],
                    "userExtensions": {
                        "opap:notes": "Batch acceptance at international gateway."
                    }
                }
            ]
        }
    }

    res = client.post(
        "/v1/epcis/capture",
        json=epcis_doc,
        headers={"X-API-Key": "dev-change-me"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "INGESTED_SUCCESSFULLY"
    assert data["total_events_processed"] == 1
    assert "PROD-EPCIS-001" in data["affected_product_ids"]
