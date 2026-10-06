"""GS1 EPCIS 2.0 (Electronic Product Code Information Services) Supply Chain Custody Engine.

Tracks multi-hop custody transitions across manufacturers, logistics providers,
customs authorities, regional distribution hubs, and retail points of sale.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import CustodyBusinessStep, CustodyDisposition, CustodyEvent, Product


def add_custody_event(
    db: Session,
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
    occurred_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> CustodyEvent:
    """Records an immutable EPCIS 2.0 custody event along the supply chain."""
    step_enum = CustodyBusinessStep(business_step.upper())
    disp_enum = CustodyDisposition(disposition.upper())
    timestamp = occurred_at or datetime.now(timezone.utc)

    event = CustodyEvent(
        event_id=str(uuid.uuid4()),
        product_id=product_id,
        business_step=step_enum,
        disposition=disp_enum,
        location_gln=location_gln,
        location_name=location_name,
        geo_lat=geo_lat,
        geo_lon=geo_lon,
        custodian_id=custodian_id,
        custodian_name=custodian_name,
        notes=notes,
        occurred_at=timestamp,
        metadata_json=metadata or {},
    )
    db.add(event)
    db.flush()
    return event


def export_epcis2_document(product: Product, events: list[CustodyEvent]) -> dict[str, Any]:
    """Generates a standard GS1 EPCIS 2.0 JSON-LD compliant document."""
    epc_urn = f"urn:epc:id:sgtin:{product.gtin or '00000000000000'}.{product.serial_number}"
    
    event_list = []
    for ev in events:
        read_point_id = (
            f"urn:epc:id:sgln:{ev.location_gln}"
            if ev.location_gln
            else f"geo:{ev.geo_lat},{ev.geo_lon}" if ev.geo_lat is not None and ev.geo_lon is not None
            else f"urn:opap:loc:{ev.location_name.replace(' ', '_').lower()}"
        )
        
        event_list.append({
            "type": "ObjectEvent",
            "eventID": f"urn:uuid:{ev.event_id}",
            "eventTime": ev.occurred_at.isoformat().replace("+00:00", "Z"),
            "eventTimeZoneOffset": "+00:00",
            "epcList": [epc_urn],
            "action": "OBSERVE",
            "bizStep": f"urn:epcglobal:cbv:bizstep:{ev.business_step.value.lower()}",
            "disposition": f"urn:epcglobal:cbv:disp:{ev.disposition.value.lower()}",
            "readPoint": {
                "id": read_point_id,
            },
            "bizLocation": {
                "name": ev.location_name,
            },
            "custodian": {
                "id": ev.custodian_id,
                "name": ev.custodian_name,
            },
            "userExtensions": {
                "opap:product_id": product.product_id,
                "opap:notes": ev.notes,
                "opap:metadata": ev.metadata_json,
            },
        })

    return {
        "@context": [
            "https://ref.gs1.org/standards/epcis/2.0.0/epcis-context.jsonld",
            {
                "opap": "https://opap.org/spec/v0.1/epcis#",
            },
        ],
        "type": "EPCISDocument",
        "schemaVersion": "2.0",
        "creationDate": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "epcisBody": {
            "eventList": event_list,
        },
    }


def parse_cbv_business_step(raw_step: str) -> CustodyBusinessStep:
    """Normalizes standard CBV bizStep URNs or plain strings into CustodyBusinessStep enum."""
    val = raw_step.split(":")[-1].upper()
    valid_map = {
        "COMMISSIONING": CustodyBusinessStep.COMMISSIONING,
        "SHIPPING": CustodyBusinessStep.SHIPPING,
        "CUSTOMS_CLEARANCE": CustodyBusinessStep.CUSTOMS_CLEARANCE,
        "CUSTOMSCLEARANCE": CustodyBusinessStep.CUSTOMS_CLEARANCE,
        "RECEIVING": CustodyBusinessStep.RECEIVING,
        "HOLDING": CustodyBusinessStep.HOLDING,
        "RETAIL_SELLING": CustodyBusinessStep.RETAIL_SELLING,
        "RETAILSELLING": CustodyBusinessStep.RETAIL_SELLING,
    }
    return valid_map.get(val, CustodyBusinessStep.SHIPPING)


def parse_cbv_disposition(raw_disp: str) -> CustodyDisposition:
    """Normalizes standard CBV disposition URNs or plain strings into CustodyDisposition enum."""
    val = raw_disp.split(":")[-1].upper()
    valid_map = {
        "ACTIVE": CustodyDisposition.ACTIVE,
        "IN_TRANSIT": CustodyDisposition.IN_TRANSIT,
        "INTRANSIT": CustodyDisposition.IN_TRANSIT,
        "QUARANTINED": CustodyDisposition.QUARANTINED,
        "SOLD": CustodyDisposition.SOLD,
        "RECALLED": CustodyDisposition.RECALLED,
    }
    return valid_map.get(val, CustodyDisposition.ACTIVE)


def ingest_epcis2_document(db: Session, epcis_doc: dict[str, Any]) -> dict[str, Any]:
    """
    Ingests and validates a standard GS1 EPCIS 2.0 JSON-LD Document.
    Parses eventList and records custody transitions for all referenced products.
    """
    epcis_body = epcis_doc.get("epcisBody", {})
    event_list = epcis_body.get("eventList", [])
    if not event_list and isinstance(epcis_doc.get("eventList"), list):
        event_list = epcis_doc["eventList"]

    if not event_list:
        raise ValueError("EPCIS document contains no events in epcisBody.eventList")

    processed_events: list[dict[str, Any]] = []
    affected_product_ids: set[str] = set()

    for idx, raw_ev in enumerate(event_list):
        # 1. Resolve target products
        target_product_ids: list[str] = []
        
        # Check userExtensions
        user_ext = raw_ev.get("userExtensions", {})
        if "opap:product_id" in user_ext and user_ext["opap:product_id"]:
            target_product_ids.append(user_ext["opap:product_id"])

        # Check epcList
        epc_list = raw_ev.get("epcList", [])
        for epc in epc_list:
            if epc.startswith("urn:epc:id:sgtin:"):
                # Format: urn:epc:id:sgtin:GTIN.SERIAL
                parts = epc.split(":")[-1].split(".")
                if len(parts) >= 2:
                    gtin, serial = parts[0], parts[1]
                    prod = db.scalar(select(Product).where(Product.gtin == gtin, Product.serial_number == serial))
                    if not prod:
                        prod = db.scalar(select(Product).where(Product.serial_number == serial))
                    if prod and prod.product_id not in target_product_ids:
                        target_product_ids.append(prod.product_id)
            elif epc.startswith("urn:opap:product:"):
                pid = epc.split(":")[-1]
                if pid not in target_product_ids:
                    target_product_ids.append(pid)

        if not target_product_ids:
            # Fallback: search by serial or direct ID in user extensions
            continue

        # 2. Extract event parameters
        biz_step = parse_cbv_business_step(raw_ev.get("bizStep", "urn:epcglobal:cbv:bizstep:shipping"))
        disposition = parse_cbv_disposition(raw_ev.get("disposition", "urn:epcglobal:cbv:disp:in_transit"))
        
        # Location & ReadPoint
        loc_name = raw_ev.get("bizLocation", {}).get("name") or raw_ev.get("location_name") or "Global Supply Chain Node"
        read_point = raw_ev.get("readPoint", {}).get("id", "")
        location_gln = None
        geo_lat = None
        geo_lon = None

        if "urn:epc:id:sgln:" in read_point:
            location_gln = read_point.split(":")[-1]
        elif read_point.startswith("geo:"):
            try:
                coords = read_point.replace("geo:", "").split(",")
                geo_lat = float(coords[0])
                geo_lon = float(coords[1])
            except (ValueError, IndexError):
                pass

        # Custodian
        custodian_info = raw_ev.get("custodian", {})
        custodian_id = custodian_info.get("id") or raw_ev.get("custodian_id") or "CUST-SUPPLY-CHAIN"
        custodian_name = custodian_info.get("name") or raw_ev.get("custodian_name") or "Global Logistics Partner"

        # Timestamp
        event_time_str = raw_ev.get("eventTime")
        occurred_at = datetime.now(timezone.utc)
        if event_time_str:
            try:
                occurred_at = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        notes = user_ext.get("opap:notes") or raw_ev.get("notes") or f"Ingested from EPCIS 2.0 Document ({raw_ev.get('type', 'ObjectEvent')})"

        # 3. Add Custody Events
        for pid in target_product_ids:
            ev = CustodyEvent(
                event_id=str(uuid.uuid4()),
                product_id=pid,
                business_step=biz_step,
                disposition=disposition,
                location_gln=location_gln,
                location_name=loc_name,
                geo_lat=geo_lat,
                geo_lon=geo_lon,
                custodian_id=custodian_id,
                custodian_name=custodian_name,
                notes=notes,
                occurred_at=occurred_at,
                metadata_json=user_ext.get("opap:metadata") or {},
            )
            db.add(ev)
            affected_product_ids.add(pid)
            processed_events.append({
                "event_id": ev.event_id,
                "product_id": pid,
                "business_step": biz_step.value,
                "disposition": disposition.value,
                "location_name": loc_name,
                "occurred_at": occurred_at.isoformat(),
            })

    db.flush()

    return {
        "status": "INGESTED_SUCCESSFULLY",
        "schema": "GS1_EPCIS_2.0",
        "total_events_processed": len(processed_events),
        "affected_products_count": len(affected_product_ids),
        "affected_product_ids": list(affected_product_ids),
        "events": processed_events,
    }
