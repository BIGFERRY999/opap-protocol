"""Comprehensive Enterprise Test Suite for OPAP.

Tests:
1. GS1 Digital Link (Sunrise 2027) Syntax, Modulo 10, and URI Resolver
2. EU ESPR Digital Product Passport (DPP) Circularity & Cryptographic Seal
3. GS1 EPCIS 2.0 Multi-Hop Custody Tracking & JSON-LD Export
4. AI Counterfeit Forensics & Haversine Impossible Travel Anomaly Detection
5. Industrial Packaging Label & Batch Sheet Exporters
"""

import base64
from datetime import datetime, timezone
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
from app.gs1 import (
    calculate_gtin_check_digit,
    validate_gtin,
    pad_gtin14,
    build_digital_link_uri,
    parse_digital_link_uri,
)
from app.ai import haversine_distance_km, ForensicEngine


# In-memory test database
engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base.metadata.create_all(engine)
main_module.engine = engine

# Keypair fixture
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


@pytest.fixture(autouse=True)
def setup_db(monkeypatch):
    monkeypatch.setenv("OPAP_API_KEY", "test-api-key-123")
    monkeypatch.setenv("OPAP_SIGNING_PRIVATE_KEY_HEX", private_raw.hex())
    from app.config import get_settings
    get_settings.cache_clear()

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def test_gtin_modulo10_and_uri_parser():
    # Standard GTIN check digits
    # 0001234567890 -> payload check digit: 5
    chk = calculate_gtin_check_digit("0001234567890")
    assert chk == 5
    assert validate_gtin("00012345678905") is True
    assert validate_gtin("00012345678909") is False

    # Pad GTIN to 14 digits
    assert pad_gtin14("1234567890128") == "01234567890128"

    # Build GS1 Digital Link URI
    uri = build_digital_link_uri(
        base_url="https://id.opap.example",
        gtin="00012345678905",
        serial_number="SER-9942",
        batch_id="LOT-ABC",
        expiry_yymmdd="281231",
    )
    assert "https://id.opap.example/01/00012345678905/21/SER-9942?10=LOT-ABC&17=281231" == uri

    # Parse GS1 Digital Link URI
    parsed = parse_digital_link_uri(uri)
    assert parsed["gtin"] == "00012345678905"
    assert parsed["serial_number"] == "SER-9942"
    assert parsed["batch_id"] == "LOT-ABC"
    assert parsed["expiry_date"] == "281231"


def test_gs1_digital_link_resolver():
    headers = {"X-API-Key": "test-api-key-123"}
    # Register manufacturer
    r_mfr = client.post(
        "/v1/manufacturers",
        headers=headers,
        json={
            "manufacturer_id": "MFR-GS1",
            "name": "Global Pharma Ltd",
            "key_id": "KEY-1",
            "public_key_b64": base64.b64encode(public_raw).decode(),
        },
    )
    assert r_mfr.status_code == 201

    # Issue product with GTIN
    r_prod = client.post(
        "/v1/manufacturers/MFR-GS1/products",
        headers=headers,
        json={
            "product_code": "VAX-COVID-01",
            "product_name": "mRNA Vaccine 30mcg",
            "batch_id": "BATCH-901",
            "gtin": "00012345678905",
            "quantity": 1,
        },
    )
    assert r_prod.status_code == 201
    prod = r_prod.json()["products"][0]
    serial = prod["serial_number"]
    gtin = prod["gtin"]

    # 1. Resolve JSON-LD linkset
    r_resolve = client.get(
        f"/01/{gtin}/21/{serial}",
        headers={"Accept": "application/ld+json"},
    )
    assert r_resolve.status_code == 200
    data = r_resolve.json()
    assert data["gtin"] == gtin
    assert data["serial_number"] == serial
    assert len(data["linkset"]) >= 3
    assert any(link["rel"] == "gs1:dpp" for link in data["linkset"])

    # 2. Resolve SVG vector packaging label
    r_svg = client.get(
        f"/01/{gtin}/21/{serial}",
        headers={"Accept": "image/svg+xml"},
    )
    assert r_svg.status_code == 200
    assert r_svg.headers["content-type"] == "image/svg+xml"
    assert "<svg" in r_svg.text
    assert "VAX-COVID-01" in r_svg.text

    # 3. Resolve HTML redirect for consumer smartphones
    r_html = client.get(
        f"/01/{gtin}/21/{serial}",
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )
    assert r_html.status_code == 307
    assert "/ui?product_id=" in r_html.headers["location"]


def test_eu_espr_digital_product_passport():
    headers = {"X-API-Key": "test-api-key-123"}
    client.post(
        "/v1/manufacturers",
        headers=headers,
        json={
            "manufacturer_id": "MFR-DPP",
            "name": "EcoElectronics SE",
            "key_id": "KEY-1",
            "public_key_b64": base64.b64encode(public_raw).decode(),
        },
    )

    r_prod = client.post(
        "/v1/manufacturers/MFR-DPP/products",
        headers=headers,
        json={
            "product_code": "SMART-WATCH-E",
            "product_name": "Circularity Smart Watch Series 5",
            "batch_id": "BATCH-CIRCULAR-01",
            "quantity": 1,
            "carbon_footprint_kg": 2.15,
            "recycled_content_pct": 68.5,
            "repairability_score": 9.2,
            "circularity_status": "HIGHLY_RECYCLABLE",
            "compliance_certs": ["EU_ESPR_2024", "CE_MARK", "WEEE_RECYCLED"],
        },
    )
    pid = r_prod.json()["products"][0]["product_id"]

    # Query DPP endpoint
    r_dpp = client.get(f"/v1/products/{pid}/dpp")
    assert r_dpp.status_code == 200
    dpp = r_dpp.json()

    assert dpp["product_id"] == pid
    assert dpp["carbon_footprint_kg"] == 2.15
    assert dpp["recycled_content_pct"] == 68.5
    assert dpp["repairability_score"] == 9.2
    assert dpp["circularity_status"] == "HIGHLY_RECYCLABLE"
    assert "EU_ESPR_2024" in dpp["compliance_certs"]
    assert dpp["ed25519_verified"] is True
    assert len(dpp["digest_sha256"]) == 64
    assert dpp["custody_events_count"] >= 1  # Commissioning event


def test_gs1_epcis2_custody_engine():
    headers = {"X-API-Key": "test-api-key-123"}
    client.post(
        "/v1/manufacturers",
        headers=headers,
        json={
            "manufacturer_id": "MFR-EPCIS",
            "name": "Global Cargo Pharma",
            "key_id": "KEY-1",
            "public_key_b64": base64.b64encode(public_raw).decode(),
        },
    )

    r_prod = client.post(
        "/v1/manufacturers/MFR-EPCIS/products",
        headers=headers,
        json={
            "product_code": "INSULIN-PEN-100",
            "product_name": "Recombinant Human Insulin Pen",
            "batch_id": "LOT-INS-77",
            "quantity": 1,
        },
    )
    pid = r_prod.json()["products"][0]["product_id"]

    # 1. Append Shipping event
    r_ship = client.post(
        f"/v1/products/{pid}/custody",
        headers=headers,
        json={
            "business_step": "SHIPPING",
            "disposition": "IN_TRANSIT",
            "location_name": "Hamburg Port Terminal",
            "location_gln": "4012345999990",
            "custodian_id": "LOGISTICS-01",
            "custodian_name": "Maersk Cold Chain",
            "notes": "Loaded onto refrigerated container #22.",
        },
    )
    assert r_ship.status_code == 200
    assert r_ship.json()["business_step"] == "SHIPPING"

    # 2. Append Customs Clearance event
    r_customs = client.post(
        f"/v1/products/{pid}/custody",
        headers=headers,
        json={
            "business_step": "CUSTOMS_CLEARANCE",
            "disposition": "ACTIVE",
            "location_name": "Lagos Customs Hub",
            "custodian_id": "CUSTOMS-NG",
            "custodian_name": "Nigeria Customs Inspection Service",
            "notes": "Cleared customs inspection with seal intact.",
        },
    )
    assert r_customs.status_code == 200

    # 3. Query Custody History
    r_hist = client.get(f"/v1/products/{pid}/custody")
    assert r_hist.status_code == 200
    events = r_hist.json()["events"]
    assert len(events) == 3  # COMMISSIONING + SHIPPING + CUSTOMS_CLEARANCE
    assert events[1]["business_step"] == "SHIPPING"
    assert events[2]["business_step"] == "CUSTOMS_CLEARANCE"

    # 4. Export standard GS1 EPCIS 2.0 JSON-LD
    r_epcis = client.get(f"/v1/products/{pid}/custody?format=epcis")
    assert r_epcis.status_code == 200
    doc = r_epcis.json()
    assert doc["type"] == "EPCISDocument"
    assert doc["schemaVersion"] == "2.0"
    assert len(doc["epcisBody"]["eventList"]) == 3
    assert doc["epcisBody"]["eventList"][0]["bizStep"] == "urn:epcglobal:cbv:bizstep:commissioning"


def test_ai_forensics_impossible_travel():
    # Verify Haversine distance
    # Paris (48.8566, 2.3522) to London (51.5074, -0.1278) ~ 343 km
    dist = haversine_distance_km(48.8566, 2.3522, 51.5074, -0.1278)
    assert 340 < dist < 350

    # Test impossible velocity evaluation:
    # 2 events 343 km apart in 60 seconds -> 20,580 km/h (impossible commercial speed)
    t1 = datetime(2026, 10, 6, 12, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 10, 6, 12, 1, 0, tzinfo=timezone.utc)

    e1 = {"geo_lat": 48.8566, "geo_lon": 2.3522, "occurred_at": t1, "city": "Paris"}
    e2 = {"geo_lat": 51.5074, "geo_lon": -0.1278, "occurred_at": t2, "city": "London"}

    anomaly = ForensicEngine.evaluate_geo_velocity(e1, e2)
    assert anomaly is not None
    assert anomaly["anomaly_type"] == "IMPOSSIBLE_TRAVEL_VELOCITY"
    assert anomaly["velocity_kmh"] > 900.0

    # Nominal travel evaluation:
    # Paris to London in 3 hours -> ~114 km/h (nominal Eurostar)
    t3 = datetime(2026, 10, 6, 15, 0, 0, tzinfo=timezone.utc)
    e3 = {"geo_lat": 51.5074, "geo_lon": -0.1278, "occurred_at": t3, "city": "London"}
    nom_anomaly = ForensicEngine.evaluate_geo_velocity(e1, e3)
    assert nom_anomaly is None


def test_ai_forensic_threat_report_and_feed():
    headers = {"X-API-Key": "test-api-key-123"}
    client.post(
        "/v1/manufacturers",
        headers=headers,
        json={
            "manufacturer_id": "MFR-AI",
            "name": "BioDefense Lab",
            "key_id": "KEY-1",
            "public_key_b64": base64.b64encode(public_raw).decode(),
        },
    )

    r_prod = client.post(
        "/v1/manufacturers/MFR-AI/products",
        headers=headers,
        json={
            "product_code": "BIO-ANTIDOTE-9",
            "product_name": "Broad-Spectrum Antitoxin",
            "batch_id": "LOT-AI-01",
            "quantity": 1,
        },
    )
    pid = r_prod.json()["products"][0]["product_id"]

    # First consumer scan (Nominal)
    v1 = client.post(
        "/v1/verify",
        json={"product_id": pid, "lane": "CONSUMER", "geo_lat": 40.7128, "geo_lon": -74.0060, "city": "New York"},
    )
    assert v1.json()["result"] == "AUTHENTIC"

    # Second consumer scan (Replay attack in Tokyo minutes later -> impossible travel!)
    v2 = client.post(
        "/v1/verify",
        json={"product_id": pid, "lane": "CONSUMER", "geo_lat": 35.6762, "geo_lon": 139.6503, "city": "Tokyo"},
    )
    assert v2.json()["result"] == "ALREADY_VERIFIED"
    assert "threat_analysis" in v2.json()

    # Query AI Forensics report
    r_forensics = client.get(f"/v1/products/{pid}/forensics")
    assert r_forensics.status_code == 200
    report = r_forensics.json()
    assert report["risk_level"] in ("CRITICAL", "ELEVATED")
    assert len(report["threat_indicators"]) >= 1
    assert "CRITICAL" in report["ai_advisory"] or "CAUTION" in report["ai_advisory"]

    # Query global threat feed
    r_feed = client.get("/v1/forensics/threats")
    assert r_feed.status_code == 200
    feed = r_feed.json()
    assert feed["count"] >= 1
    assert feed["threats"][0]["product_id"] == pid


def test_packaging_labels_and_sheet():
    headers = {"X-API-Key": "test-api-key-123"}
    client.post(
        "/v1/manufacturers",
        headers=headers,
        json={
            "manufacturer_id": "MFR-PACK",
            "name": "Astra Packaging Solutions",
            "key_id": "KEY-1",
            "public_key_b64": base64.b64encode(public_raw).decode(),
        },
    )

    r_prod = client.post(
        "/v1/manufacturers/MFR-PACK/products",
        headers=headers,
        json={
            "product_code": "PACK-MED-01",
            "product_name": "Sterile Surgical Bandage",
            "batch_id": "BATCH-PACK-01",
            "quantity": 3,
        },
    )
    products = r_prod.json()["products"]
    pid0 = products[0]["product_id"]

    # 1. Single packaging SVG label
    r_label = client.get(f"/v1/products/{pid0}/label.svg")
    assert r_label.status_code == 200
    assert r_label.headers["content-type"] == "image/svg+xml"
    assert "<svg" in r_label.text
    assert "SCAN TO AUTHENTICATE" in r_label.text
    assert "Sterile Surgical Bandage" in r_label.text

    # 2. Batch sticker print sheet HTML
    r_sheet = client.get("/v1/manufacturers/MFR-PACK/labels/sheet")
    assert r_sheet.status_code == 200
    assert "text/html" in r_sheet.headers["content-type"]
    assert "OPAP Production Packaging Labels" in r_sheet.text
    assert "window.print()" in r_sheet.text
