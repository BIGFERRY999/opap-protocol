"""Realistic Enterprise Data Seeder for OPAP Protocol.

Seeds realistic multi-industry supply chains:
1. PharmaTech Life Sciences (Cold-chain vaccine with full EPCIS 2.0 multi-hop custody)
2. LuxeArtisans Horlogerie (Luxury timepiece with active AI impossible travel threat)
3. Nordic EcoMobility (EU Battery Passport with materials breakdown & circularity)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
import sys

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.client import OPAPClient


def seed_database(base_url: str = "http://127.0.0.1:8080", api_key: str = "dev-change-me"):
    client = OPAPClient(base_url=base_url, api_key=api_key)

    print("🚀 Initializing OPAP Enterprise Data Seeding...")
    signer = client.signer_status()
    pub_key = signer["public_key_b64"]

    # =========================================================================
    # 1. PHARMATECH LIFE SCIENCES (Vaccines & Cold-Chain Logistics)
    # =========================================================================
    print("\n[1/3] Seeding PharmaTech Global Life Sciences...")
    client.register_manufacturer(
        manufacturer_id="MFR-PHARMA-01",
        name="PharmaTech Global Life Sciences AG",
        key_id="KEY-PHARMA-1",
        public_key_b64=pub_key,
    )

    pharma_batch = client.issue_products(
        manufacturer_id="MFR-PHARMA-01",
        product_code="MRNA-VAX-50MCG",
        product_name="mRNA Polyvalent Vaccine 50mcg Injection",
        batch_id="LOT-2026-COLD9",
        quantity=3,
        gtin="00012345678905",
        carbon_footprint_kg=0.45,
        recycled_content_pct=20.0,
        repairability_score=1.0,
        circularity_status="CLINICAL_DISPOSAL",
        compliance_certs=["WHO_GMP", "FDA_DSCSA", "EMA_COLD_CHAIN"],
    )
    p_vax = pharma_batch["products"][0]
    pid_vax = p_vax["product_id"]
    print(f"  • Issued Vaccine Item: {pid_vax}")
    print(f"    GS1 Link: {p_vax['gs1_digital_link_uri']}")

    # Log Multi-Hop EPCIS Custody Events
    print("  • Recording EPCIS 2.0 supply chain custody progression...")
    client.log_custody_event(
        product_id=pid_vax,
        business_step="SHIPPING",
        disposition="IN_TRANSIT",
        location_name="Basel Cold Storage Freight Terminal",
        location_gln="7612345000012",
        custodian_id="LOG-MAERSK-01",
        custodian_name="Maersk Special Pharma Cold Logistics",
        notes="Dispatched in certified dry-ice thermal container #TC-994 (-80C nominal).",
    )
    client.log_custody_event(
        product_id=pid_vax,
        business_step="CUSTOMS_CLEARANCE",
        disposition="ACTIVE",
        location_name="London Heathrow Airport Border Inspection Post",
        location_gln="5012345888880",
        custodian_id="UK-BORDER-FORCE",
        custodian_name="UK Border Regulatory & Medicines Control",
        notes="Customs and temperature log compliance verified. Seals untouched.",
    )
    client.log_custody_event(
        product_id=pid_vax,
        business_step="RECEIVING",
        disposition="ACTIVE",
        location_name="NHS Central Hospital Logistics Depot London",
        location_gln="5012345999991",
        custodian_id="NHS-DEPOT-CHIEF",
        custodian_name="NHS Supply Chain Pharmacy Services",
        notes="Accepted into cryogenic storage rack B4.",
    )

    # Wholesale Merchant Acceptance Scan
    client.verify(
        product_id=pid_vax,
        lane="MERCHANT",
        merchant_id="NHS-LONDON-PHARMACY-01",
        city="London",
        geo_lat=51.5074,
        geo_lon=-0.1278,
    )
    print("  • Merchant acceptance lane consumed successfully.")

    # =========================================================================
    # 2. LUXEARTISANS HORLOGERIE (Luxury Timepiece with Replay/Impossible Travel)
    # =========================================================================
    print("\n[2/3] Seeding LuxeArtisans Haute Horlogerie...")
    client.register_manufacturer(
        manufacturer_id="MFR-LUXE-01",
        name="LuxeArtisans Horlogerie Geneve SA",
        key_id="KEY-LUXE-1",
        public_key_b64=pub_key,
    )

    luxe_batch = client.issue_products(
        manufacturer_id="MFR-LUXE-01",
        product_code="TOURBILLON-TI-8",
        product_name="Master Tourbillon Titanium Chronograph",
        batch_id="LIMITED-EDITION-50",
        quantity=2,
        gtin="07640123456783",
        carbon_footprint_kg=1.85,
        recycled_content_pct=85.0,
        repairability_score=9.8,
        circularity_status="LIFETIME_REPAIRABLE",
        compliance_certs=["SWISS_MADE_CHRONOMETER", "RESPONSIBLE_JEWELLERY_COUNCIL"],
    )
    p_watch = luxe_batch["products"][0]
    pid_watch = p_watch["product_id"]
    print(f"  • Issued Luxury Timepiece: {pid_watch}")

    # Initial scan in Geneva (Boutique sale)
    client.verify(
        product_id=pid_watch,
        lane="CONSUMER",
        city="Geneva",
        geo_lat=46.2044,
        geo_lon=6.1432,
    )
    print("  • Initial Consumer scan recorded in Geneva boutique (Nominal).")

    # Counterfeit Syndicate attack: Duplicate scan in Hong Kong minutes later!
    print("  • Simulating syndicated counterfeit attack (Hong Kong scan 5 mins later)...")
    threat_res = client.verify(
        product_id=pid_watch,
        lane="CONSUMER",
        city="Hong Kong",
        geo_lat=22.3193,
        geo_lon=114.1694,
    )
    print(f"  🚨 Threat Triggered: {threat_res['result']} | Alert: {threat_res.get('threat_analysis', {}).get('risk_flag')}")

    # =========================================================================
    # 3. NORDIC ECOMOBILITY (EU Battery Passport Compliance)
    # =========================================================================
    print("\n[3/3] Seeding Nordic EcoMobility (EU Battery Passport)...")
    client.register_manufacturer(
        manufacturer_id="MFR-CLEANTECH-01",
        name="Nordic EcoMobility Systems AB",
        key_id="KEY-NORDIC-1",
        public_key_b64=pub_key,
    )

    nordic_batch = client.issue_products(
        manufacturer_id="MFR-CLEANTECH-01",
        product_code="SOLID-STATE-CELL-100",
        product_name="Automotive Solid-State Battery Cell 100Ah",
        batch_id="NORDIC-CELL-B44",
        quantity=2,
        gtin="07350012345671",
        carbon_footprint_kg=3.10,
        recycled_content_pct=52.0,
        repairability_score=8.0,
        circularity_status="CLOSED_LOOP_RECYCLING",
        compliance_certs=["EU_BATTERIES_2023_1542", "ISO_14040", "UN_38.3"],
    )
    p_cell = nordic_batch["products"][0]
    pid_cell = p_cell["product_id"]
    print(f"  • Issued Battery Cell: {pid_cell}")

    # Summary
    print("\n============================================================")
    print("✨ OPAP Enterprise Demo Seeding Complete!")
    print(f"1. PharmaTech Vaccine ID: {pid_vax}")
    print(f"2. LuxeArtisans Watch ID: {pid_watch} (Active AI Threat)")
    print(f"3. Nordic Battery Cell ID: {pid_cell}")
    print("============================================================")
    print("Explore live at: http://127.0.0.1:8080/ui")


if __name__ == "__main__":
    seed_database()
