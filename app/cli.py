"""OPAP Enterprise Command-Line Interface (CLI).

Enables factory operators, warehouse managers, brand inspectors, and developers
to interact with the OPAP trust layer directly from terminal workflows and automated scripts.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from .client import OPAPClient, OPAPClientError


def format_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def main():
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        prog="opap-cli",
        description="OPAP Protocol // Enterprise CLI & Brand Protection Utility",
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("OPAP_URL", "http://127.0.0.1:8080"),
        help="OPAP API Base URL (default: http://127.0.0.1:8080 or $OPAP_URL)",
    )
    parser.add_argument(
        "--key",
        default=os.environ.get("OPAP_API_KEY", "dev-change-me"),
        help="Management API Key (default: dev-change-me or $OPAP_API_KEY)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Sub-commands")

    # 1. Health
    subparsers.add_parser("health", help="Check system health and protocol version")

    # 2. Signer
    subparsers.add_parser("signer", help="Inspect active cryptographic hardware signer")

    # 3. Manufacturer registration
    mfr_p = subparsers.add_parser("mfr", help="Manage registered manufacturers")
    mfr_sub = mfr_p.add_subparsers(dest="mfr_cmd", required=True)
    mfr_reg = mfr_sub.add_parser("register", help="Register a manufacturer and public key")
    mfr_reg.add_argument("--id", required=True, help="Manufacturer ID")
    mfr_reg.add_argument("--name", required=True, help="Manufacturer Legal Name")
    mfr_reg.add_argument("--key-id", default="KEY-1", help="Public Key ID")
    mfr_reg.add_argument("--pub", help="Ed25519 public key base64 (fetches active signer if omitted)")

    # 4. Product Issuance
    issue_p = subparsers.add_parser("issue", help="Issue cryptographically signed product batch")
    issue_p.add_argument("--mfr", required=True, help="Manufacturer ID")
    issue_p.add_argument("--code", required=True, help="Product SKU code")
    issue_p.add_argument("--name", required=True, help="Product trade name")
    issue_p.add_argument("--batch", required=True, help="Production batch/lot number")
    issue_p.add_argument("--qty", type=int, default=1, help="Quantity to issue (1 - 5000)")
    issue_p.add_argument("--gtin", help="14-digit GS1 GTIN")
    issue_p.add_argument("--carbon", type=float, default=1.25, help="Carbon footprint (kg CO2e)")
    issue_p.add_argument("--recycled", type=float, default=30.0, help="Recycled content percentage")
    issue_p.add_argument("--repairability", type=float, default=8.5, help="Repairability index (0-10)")

    # 5. Product Verification
    verify_p = subparsers.add_parser("verify", help="Authenticate a product token")
    verify_p.add_argument("product_id", help="Product ID or GS1 URI")
    verify_p.add_argument("--lane", choices=["CONSUMER", "MERCHANT"], default="CONSUMER", help="Verification lane")
    verify_p.add_argument("--merchant-id", help="Merchant ID (required for MERCHANT lane)")
    verify_p.add_argument("--lat", type=float, help="GPS Latitude")
    verify_p.add_argument("--lon", type=float, help="GPS Longitude")
    verify_p.add_argument("--city", help="Scan City / Facility name")

    # 6. Digital Product Passport (DPP)
    dpp_p = subparsers.add_parser("dpp", help="Retrieve EU ESPR Digital Product Passport")
    dpp_p.add_argument("product_id", help="Product ID")

    # 7. Custody Track & Trace
    custody_p = subparsers.add_parser("custody", help="Manage GS1 EPCIS 2.0 supply chain custody")
    custody_sub = custody_p.add_subparsers(dest="custody_cmd", required=True)
    c_show = custody_sub.add_parser("show", help="View custody timeline")
    c_show.add_argument("product_id", help="Product ID")
    c_show.add_argument("--epcis", action="store_true", help="Export as standard EPCIS 2.0 JSON-LD")

    c_log = custody_sub.add_parser("log", help="Log a custody transition")
    c_log.add_argument("product_id", help="Product ID")
    c_log.add_argument("--step", required=True, help="Business step (SHIPPING, RECEIVING, CUSTOMS_CLEARANCE, etc.)")
    c_log.add_argument("--disp", default="ACTIVE", help="Disposition (ACTIVE, IN_TRANSIT, HELD)")
    c_log.add_argument("--location", required=True, help="Location name")
    c_log.add_argument("--gln", help="GS1 Global Location Number (GLN)")
    c_log.add_argument("--custodian-id", default="CUST-AGENT", help="Custodian ID")
    c_log.add_argument("--custodian-name", required=True, help="Custodian Name")
    c_log.add_argument("--notes", help="Audit notes")

    # 8. Industrial Packaging Label
    label_p = subparsers.add_parser("label", help="Generate packaging vector label (SVG)")
    label_p.add_argument("product_id", help="Product ID")
    label_p.add_argument("--out", help="Output file path (default: stdout)")
    label_p.add_argument("--width", type=int, default=100, help="Label width in mm")
    label_p.add_argument("--height", type=int, default=50, help="Label height in mm")

    # 9. AI Surveillance Threat Radar
    subparsers.add_parser("threats", help="Inspect global AI counterfeit threat surveillance feed")

    # 10. Key Transparency & JWKS
    trans_p = subparsers.add_parser("transparency", help="Query Key Transparency, CRL, and Merkle proofs")
    trans_sub = trans_p.add_subparsers(dest="trans_cmd", required=True)
    trans_sub.add_parser("jwks", help="Export RFC 7517 JSON Web Key Set")
    trans_sub.add_parser("crl", help="Export Certificate Revocation List")
    trans_sub.add_parser("merkle", help="Inspect RFC 6962 SHA-256 Merkle root hash")

    # 11. Offline Verification (V-Pass)
    offline_p = subparsers.add_parser("offline", help="Manage offline verification tokens (V-Pass)")
    off_sub = offline_p.add_subparsers(dest="off_cmd", required=True)
    off_get = off_sub.add_parser("get-token", help="Generate offline verification token")
    off_get.add_argument("product_id", help="Product ID")
    off_verify = off_sub.add_parser("verify", help="Validate an offline token locally/server-side")
    off_verify.add_argument("token", help="Offline token string (OPAP.V1...)")

    # 12. Sector DPP Generator
    sec_p = subparsers.add_parser("sector-dpp", help="Generate EU CIRPASS 2.0 multi-sector DPP")
    sec_p.add_argument("product_id", help="Product ID")
    sec_p.add_argument("--sector", choices=["battery", "textile", "electronics", "pharma"], default="battery", help="Industry sector")
    sec_p.add_argument("--format", choices=["json", "html"], default="json", help="Output format")

    args = parser.parse_args()
    client = OPAPClient(base_url=args.url, api_key=args.key)

    try:
        if args.command == "health":
            res = client.health()
            print(f"✅ OPAP Status: {res.get('status')} | Protocol: {res.get('protocol')} v{res.get('version')}")

        elif args.command == "signer":
            res = client.signer_status()
            print("🔐 Active Cryptographic Signer:")
            print(format_json(res))

        elif args.command == "transparency":
            if args.trans_cmd == "jwks":
                res = client.get_jwks()
                print("🔑 RFC 7517 / 8037 JSON Web Key Set (JWKS):")
                print(format_json(res))
            elif args.trans_cmd == "crl":
                res = client.get_crl()
                print("🚫 Key Certificate Revocation List (CRL):")
                print(format_json(res))
            elif args.trans_cmd == "merkle":
                res = client.get_merkle_root()
                print("🌳 RFC 6962 Merkle Key Transparency Root:")
                print(format_json(res))

        elif args.command == "offline":
            if args.off_cmd == "get-token":
                res = client.get_offline_token(args.product_id)
                print(f"🎫 Offline V-Pass Token for {args.product_id}:")
                print(res["offline_token"])
            elif args.off_cmd == "verify":
                res = client.verify_offline(args.token)
                is_valid = res.get("valid", False)
                status_emoji = "✅" if is_valid else "❌"
                print(f"{status_emoji} Offline Verification Result: {res.get('reason')}")
                print(format_json(res))

        elif args.command == "sector-dpp":
            res = client.get_sector_dpp(args.product_id, sector=args.sector, format=args.format)
            if args.format == "html":
                print(res)
            else:
                print(format_json(res))

        elif args.command == "mfr":
            if args.mfr_cmd == "register":
                pub = args.pub
                if not pub:
                    signer_data = client.signer_status()
                    pub = signer_data["public_key_b64"]
                res = client.register_manufacturer(
                    manufacturer_id=args.id,
                    name=args.name,
                    key_id=args.key_id,
                    public_key_b64=pub,
                )
                print(f"✅ Manufacturer registered: {res.get('manufacturer_id')} ({args.name})")

        elif args.command == "issue":
            res = client.issue_products(
                manufacturer_id=args.mfr,
                product_code=args.code,
                product_name=args.name,
                batch_id=args.batch,
                quantity=args.qty,
                gtin=args.gtin,
                carbon_footprint_kg=args.carbon,
                recycled_content_pct=args.recycled,
                repairability_score=args.repairability,
            )
            print(f"🎉 Successfully issued {res['count']} signed item(s):")
            for p in res.get("products", []):
                print(f"  • ID: {p['product_id']}")
                print(f"    Serial: {p['serial_number']} | GTIN: {p.get('gtin')}")
                print(f"    GS1 Link: {p.get('gs1_digital_link_uri')}")

        elif args.command == "verify":
            pid = args.product_id
            if "/01/" in pid and "/21/" in pid:
                pid = pid.split("/21/")[1].split("?")[0].split("/")[0]
            elif "/v1/verify/" in pid:
                pid = pid.split("/v1/verify/")[1].split("?")[0].split("/")[0]

            res = client.verify(
                product_id=pid,
                lane=args.lane,
                merchant_id=args.merchant_id,
                geo_lat=args.lat,
                geo_lon=args.lon,
                city=args.city,
            )
            result_code = res.get("result")
            status_emoji = "✅" if result_code == "AUTHENTIC" else ("⚠️" if result_code == "ALREADY_VERIFIED" else "❌")
            print(f"\n{status_emoji} Result: {result_code}")
            prod = res.get("product") or {}
            print(f"Product: {prod.get('product_name')} (Batch #{prod.get('batch')})")
            print(f"Manufacturer: {prod.get('manufacturer')}")
            threat = res.get("threat_analysis") or {}
            if threat.get("risk_flag"):
                print(f"🚨 ALERT: {threat.get('risk_flag')} - {threat.get('threat_advisory')}")

        elif args.command == "dpp":
            res = client.get_dpp(args.product_id)
            print("🇪🇺 EU ESPR Digital Product Passport (EU 2024/1781):")
            print(f"Product: {res['product_name']} | GTIN-14: {res.get('gtin')}")
            print(f"Manufacturer: {res['manufacturer']}")
            print(f"Carbon Footprint: {res['carbon_footprint_kg']} kg CO2e")
            print(f"Recycled Content: {res['recycled_content_pct']}% | Repairability: {res['repairability_score']}/10")
            print(f"Circularity Status: {res['circularity_status']}")
            print(f"Ed25519 Seal Verified: {res['ed25519_verified']}")
            print(f"Certificates: {', '.join(res.get('compliance_certs', []))}")
            print(f"Digital Link: {res.get('gs1_digital_link_uri')}")

        elif args.command == "custody":
            if args.custody_cmd == "show":
                res = client.get_custody(args.product_id, epcis_format=args.epcis)
                print(format_json(res))
            elif args.custody_cmd == "log":
                res = client.log_custody_event(
                    product_id=args.product_id,
                    business_step=args.step,
                    disposition=args.disp,
                    location_name=args.location,
                    custodian_id=args.custodian_id,
                    custodian_name=args.custodian_name,
                    location_gln=args.gln,
                    notes=args.notes,
                )
                print(f"✅ Custody transition recorded: {res['business_step']} at {res['location_name']}")

        elif args.command == "label":
            svg = client.get_label_svg(args.product_id, width_mm=args.width, height_mm=args.height)
            if args.out:
                with open(args.out, "w", encoding="utf-8") as f:
                    f.write(svg)
                print(f"🏷️ Label written to {args.out} ({len(svg)} bytes)")
            else:
                print(svg)

        elif args.command == "threats":
            res = client.get_global_threats()
            threats = res.get("threats", [])
            print(f"🤖 Global AI Threat Feed ({len(threats)} active anomalies):")
            if not threats:
                print("  • No active supply chain threats detected.")
            for t in threats:
                print(f"  🚨 [{t['risk_flag']}] Item: {t['product_id']} | City: {t.get('city')} | Time: {t['occurred_at']}")

    except OPAPClientError as e:
        print(f"❌ Error ({e.status_code}): {e.detail}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
