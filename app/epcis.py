"""GS1 EPCIS 2.0 (Electronic Product Code Information Services) Supply Chain Custody Engine.

Tracks multi-hop custody transitions across manufacturers, logistics providers,
customs authorities, regional distribution hubs, and retail points of sale.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
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
    step_enum = CustodyBusinessStep(business_step)
    disp_enum = CustodyDisposition(disposition)
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
