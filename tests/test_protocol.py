import base64
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption, PublicFormat
from app.database import Base, get_db
from app.main import app
import app.main as main_module


engine = create_engine("sqlite://", connect_args={"check_same_thread":False}, poolclass=StaticPool)
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


def test_canonical_sign_verify_and_independent_lanes(monkeypatch):
    monkeypatch.setenv("OPAP_API_KEY", "dev-change-me")
    monkeypatch.setenv("OPAP_SIGNING_PRIVATE_KEY_HEX", private_raw.hex())
    from app.config import get_settings
    get_settings.cache_clear()
    headers = {"X-API-Key":"dev-change-me"}
    r = client.post("/v1/manufacturers", headers=headers, json={"manufacturer_id":"NG-MFR-1","name":"Example Foods","key_id":"KEY-1","public_key_b64":base64.b64encode(public_raw).decode()})
    assert r.status_code == 201, r.text
    issued = client.post("/v1/manufacturers/NG-MFR-1/products", headers=headers, json={"product_code":"RICE-1","product_name":"Golden Rice","batch_id":"B-001","quantity":1})
    assert issued.status_code == 201, issued.text
    product_id = issued.json()["products"][0]["product_id"]
    assert issued.json()["products"][0]["qr_uri"].endswith(product_id)
    merchant = client.post("/v1/verify", json={"product_id":product_id,"lane":"MERCHANT","merchant_id":"shop-7"})
    assert merchant.json()["result"] == "AUTHENTIC"
    consumer = client.post("/v1/verify", json={"product_id":product_id,"lane":"CONSUMER"})
    assert consumer.json()["result"] == "AUTHENTIC"
    replay = client.post("/v1/verify", json={"product_id":product_id,"lane":"CONSUMER"})
    assert replay.json()["result"] == "ALREADY_VERIFIED"
    record = client.get(f"/v1/products/{product_id}").json()
    assert record["status"] == "ACTIVE"


def test_invalid_product_and_revocation(monkeypatch):
    monkeypatch.setenv("OPAP_SIGNING_PRIVATE_KEY_HEX", private_raw.hex())
    from app.config import get_settings
    get_settings.cache_clear()
    headers={"X-API-Key":"dev-change-me"}
    client.post("/v1/manufacturers", headers=headers, json={"manufacturer_id":"NG-MFR-2","name":"Maker","key_id":"KEY-2","public_key_b64":base64.b64encode(public_raw).decode()})
    out=client.post("/v1/manufacturers/NG-MFR-2/products", headers=headers, json={"product_code":"X","product_name":"Thing","batch_id":"B","quantity":1}).json()
    pid=out["products"][0]["product_id"]
    assert client.post("/v1/verify",json={"product_id":"missing","lane":"CONSUMER"}).json()["result"] == "INVALID_PRODUCT"
    assert client.post(f"/v1/products/{pid}/revoke",headers=headers,json={"reason":"recall"}).json()["status"] == "REVOKED"
    assert client.post("/v1/verify",json={"product_id":pid,"lane":"CONSUMER"}).json()["result"] == "REVOKED_PRODUCT"


def test_canonicalization_stable_and_tamper_evident():
    from app.crypto import canonical_bytes, sign_payload, verify_signature
    a={"b":2,"a":"café"}
    b={"a":"café","b":2}
    assert canonical_bytes(a) == canonical_bytes(b)
    sig=sign_payload(private_raw,a)
    assert verify_signature(public_raw,b,sig)
    assert not verify_signature(public_raw,{"a":"tampered","b":2},sig)


def test_invalid_request_has_protocol_result_code():
    response = client.post("/v1/verify", json={"product_id":"x","lane":"SHOPPER"})
    assert response.status_code == 422
    assert response.json()["result"] == "INVALID_REQUEST"
