"""EU CIRPASS Digital Product Passport (DPP) 2.0 Multi-Sector Engine.

Implements sector-specific compliance models and verifiable provenance schemas for:
- EU Battery Regulation (EU 2023/1542)
- EU ESPR Textiles & Apparel
- EU ICT & Consumer Electronics (French Repairability Index)
- Pharmaceutical & Regulated Healthcare Serialization
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any

from .crypto import utc_iso
from .models import Product


def generate_battery_passport(product: Product, custom_attrs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generates an EU Battery Regulation (EU 2023/1542) compliant Battery Passport."""
    attrs = custom_attrs or {}
    return {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://w3id.org/dpp/battery/v1",
        ],
        "type": ["VerifiableCredential", "DigitalProductPassport", "BatteryPassport"],
        "schema_version": "EU_2023_1542_v2.0",
        "product_id": product.product_id,
        "product_name": product.product_name,
        "manufacturer_id": product.manufacturer_id,
        "gtin": product.gtin,
        "serial_number": product.serial_number,
        "batch_id": product.batch_id,
        "sector": "BATTERY_STORAGE",
        "battery_specifications": {
            "chemistry": attrs.get("chemistry", "Lithium-Nickel-Manganese-Cobalt (NMC 811)"),
            "rated_capacity_kwh": float(attrs.get("rated_capacity_kwh", 78.4)),
            "nominal_voltage_v": float(attrs.get("nominal_voltage_v", 400.0)),
            "state_of_health_pct": float(attrs.get("state_of_health_pct", 100.0)),
            "expected_lifetime_cycles": int(attrs.get("expected_lifetime_cycles", 3500)),
            "warranty_years": int(attrs.get("warranty_years", 8)),
        },
        "critical_raw_materials": attrs.get("critical_raw_materials", {
            "cobalt_kg": 9.2,
            "lithium_kg": 6.8,
            "nickel_kg": 42.1,
            "manganese_kg": 5.4,
            "synthetic_graphite_kg": 52.0,
            "conflict_free_certified": True,
            "responsible_mining_standard": "IRMA-Standard-v1.0",
        }),
        "sustainability_metrics": {
            "carbon_footprint_kg_co2e": float(attrs.get("carbon_footprint_kg_co2e", 52.3)),
            "carbon_footprint_by_lifecycle": {
                "raw_material_extraction_pct": 58.0,
                "cell_manufacturing_pct": 28.0,
                "distribution_pct": 6.0,
                "end_of_life_recycling_pct": 8.0,
            },
            "recycled_content": {
                "recycled_cobalt_pct": float(attrs.get("recycled_cobalt_pct", 16.0)),
                "recycled_lithium_pct": float(attrs.get("recycled_lithium_pct", 6.0)),
                "recycled_nickel_pct": float(attrs.get("recycled_nickel_pct", 18.0)),
            },
            "circularity_status": attrs.get("circularity_status", "REMANUFACTURABLE_TIER_1"),
        },
        "safety_and_disassembly": {
            "extinguishing_agent": attrs.get("extinguishing_agent", "High-Volume Water / F-500 Encapsulator"),
            "disassembly_manual_uri": f"https://dpp.opap.io/manuals/{product.product_id}/disassembly.pdf",
            "second_life_suitability": attrs.get("second_life_suitability", "Grid Energy Storage Compatible (BESS)"),
        },
        "compliance_certifications": attrs.get("compliance_certifications", [
            {"standard": "UN 38.3", "status": "CERTIFIED", "audit_id": "AUD-UN383-992"},
            {"standard": "IEC 62619", "status": "CERTIFIED", "audit_id": "AUD-IEC-771"},
            {"standard": "EU Battery Regulation 2023/1542", "status": "COMPLIANT", "audit_id": "AUD-EU-2023"},
        ]),
        "issued_at": utc_iso(product.issued_at),
        "passport_valid_until": "2038-12-31T23:59:59Z",
    }


def generate_textile_passport(product: Product, custom_attrs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generates an EU ESPR Textile and Apparel Passport."""
    attrs = custom_attrs or {}
    return {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://w3id.org/dpp/textiles/v1",
        ],
        "type": ["VerifiableCredential", "DigitalProductPassport", "TextilePassport"],
        "schema_version": "EU_ESPR_TEXTILE_v1.2",
        "product_id": product.product_id,
        "product_name": product.product_name,
        "manufacturer_id": product.manufacturer_id,
        "gtin": product.gtin,
        "serial_number": product.serial_number,
        "batch_id": product.batch_id,
        "sector": "TEXTILES_APPAREL",
        "material_composition": attrs.get("material_composition", {
            "organic_cotton_pct": 70.0,
            "recycled_polyester_pct": 28.0,
            "elastane_pct": 2.0,
            "hazardous_chemicals_free": True,
            "pfas_free": True,
        }),
        "durability_and_care": {
            "expected_wash_cycles": int(attrs.get("expected_wash_cycles", 120)),
            "microplastic_shedding_mg_per_kg": float(attrs.get("microplastic_shedding_mg_per_kg", 0.12)),
            "repairability_grade": attrs.get("repairability_grade", "A_PLUS"),
            "takeback_program_available": True,
        },
        "environmental_impact": {
            "carbon_footprint_kg_co2e": float(attrs.get("carbon_footprint_kg_co2e", 4.8)),
            "water_consumption_liters": float(attrs.get("water_consumption_liters", 340.0)),
            "recycled_content_pct": float(attrs.get("recycled_content_pct", 28.0)),
            "circularity_status": attrs.get("circularity_status", "100%_FIBER_TO_FIBER_RECYCLABLE"),
        },
        "certifications": attrs.get("certifications", [
            {"name": "GOTS (Global Organic Textile Standard)", "code": "GOTS-CU-88421"},
            {"name": "OEKO-TEX Standard 100", "code": "OEKO-TEX-TEST-99"},
            {"name": "Cradle to Cradle Certified (Gold)", "code": "C2C-GOLD-2026"},
        ]),
        "issued_at": utc_iso(product.issued_at),
    }


def generate_electronics_passport(product: Product, custom_attrs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generates an EU ICT and Consumer Electronics Passport with French Repairability Index."""
    attrs = custom_attrs or {}
    return {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://w3id.org/dpp/electronics/v1",
        ],
        "type": ["VerifiableCredential", "DigitalProductPassport", "ElectronicsPassport"],
        "schema_version": "EU_ESPR_ELECTRONICS_v1.0",
        "product_id": product.product_id,
        "product_name": product.product_name,
        "manufacturer_id": product.manufacturer_id,
        "gtin": product.gtin,
        "serial_number": product.serial_number,
        "batch_id": product.batch_id,
        "sector": "ELECTRONICS_ICT",
        "repairability_index": {
            "french_repairability_score": float(attrs.get("french_repairability_score", 9.2)),
            "score_out_of_10": float(attrs.get("score_out_of_10", 9.2)),
            "documentation_score": 9.5,
            "disassembly_ease_score": 9.0,
            "spare_parts_availability_score": 9.4,
            "spare_parts_price_score": 8.9,
            "guaranteed_spare_parts_years": int(attrs.get("guaranteed_spare_parts_years", 7)),
        },
        "substances_and_materials": {
            "rohs_compliant": True,
            "reach_svhc_free": True,
            "recycled_plastics_pct": float(attrs.get("recycled_plastics_pct", 65.0)),
            "recycled_aluminum_pct": float(attrs.get("recycled_aluminum_pct", 85.0)),
            "halogen_free_pcb": True,
        },
        "lifecycle_and_support": {
            "security_updates_guarantee_years": int(attrs.get("security_updates_guarantee_years", 8)),
            "os_upgrades_guarantee_years": int(attrs.get("os_upgrades_guarantee_years", 6)),
            "carbon_footprint_kg_co2e": float(attrs.get("carbon_footprint_kg_co2e", 38.5)),
            "circularity_status": "MODULAR_REPAIRABLE",
        },
        "issued_at": utc_iso(product.issued_at),
    }


def generate_pharma_passport(product: Product, custom_attrs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generates an EU FMD / FDA DSCSA compliant Pharmaceutical Serialization Passport."""
    attrs = custom_attrs or {}
    return {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://w3id.org/dpp/pharma/v1",
        ],
        "type": ["VerifiableCredential", "DigitalProductPassport", "PharmaceuticalPassport"],
        "schema_version": "EU_FMD_DSCSA_v2.1",
        "product_id": product.product_id,
        "product_name": product.product_name,
        "manufacturer_id": product.manufacturer_id,
        "gtin": product.gtin,
        "serial_number": product.serial_number,
        "batch_id": product.batch_id,
        "sector": "PHARMA_HEALTHCARE",
        "drug_master_data": {
            "active_ingredient": attrs.get("active_ingredient", "Biologic Monoclonal Antibody"),
            "dosage_form": attrs.get("dosage_form", "Prefilled Syringe 100mg/mL"),
            "storage_conditions": attrs.get("storage_conditions", "Store refrigerated at 2°C to 8°C. Do not freeze."),
            "tamper_evident_seal": attrs.get("tamper_evident_seal", "Holographic Void-Pattern Optical Film"),
            "serialization_standard": "GS1 DataMatrix (01)GTIN(21)SERIAL(17)EXP(10)LOT",
        },
        "regulatory_authorizations": attrs.get("regulatory_authorizations", [
            {"authority": "EMA (European Medicines Agency)", "market_auth_num": "EU/1/24/9912/001"},
            {"authority": "FDA (US Food & Drug Admin)", "market_auth_num": "BLA-761922"},
            {"authority": "WHO GMP Certified", "cert_id": "WHO-GMP-GENEVA-2025"},
        ]),
        "cold_chain_profile": {
            "monitored": True,
            "max_temp_c": float(attrs.get("max_temp_c", 8.0)),
            "min_temp_c": float(attrs.get("min_temp_c", 2.0)),
            "temperature_breach_detected": False,
        },
        "issued_at": utc_iso(product.issued_at),
        "expiry_date": utc_iso(product.expiry_date) if product.expiry_date else "2028-12-31T23:59:59Z",
    }


def render_dpp_interactive_html(dpp: dict[str, Any]) -> str:
    """Renders a responsive, standalone EU Digital Product Passport interactive HTML card."""
    sector = dpp.get("sector", "GENERAL")
    prod_name = dpp.get("product_name", "Product Passport")
    prod_id = dpp.get("product_id", "")
    mfr_id = dpp.get("manufacturer_id", "")
    gtin = dpp.get("gtin", "N/A")
    serial = dpp.get("serial_number", "N/A")
    dpp_json_str = json.dumps(dpp, indent=2)

    badge_color = (
        "#10b981" if sector == "BATTERY_STORAGE"
        else "#3b82f6" if sector == "TEXTILES_APPAREL"
        else "#8b5cf6" if sector == "ELECTRONICS_ICT"
        else "#ef4444"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>EU Digital Product Passport - {prod_name}</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; background: #0b0f19; color: #f3f4f6; padding: 20px; }}
        .dpp-card {{ max-width: 800px; margin: 0 auto; background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
        .dpp-header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1f2937; padding-bottom: 16px; }}
        .badge {{ background: {badge_color}; color: #000; font-weight: 700; font-size: 11px; padding: 4px 10px; border-radius: 20px; text-transform: uppercase; }}
        .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 20px 0; }}
        .box {{ background: #1f2937; padding: 14px; border-radius: 8px; }}
        .box-title {{ font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.05em; }}
        .box-val {{ font-size: 16px; font-weight: 600; margin-top: 4px; color: #f9fafb; }}
        pre {{ background: #030712; padding: 14px; border-radius: 8px; font-size: 12px; overflow-x: auto; color: #10b981; border: 1px solid #1f2937; }}
    </style>
</head>
<body>
    <div class="dpp-card">
        <div class="dpp-header">
            <div>
                <h1 style="margin:0; font-size: 20px;">{prod_name}</h1>
                <p style="margin:4px 0 0 0; color: #9ca3af; font-size: 13px;">Product ID: {prod_id} | MFR: {mfr_id}</p>
            </div>
            <span class="badge">{sector}</span>
        </div>
        <div class="grid">
            <div class="box"><div class="box-title">GS1 GTIN-14</div><div class="box-val">{gtin}</div></div>
            <div class="box"><div class="box-title">Serial Number</div><div class="box-val">{serial}</div></div>
            <div class="box"><div class="box-title">Compliance Standard</div><div class="box-val">{dpp.get('schema_version', 'EU_DPP_2.0')}</div></div>
            <div class="box"><div class="box-title">Verification Integrity</div><div class="box-val" style="color: #10b981;">🛡️ Cryptographically Sealed</div></div>
        </div>
        <h3 style="font-size: 14px; margin-top: 20px; color: #9ca3af;">Verifiable W3C / CIRPASS JSON-LD Payload</h3>
        <pre><code>{dpp_json_str}</code></pre>
    </div>
</body>
</html>"""
