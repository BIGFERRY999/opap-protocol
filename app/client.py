"""Official OPAP Python Client SDK.

Enables seamless integration with ERP systems (SAP, Oracle NetSuite),
warehouse management systems (WMS), industrial barcode printers (Zebra, Sato),
and mobile supply chain scanners.
"""

from __future__ import annotations

import json
from typing import Any
import urllib.parse
import urllib.request
import urllib.error


class OPAPClientError(Exception):
    """Base exception for OPAP client failures."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(f"HTTP {status_code}: {detail}")
        self.status_code = status_code
        self.detail = detail


class OPAPClient:
    """High-performance API client for OPAP Enterprise Platform."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        raw_response: bool = False,
    ) -> Any:
        url = f"{self.base_url}{path}"
        req_headers = {"User-Agent": "OPAP-Python-SDK/0.1.0"}
        if self.api_key:
            req_headers["X-API-Key"] = self.api_key
        if headers:
            req_headers.update(headers)

        payload_bytes = None
        if data is not None:
            req_headers["Content-Type"] = "application/json"
            payload_bytes = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=payload_bytes, headers=req_headers, method=method)

        try:
            with urllib.request.urlopen(req) as resp:
                raw_bytes = resp.read()
                if raw_response:
                    return raw_bytes.decode("utf-8")
                return json.loads(raw_bytes.decode("utf-8"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(err_body)
                detail = err_json.get("detail") or err_json.get("message") or err_body
            except Exception:
                detail = err_body
            raise OPAPClientError(e.code, str(detail)) from e

    # --- System & Diagnostics ---

    def health(self) -> dict[str, Any]:
        """Checks API health and version."""
        return self._request("GET", "/health")

    def signer_status(self) -> dict[str, Any]:
        """Inspects active cryptographic signer provider (HSM/KMS/Env)."""
        return self._request("GET", "/v1/signer")

    # --- Manufacturer & Product Management ---

    def register_manufacturer(
        self,
        manufacturer_id: str,
        name: str,
        key_id: str,
        public_key_b64: str,
    ) -> dict[str, Any]:
        """Registers a verified manufacturer and Ed25519 public key."""
        payload = {
            "manufacturer_id": manufacturer_id,
            "name": name,
            "key_id": key_id,
            "public_key_b64": public_key_b64,
        }
        return self._request("POST", "/v1/manufacturers", data=payload)

    def issue_products(
        self,
        manufacturer_id: str,
        product_code: str,
        product_name: str,
        batch_id: str,
        quantity: int = 1,
        gtin: str | None = None,
        carbon_footprint_kg: float | None = None,
        recycled_content_pct: float | None = None,
        repairability_score: float | None = None,
        circularity_status: str | None = None,
        compliance_certs: list[str] | None = None,
    ) -> dict[str, Any]:
        """Issues 1 to 5,000 uniquely serialized, cryptographically signed product items."""
        payload: dict[str, Any] = {
            "product_code": product_code,
            "product_name": product_name,
            "batch_id": batch_id,
            "quantity": quantity,
        }
        if gtin:
            payload["gtin"] = gtin
        if carbon_footprint_kg is not None:
            payload["carbon_footprint_kg"] = carbon_footprint_kg
        if recycled_content_pct is not None:
            payload["recycled_content_pct"] = recycled_content_pct
        if repairability_score is not None:
            payload["repairability_score"] = repairability_score
        if circularity_status:
            payload["circularity_status"] = circularity_status
        if compliance_certs:
            payload["compliance_certs"] = compliance_certs

        return self._request("POST", f"/v1/manufacturers/{manufacturer_id}/products", data=payload)

    # --- Verification Core ---

    def verify(
        self,
        product_id: str,
        lane: str = "CONSUMER",
        merchant_id: str | None = None,
        geo_lat: float | None = None,
        geo_lon: float | None = None,
        city: str | None = None,
    ) -> dict[str, Any]:
        """Consumes one one-time merchant or consumer verification lane."""
        payload: dict[str, Any] = {
            "product_id": product_id,
            "lane": lane,
        }
        if merchant_id:
            payload["merchant_id"] = merchant_id
        if geo_lat is not None:
            payload["geo_lat"] = geo_lat
        if geo_lon is not None:
            payload["geo_lon"] = geo_lon
        if city:
            payload["city"] = city

        return self._request("POST", "/v1/verify", data=payload)

    def batch_verify(
        self,
        product_ids: list[str],
        default_lane: str = "CONSUMER",
        default_merchant_id: str | None = None,
    ) -> dict[str, Any]:
        """Bulk verifies multiple products in a single atomic transaction."""
        payload = {
            "default_lane": default_lane,
            "default_merchant_id": default_merchant_id,
            "items": [{"product_id": pid} for pid in product_ids],
        }
        return self._request("POST", "/v1/verify/batch", data=payload)

    # --- GS1 Digital Link & EU DPP ---

    def resolve_gs1(self, gtin: str, serial: str, accept: str = "application/ld+json") -> Any:
        """Resolves a GS1 Digital Link (Sunrise 2027) URI."""
        return self._request(
            "GET",
            f"/01/{gtin}/21/{serial}",
            headers={"Accept": accept},
            raw_response="image/svg" in accept,
        )

    def get_dpp(self, product_id: str) -> dict[str, Any]:
        """Retrieves EU ESPR Digital Product Passport (DPP) compliance records."""
        return self._request("GET", f"/v1/products/{product_id}/dpp")

    # --- GS1 EPCIS 2.0 Custody ---

    def get_custody(self, product_id: str, epcis_format: bool = False) -> dict[str, Any]:
        """Fetches product custody history (default JSON or standard EPCIS 2.0 JSON-LD)."""
        fmt = "epcis" if epcis_format else "json"
        return self._request("GET", f"/v1/products/{product_id}/custody?format={fmt}")

    def log_custody_event(
        self,
        product_id: str,
        business_step: str,
        disposition: str,
        location_name: str,
        custodian_id: str,
        custodian_name: str,
        location_gln: str | None = None,
        geo_lat: float | None = None,
        geo_lon: float | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Appends an immutable GS1 EPCIS 2.0 custody event along the supply chain."""
        payload = {
            "business_step": business_step,
            "disposition": disposition,
            "location_name": location_name,
            "custodian_id": custodian_id,
            "custodian_name": custodian_name,
            "location_gln": location_gln,
            "geo_lat": geo_lat,
            "geo_lon": geo_lon,
            "notes": notes,
        }
        return self._request("POST", f"/v1/products/{product_id}/custody", data=payload)

    # --- AI Forensics & Threat Surveillance ---

    def get_forensics(self, product_id: str) -> dict[str, Any]:
        """Generates an AI threat report with impossible travel and replay analysis."""
        return self._request("GET", f"/v1/products/{product_id}/forensics")

    def get_global_threats(self, limit: int = 50) -> dict[str, Any]:
        """Fetches active supply chain threats and anomalies from the global radar."""
        return self._request("GET", f"/v1/forensics/threats?limit={limit}")

    # --- Industrial Packaging ---

    def get_label_svg(self, product_id: str, width_mm: int = 100, height_mm: int = 50) -> str:
        """Fetches a print-ready vector packaging label (SVG)."""
        return self._request(
            "GET",
            f"/v1/products/{product_id}/label.svg?width_mm={width_mm}&height_mm={height_mm}",
            headers={"Accept": "image/svg+xml"},
            raw_response=True,
        )

    def get_batch_sheet_html(self, manufacturer_id: str, batch_id: str | None = None) -> str:
        """Fetches printable multi-up sticker sheet HTML."""
        path = f"/v1/manufacturers/{manufacturer_id}/labels/sheet"
        if batch_id:
            path += f"?batch_id={urllib.parse.quote(batch_id)}"
        return self._request("GET", path, headers={"Accept": "text/html"}, raw_response=True)
