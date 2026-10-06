"""Test suite for EU CIRPASS Digital Product Passport (DPP) 2.0 Multi-Sector Engine.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models import Manufacturer, Product, Status
from app.dpp import (
    generate_battery_passport,
    generate_textile_passport,
    generate_electronics_passport,
    generate_pharma_passport,
    render_dpp_interactive_html,
)

client = TestClient(app)


def test_battery_passport_structure():
    """Verify EU Battery Regulation (EU 2023/1542) passport generation."""
    prod = Product(
        product_id="PROD-BAT-001",
        manufacturer_id="MFR-TESLA-01",
        product_code="BATT-PACK-100",
        product_name="Lithium-Ion Traction Battery Pack",
        batch_id="LOT-CELL-42",
        serial_number="SER-BATT-9901",
        gtin="00012345678905",
        issued_at=datetime.now(timezone.utc),
        canonical_payload={},
        key_id="KEY-1",
        signature=b"0" * 64,
    )

    dpp = generate_battery_passport(prod)
    assert dpp["schema_version"] == "EU_2023_1542_v2.0"
    assert dpp["sector"] == "BATTERY_STORAGE"
    assert "battery_specifications" in dpp
    assert dpp["battery_specifications"]["chemistry"] == "Lithium-Nickel-Manganese-Cobalt (NMC 811)"
    assert dpp["critical_raw_materials"]["conflict_free_certified"] is True
    assert dpp["sustainability_metrics"]["recycled_content"]["recycled_cobalt_pct"] > 0


def test_textile_passport_structure():
    """Verify EU ESPR Textile passport generation."""
    prod = Product(
        product_id="PROD-TEX-001",
        manufacturer_id="MFR-PATAGONIA",
        product_code="JACKET-ALP-01",
        product_name="Recycled Technical Alpine Shell",
        batch_id="LOT-TEX-88",
        serial_number="SER-TEX-1234",
        issued_at=datetime.now(timezone.utc),
        canonical_payload={},
        key_id="KEY-1",
        signature=b"0" * 64,
    )

    dpp = generate_textile_passport(prod)
    assert dpp["sector"] == "TEXTILES_APPAREL"
    assert "material_composition" in dpp
    assert dpp["material_composition"]["pfas_free"] is True
    assert dpp["durability_and_care"]["expected_wash_cycles"] >= 100


def test_electronics_passport_structure():
    """Verify EU ESPR ICT & Consumer Electronics passport with repairability metrics."""
    prod = Product(
        product_id="PROD-ELEC-001",
        manufacturer_id="MFR-FAIRPHONE",
        product_code="PHONE-MOD-5",
        product_name="Modular 5G Smartphone",
        batch_id="LOT-ELEC-7",
        serial_number="SER-ELEC-55",
        issued_at=datetime.now(timezone.utc),
        canonical_payload={},
        key_id="KEY-1",
        signature=b"0" * 64,
    )

    dpp = generate_electronics_passport(prod)
    assert dpp["sector"] == "ELECTRONICS_ICT"
    assert "repairability_index" in dpp
    assert dpp["repairability_index"]["french_repairability_score"] >= 9.0
    assert dpp["substances_and_materials"]["rohs_compliant"] is True


def test_pharma_passport_structure():
    """Verify Pharmaceutical Serialization & cold-chain passport."""
    prod = Product(
        product_id="PROD-PHARMA-001",
        manufacturer_id="MFR-NOVARTIS",
        product_code="MED-BIOLOGIC-01",
        product_name="Recombinant Oncology Monoclonal Antibody",
        batch_id="LOT-PHARMA-99",
        serial_number="SER-PHARMA-101",
        issued_at=datetime.now(timezone.utc),
        canonical_payload={},
        key_id="KEY-1",
        signature=b"0" * 64,
    )

    dpp = generate_pharma_passport(prod)
    assert dpp["sector"] == "PHARMA_HEALTHCARE"
    assert dpp["cold_chain_profile"]["monitored"] is True
    assert dpp["cold_chain_profile"]["min_temp_c"] == 2.0


def test_dpp_endpoint_and_html_render():
    """Verify /v1/products/{id}/dpp/sector/{sector} endpoint."""
    db_factory = app.dependency_overrides.get(get_db, get_db)
    with next(db_factory()) as db:
        mfr = db.get(Manufacturer, "MFR-DPP-TEST")
        if not mfr:
            mfr = Manufacturer(id="MFR-DPP-TEST", name="DPP Sector Corp", status=Status.ACTIVE)
            db.add(mfr)
        prod = db.get(Product, "PROD-DPP-SECTOR-01")
        if not prod:
            prod = Product(
                product_id="PROD-DPP-SECTOR-01",
                manufacturer_id="MFR-DPP-TEST",
                product_code="EV-BAT-01",
                product_name="Solid State EV Battery",
                batch_id="LOT-SSB-1",
                serial_number="SER-SSB-999",
                gtin="00012345678905",
                issued_at=datetime.now(timezone.utc),
                canonical_payload={"product_id": "PROD-DPP-SECTOR-01"},
                key_id="KEY-1",
                signature=b"0" * 64,
                status=Status.ACTIVE,
            )
            db.add(prod)
        db.commit()

    # JSON response
    res_json = client.get("/v1/products/PROD-DPP-SECTOR-01/dpp/sector/battery")
    assert res_json.status_code == 200
    assert res_json.json()["sector"] == "BATTERY_STORAGE"

    # HTML response
    res_html = client.get("/v1/products/PROD-DPP-SECTOR-01/dpp/sector/battery?format=html")
    assert res_html.status_code == 200
    assert "text/html" in res_html.headers["content-type"]
    assert "Solid State EV Battery" in res_html.text
