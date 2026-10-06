"""GS1 Digital Link (Sunrise 2027) syntax engine & GTIN validator for OPAP.

Conforms to GS1 Digital Link URI Syntax Standard v1.7.0.
Enables POS scanners, warehouse RFID/2D scanners, and consumer smartphones
to parse and resolve products according to GS1 Application Identifiers (AIs).
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urlparse


GS1_AI_DESCRIPTIONS: dict[str, str] = {
    "01": "Global Trade Item Number (GTIN)",
    "21": "Serial Number",
    "10": "Batch or Lot Number",
    "17": "Expiration Date (YYMMDD)",
    "22": "Secondary Data / Internal Product Variant",
    "310": "Net Weight (kg)",
    "400": "Customer Purchase Order Number",
    "414": "Global Location Number (GLN)",
}


def calculate_gtin_check_digit(digits_str: str) -> int:
    """Calculates GS1 standard Modulo 10 check digit for GTIN (8, 12, 13, 14 digits)."""
    clean = "".join(ch for ch in digits_str if ch.isdigit())
    if not clean:
        return 0
    # Process from right to left with alternating weights of 3 and 1
    total = 0
    for idx, char in enumerate(reversed(clean)):
        weight = 3 if idx % 2 == 0 else 1
        total += int(char) * weight
    remainder = total % 10
    return (10 - remainder) % 10


def validate_gtin(gtin: str) -> bool:
    """Validates length (8, 12, 13, 14 digits) and Modulo 10 check digit."""
    clean = "".join(ch for ch in gtin if ch.isdigit())
    if len(clean) not in (8, 12, 13, 14):
        return False
    payload = clean[:-1]
    expected_check = calculate_gtin_check_digit(payload)
    return int(clean[-1]) == expected_check


def pad_gtin14(gtin: str) -> str:
    """Normalizes any valid GTIN (8, 12, 13 digits) to standard 14-digit GTIN-14 string."""
    clean = "".join(ch for ch in gtin if ch.isdigit())
    return clean.zfill(14)


def build_digital_link_uri(
    base_url: str,
    gtin: str,
    serial_number: str,
    batch_id: str | None = None,
    expiry_yymmdd: str | None = None,
) -> str:
    """Constructs a conformant GS1 Digital Link URI.
    
    Example: https://id.opap.example/01/00012345678905/21/SER-001?10=LOT-99&17=281231
    """
    gtin14 = pad_gtin14(gtin)
    root = base_url.rstrip("/")
    uri = f"{root}/01/{gtin14}/21/{serial_number}"
    
    query_parts: list[str] = []
    if batch_id:
        query_parts.append(f"10={batch_id}")
    if expiry_yymmdd:
        query_parts.append(f"17={expiry_yymmdd}")
    
    if query_parts:
        uri += "?" + "&".join(query_parts)
    return uri


def parse_digital_link_uri(raw_uri_or_path: str) -> dict[str, Any]:
    """Parses a GS1 Digital Link URI into structured Application Identifiers (AIs).
    
    Handles both path-based qualifiers (/01/../21/..) and query parameter qualifiers (?10=..&17=..).
    """
    parsed = urlparse(raw_uri_or_path)
    path = parsed.path.strip("/")
    segments = path.split("/")

    result: dict[str, Any] = {
        "gtin": None,
        "serial_number": None,
        "batch_id": None,
        "expiry_date": None,
        "attributes": {},
    }

    # Extract path-based AIs in pairs
    idx = 0
    while idx < len(segments) - 1:
        ai = segments[idx]
        val = segments[idx + 1]
        if ai == "01":
            result["gtin"] = pad_gtin14(val)
        elif ai == "21":
            result["serial_number"] = val
        elif ai == "10":
            result["batch_id"] = val
        elif ai == "17":
            result["expiry_date"] = val
        else:
            result["attributes"][ai] = val
        idx += 2

    # Extract query-based AIs
    if parsed.query:
        query_dict = parse_qs(parsed.query)
        for key, values in query_dict.items():
            val = values[0] if values else None
            if not val:
                continue
            if key == "10":
                result["batch_id"] = val
            elif key == "17":
                result["expiry_date"] = val
            elif key == "21":
                result["serial_number"] = val
            elif key == "01":
                result["gtin"] = pad_gtin14(val)
            else:
                result["attributes"][key] = val

    return result
