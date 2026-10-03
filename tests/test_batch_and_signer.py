import base64
import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat

from app.database import Base, get_db
from app.main import app
import app.main as main_module
from app.signer import (
    LocalEnvSigner,
    FileKeySigner,
    AwsKmsSigner,
    GcpKmsSigner,
    Pkcs11HsmSigner,
    get_signer,
)


engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base.metadata.create_all(engine)
main_module.engine = engine

private = Ed25519PrivateKey.generate()
private_raw = private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
public_raw = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
client = TestClient(app)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db


def setup_function():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def test_signer_providers():
    # 1. LocalEnvSigner
    env_signer = LocalEnvSigner(private_key_hex=private_raw.hex())
    assert env_signer.provider_name() == "env"
    assert env_signer.get_public_key() == public_raw
    sig = env_signer.sign({"item": 1})
    assert len(sig) == 64

    # 2. FileKeySigner
    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        tmp.write(private_raw.hex())
        tmp.flush()
        file_signer = FileKeySigner(key_path=tmp.name)
        assert file_signer.provider_name() == "file"
        assert file_signer.get_public_key() == public_raw
        sig_file = file_signer.sign({"item": 1})
        assert sig_file == sig
    os.unlink(tmp.name)

    # 3. AwsKmsSigner (mock)
    aws_signer = AwsKmsSigner(key_id="test-key", mock=True)
    assert "aws_kms" in aws_signer.provider_name()
    assert len(aws_signer.get_public_key()) == 32
    assert len(aws_signer.sign({"test": True})) == 64

    # 4. GcpKmsSigner (mock)
    gcp_signer = GcpKmsSigner(key_name="projects/test/keys/1", mock=True)
    assert "gcp_kms" in gcp_signer.provider_name()
    assert len(gcp_signer.get_public_key()) == 32

    # 5. Pkcs11HsmSigner (mock)
    hsm_signer = Pkcs11HsmSigner(key_label="test-label", mock=True)
    assert "pkcs11_hsm" in hsm_signer.provider_name()
    assert len(hsm_signer.get_public_key()) == 32


def test_batch_verification_flow(monkeypatch):
    monkeypatch.setenv("OPAP_API_KEY", "dev-test-key")
    monkeypatch.setenv("OPAP_SIGNING_PRIVATE_KEY_HEX", private_raw.hex())
    monkeypatch.setenv("OPAP_SIGNER_PROVIDER", "env")
    from app.config import get_settings
    get_settings.cache_clear()

    headers = {"X-API-Key": "dev-test-key"}

    # 1. Register Manufacturer
    mfr_res = client.post("/v1/manufacturers", headers=headers, json={
        "manufacturer_id": "NG-MFR-BATCH",
        "name": "Batch Mills Plc",
        "key_id": "KEY-B1",
        "public_key_b64": base64.b64encode(public_raw).decode("ascii"),
    })
    assert mfr_res.status_code == 201

    # 2. Issue 5 products
    issue_res = client.post("/v1/manufacturers/NG-MFR-BATCH/products", headers=headers, json={
        "product_code": "FLOUR-10KG",
        "product_name": "Premium Flour 10KG",
        "batch_id": "BATCH-001",
        "quantity": 5,
    })
    assert issue_res.status_code == 201
    issued_products = issue_res.json()["products"]
    pids = [p["product_id"] for p in issued_products]

    # 3. Revoke one product
    rev_res = client.post(f"/v1/products/{pids[4]}/revoke", headers=headers, json={"reason": "Damaged bag"})
    assert rev_res.status_code == 200

    # 4. Pre-verify one product in consumer lane to simulate a replay
    verify_one_res = client.post("/v1/verify", json={"product_id": pids[0], "lane": "CONSUMER"})
    assert verify_one_res.json()["result"] == "AUTHENTIC"

    # 5. Batch verify all items + an invalid ID
    batch_req = {
        "items": [
            {"product_id": pids[0]},  # Already verified (replay)
            {"product_id": pids[1]},  # Authentic
            {"product_id": pids[2]},  # Authentic
            {"product_id": pids[3]},  # Authentic
            {"product_id": pids[4]},  # Revoked product
            {"product_id": "OPAP-NG-FAKEXYZ-1234567890"},  # Invalid product
        ],
        "default_lane": "CONSUMER",
    }

    batch_res = client.post("/v1/verify/batch", json=batch_req)
    assert batch_res.status_code == 200
    data = batch_res.json()

    summary = data["summary"]
    assert summary["total"] == 6
    assert summary["authentic"] == 3
    assert summary["already_verified"] == 1
    assert summary["revoked"] == 1
    assert summary["invalid"] == 1
    assert summary["status"] == "COUNTERFEIT_DETECTED"  # because invalid > 0

    results = data["results"]
    assert len(results) == 6
    assert results[0]["result"] == "ALREADY_VERIFIED"
    assert results[1]["result"] == "AUTHENTIC"
    assert results[4]["result"] == "REVOKED_PRODUCT"
    assert results[5]["result"] == "INVALID_PRODUCT"


def test_web_scanner_ui_endpoints():
    # 1. Main index / scanner HTML
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "text/html" in res_index.headers["content-type"]
    assert "OPAP Protocol v0.1" in res_index.text

    res_scanner = client.get("/scanner")
    assert res_scanner.status_code == 200
    assert "BarcodeDetector" in res_scanner.text

    # 2. QR Landing endpoint content negotiation
    # JSON client
    res_json = client.get("/v1/verify/SAMPLE-PID", headers={"Accept": "application/json"})
    assert res_json.status_code == 200
    assert res_json.json()["product_id"] == "SAMPLE-PID"

    # HTML browser client
    res_html = client.get("/v1/verify/SAMPLE-PID", headers={"Accept": "text/html,application/xhtml+xml"})
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    assert "OPAP Protocol v0.1" in res_html.text


def test_signer_inspection_endpoint(monkeypatch):
    monkeypatch.setenv("OPAP_SIGNING_PRIVATE_KEY_HEX", private_raw.hex())
    monkeypatch.setenv("OPAP_SIGNER_PROVIDER", "env")
    from app.config import get_settings
    get_settings.cache_clear()

    res = client.get("/v1/signer")
    assert res.status_code == 200
    data = res.json()
    assert data["provider"] == "env"
    assert data["public_key_b64"] == base64.b64encode(public_raw).decode("ascii")
