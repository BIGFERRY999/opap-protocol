import base64
import os
import secrets
import string
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from .config import get_settings
from .crypto import b64url, sign_payload, utc_iso, verify_signature
from .database import Base, engine, get_db
from .models import (
    AuditEvent,
    CustodyBusinessStep,
    CustodyDisposition,
    CustodyEvent,
    Lane,
    LaneStatus,
    Manufacturer,
    ManufacturerKey,
    Product,
    ProductPassport,
    Status,
    VerificationEvent,
    VerificationLane,
)
from .schemas import (
    BatchSummary,
    BatchVerifyRequest,
    BatchVerifyResponse,
    BatchVerifyResultItem,
    CustodyEventCreate,
    CustodyEventResponse,
    DPPResponse,
    ForensicThreatReport,
    GS1ResolveResponse,
    ManufacturerCreate,
    ProductIssue,
    RevokeRequest,
    SignerStatusResponse,
    VerifyRequest,
)
from .signer import SignerConfigError, SignerError, get_signer
from .ui import get_scanner_html
from .gs1 import build_digital_link_uri, parse_digital_link_uri, pad_gtin14, validate_gtin
from .ai import ForensicEngine
from .epcis import add_custody_event, export_epcis2_document, ingest_epcis2_document
from .packaging import generate_single_label_svg, generate_batch_label_sheet_html


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="OPAP Technical Protocol",
    version="0.1.0",
    description="Open Product Authentication Protocol reference API",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def invalid_request_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "result": "INVALID_REQUEST",
            "errors": [
                {"field": ".".join(str(x) for x in e["loc"]), "message": e["msg"]}
                for e in exc.errors()
            ],
        },
    )


def require_api_key(x_api_key: str | None = Header(default=None)):
    if not x_api_key or not secrets.compare_digest(x_api_key, get_settings().api_key):
        raise HTTPException(status_code=401, detail="Unauthorized")


def audit(db: Session, actor: str, action: str, subject: str, details: dict | None = None):
    db.add(AuditEvent(actor=actor, action=action, subject=subject, details=details or {}))


def b32_id(nbytes: int = 8) -> str:
    return base64.b32encode(secrets.token_bytes(nbytes)).decode("ascii").rstrip("=")


def product_id(manufacturer_id: str) -> str:
    # Stable manufacturer prefix plus 80 bits of CSPRNG identity.
    prefix = "".join(ch for ch in manufacturer_id.upper() if ch.isalnum())[:12]
    return f"OPAP-NG-{prefix}-{b32_id(10)}"


# --- Web UI Routes ---

@app.get("/", response_class=HTMLResponse)
@app.get("/scanner", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def web_scanner_view():
    """Interactive Web Scanner, Batch Verifier, and Demo Sandbox."""
    return HTMLResponse(get_scanner_html())


@app.get("/health")
def health():
    return {"status": "ok", "protocol": "OPAP", "version": "0.1"}


# --- Signer / Hardware Management ---

@app.get("/v1/signer")
def get_signer_info():
    """Inspect active cryptographic signing provider and public key."""
    try:
        signer = get_signer()
        return signer.describe()
    except Exception as e:
        return {"provider": "error", "error": str(e)}


# --- Manufacturer & Product Management ---

@app.post("/v1/manufacturers", status_code=201, dependencies=[Depends(require_api_key)])
def create_manufacturer(body: ManufacturerCreate, db: Session = Depends(get_db)):
    try:
        public = base64.b64decode(body.public_key_b64, validate=True)
    except Exception:
        raise HTTPException(422, "public_key_b64 must be valid base64")
    if len(public) != 32:
        raise HTTPException(422, "Ed25519 public key must be 32 bytes")
    if db.get(Manufacturer, body.manufacturer_id):
        raise HTTPException(409, "Manufacturer already exists")
    manufacturer = Manufacturer(id=body.manufacturer_id, name=body.name)
    db.add(manufacturer)
    db.flush()
    db.add(ManufacturerKey(manufacturer_id=body.manufacturer_id, key_id=body.key_id, public_key=public))
    audit(db, "api-key", "MANUFACTURER_REGISTERED", body.manufacturer_id, {"key_id": body.key_id})
    db.commit()
    return {"manufacturer_id": manufacturer.id, "name": manufacturer.name, "key_id": body.key_id, "status": "ACTIVE"}


@app.post("/v1/manufacturers/{manufacturer_id}/products", status_code=201, dependencies=[Depends(require_api_key)])
def issue_products(manufacturer_id: str, body: ProductIssue, db: Session = Depends(get_db)):
    manufacturer = db.get(Manufacturer, manufacturer_id)
    if not manufacturer or manufacturer.status != Status.ACTIVE:
        raise HTTPException(404, "Active manufacturer not found")
    key = db.scalar(
        select(ManufacturerKey)
        .where(ManufacturerKey.manufacturer_id == manufacturer_id, ManufacturerKey.status == Status.ACTIVE)
        .order_by(ManufacturerKey.id.desc())
    )
    if not key:
        raise HTTPException(409, "No active manufacturer key")

    # Retrieve pluggable signer provider (Env, File, AWS KMS, GCP KMS, or PKCS11 HSM)
    try:
        signer = get_signer()
    except SignerConfigError as e:
        raise HTTPException(503, f"No signing provider configured: {e}")
    except Exception as e:
        raise HTTPException(503, f"Signing provider error: {e}")

    # Refuse signing if configured provider does not match registered manufacturer key
    if signer.get_public_key() != key.public_key:
        raise HTTPException(409, "Configured signer does not match registered manufacturer key")

    issued = datetime.fromisoformat(body.issued_at.replace("Z", "+00:00")) if body.issued_at else datetime.now(timezone.utc)
    if issued.tzinfo is None:
        issued = issued.replace(tzinfo=timezone.utc)

    expiry = datetime.fromisoformat(body.expiry_date.replace("Z", "+00:00")) if body.expiry_date else None
    if expiry and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    # Format or synthesize 14-digit GTIN
    gtin14 = pad_gtin14(body.gtin) if body.gtin else pad_gtin14("0614141" + str(abs(hash(body.product_code)) % 1000000).zfill(6))

    products = []
    for _ in range(body.quantity):
        pid = product_id(manufacturer_id)
        serial = pid.rsplit("-", 1)[-1]
        payload = {
            "protocol": "OPAP",
            "version": "0.1",
            "product_id": pid,
            "manufacturer_id": manufacturer_id,
            "product_code": body.product_code,
            "product_name": body.product_name,
            "batch_id": body.batch_id,
            "serial_number": serial,
            "gtin": gtin14,
            "issued_at": utc_iso(issued),
        }

        try:
            signature = signer.sign(payload)
        except SignerError as e:
            raise HTTPException(503, f"Cryptographic signing failure: {e}")

        prod = Product(
            product_id=pid,
            manufacturer_id=manufacturer_id,
            key_id=key.key_id,
            product_code=body.product_code,
            product_name=body.product_name,
            batch_id=body.batch_id,
            serial_number=serial,
            gtin=gtin14,
            issued_at=issued,
            expiry_date=expiry,
            canonical_payload=payload,
            signature=signature,
        )
        db.add(prod)

        # Initialize Digital Product Passport (EU ESPR)
        dpp = ProductPassport(
            product_id=pid,
            materials_composition=body.materials_composition or {"bio_based_polymer": 75.0, "recycled_core": 25.0},
            carbon_footprint_kg=body.carbon_footprint_kg if body.carbon_footprint_kg is not None else 1.25,
            recycled_content_pct=body.recycled_content_pct if body.recycled_content_pct is not None else 25.0,
            repairability_score=body.repairability_score if body.repairability_score is not None else 8.5,
            circularity_status=body.circularity_status or "RECYCLABLE",
            compliance_certs=body.compliance_certs or ["EU_ESPR_2024", "ISO_14040", "OPAP_TRUST_VERIFIED"],
        )
        db.add(dpp)

        # Record Initial EPCIS Custody Event (Commissioning)
        add_custody_event(
            db=db,
            product_id=pid,
            business_step="COMMISSIONING",
            disposition="ACTIVE",
            location_name=f"{manufacturer.name} Manufacturing Plant #1",
            custodian_id=manufacturer_id,
            custodian_name=manufacturer.name,
            notes="Initial production batch commissioning & cryptographic seal applied.",
        )

        db.add_all([
            VerificationLane(product_id=pid, lane=Lane.MERCHANT),
            VerificationLane(product_id=pid, lane=Lane.CONSUMER),
        ])

        uri = f"{get_settings().public_base_url}/v1/verify/{pid}"
        gs1_uri = build_digital_link_uri(
            get_settings().public_base_url,
            gtin14,
            serial,
            body.batch_id,
            expiry.strftime("%y%m%d") if expiry else None,
        )

        products.append({
            "product_id": pid,
            "serial_number": serial,
            "gtin": gtin14,
            "payload": payload,
            "key_id": key.key_id,
            "signature_b64url": b64url(signature),
            "qr_uri": uri,
            "gs1_digital_link_uri": gs1_uri,
        })

    audit(db, manufacturer_id, "PRODUCTS_ISSUED", body.batch_id, {"quantity": body.quantity})
    db.commit()
    return {"count": len(products), "products": products}


# --- Verification Core ---

def verify_one(db: Session, req: VerifyRequest, commit: bool = True) -> dict:
    lane = Lane(req.lane.value)
    product = db.get(Product, req.product_id)
    risk_flag = None
    geo_anomaly = None

    if product is None:
        result = "INVALID_PRODUCT"
    else:
        manufacturer = db.get(Manufacturer, product.manufacturer_id)
        key = db.scalar(
            select(ManufacturerKey).where(
                ManufacturerKey.manufacturer_id == product.manufacturer_id,
                ManufacturerKey.key_id == product.key_id,
            )
        )
        if not manufacturer or manufacturer.status != Status.ACTIVE or not key or key.status != Status.ACTIVE:
            result = "REVOKED_MANUFACTURER"
        elif not verify_signature(key.public_key, product.canonical_payload, product.signature):
            result = "INVALID_SIGNATURE"
        elif product.status == Status.REVOKED:
            result = "REVOKED_PRODUCT"
        else:
            changed = db.execute(
                update(VerificationLane)
                .where(
                    VerificationLane.product_id == product.product_id,
                    VerificationLane.lane == lane,
                    VerificationLane.status == LaneStatus.UNUSED,
                )
                .values(
                    status=LaneStatus.VERIFIED,
                    verified_at=datetime.now(timezone.utc),
                    merchant_id=req.merchant_id if lane == Lane.MERCHANT else None,
                )
                .execution_options(synchronize_session=False)
            ).rowcount
            if changed == 1:
                result = "AUTHENTIC"
            else:
                result = "ALREADY_VERIFIED"
                risk_flag = "REPLAY_DETECTED"

            # AI Forensics: Evaluate Geo-velocity against last known scan event
            if req.geo_lat is not None and req.geo_lon is not None:
                last_event = db.scalar(
                    select(VerificationEvent)
                    .where(
                        VerificationEvent.product_id == product.product_id,
                        VerificationEvent.geo_lat.is_not(None),
                    )
                    .order_by(VerificationEvent.id.desc())
                )
                if last_event:
                    prev_dict = {
                        "geo_lat": last_event.geo_lat,
                        "geo_lon": last_event.geo_lon,
                        "city": last_event.city or "Previous City",
                        "occurred_at": last_event.occurred_at,
                    }
                    curr_dict = {
                        "geo_lat": req.geo_lat,
                        "geo_lon": req.geo_lon,
                        "city": req.city or "Current City",
                        "occurred_at": datetime.now(timezone.utc),
                    }
                    geo_anomaly = ForensicEngine.evaluate_geo_velocity(prev_dict, curr_dict)
                    if geo_anomaly:
                        risk_flag = geo_anomaly["anomaly_type"]

    ev = VerificationEvent(
        product_id=req.product_id,
        lane=lane,
        result=result,
        risk_flag=risk_flag,
        geo_lat=req.geo_lat,
        geo_lon=req.geo_lon,
        city=req.city,
        ip_address=req.ip_address,
        metadata_json={"geo_anomaly": geo_anomaly} if geo_anomaly else {},
    )
    db.add(ev)
    if commit:
        db.commit()

    mfr = db.get(Manufacturer, product.manufacturer_id) if product else None
    product_info = None if product is None else {
        "product_id": product.product_id,
        "name": product.product_name,
        "product_code": product.product_code,
        "gtin": product.gtin,
        "manufacturer_id": product.manufacturer_id,
        "manufacturer": mfr.name if mfr else None,
        "batch": product.batch_id,
    }
    threat_info = None
    if product:
        threat_info = {
            "risk_flag": risk_flag,
            "geo_anomaly": geo_anomaly,
            "threat_advisory": (
                "🚨 CRITICAL: Replay attack or impossible travel detected across supply chain!"
                if risk_flag
                else "✅ Nominal scan pattern. Cryptographic seal intact."
            ),
        }

    return {
        "result": result,
        "product": product_info,
        "verification": {
            "lane": lane.value,
            "status": "VERIFIED" if result == "AUTHENTIC" else ("ALREADY_VERIFIED" if result == "ALREADY_VERIFIED" else None),
        },
        "event_id": ev.event_id,
        "threat_analysis": threat_info,
    }


@app.post("/v1/verify")
def verify_product(body: VerifyRequest, db: Session = Depends(get_db)):
    """Consume one one-time merchant or consumer verification lane."""
    return verify_one(db, body, commit=True)


@app.post("/v1/verify/batch", response_model=BatchVerifyResponse)
def verify_batch(body: BatchVerifyRequest, db: Session = Depends(get_db)):
    """Batch verify multiple product identifiers in a single operation."""
    results: list[dict[str, Any]] = []
    authentic_count = 0
    replay_count = 0
    invalid_count = 0
    revoked_count = 0

    for item in body.items:
        effective_lane = item.lane or body.default_lane
        effective_merchant = item.merchant_id or (body.default_merchant_id if effective_lane.value == "MERCHANT" else None)
        single_req = VerifyRequest(
            product_id=item.product_id,
            lane=effective_lane,
            merchant_id=effective_merchant,
        )
        res = verify_one(db, single_req, commit=False)

        res_code = res["result"]
        if res_code == "AUTHENTIC":
            authentic_count += 1
        elif res_code == "ALREADY_VERIFIED":
            replay_count += 1
        elif res_code in ("INVALID_PRODUCT", "INVALID_SIGNATURE"):
            invalid_count += 1
        elif res_code in ("REVOKED_PRODUCT", "REVOKED_MANUFACTURER"):
            revoked_count += 1

        results.append({
            "product_id": item.product_id,
            "lane": effective_lane,
            "result": res_code,
            "product": res["product"],
            "verification": res["verification"],
            "event_id": res["event_id"],
        })

    # Commit the entire batch
    db.commit()

    total = len(body.items)
    if total == 0:
        batch_status = "EMPTY"
    elif invalid_count > 0:
        batch_status = "COUNTERFEIT_DETECTED"
    elif revoked_count > 0:
        batch_status = "REVOKED_ITEMS_PRESENT"
    elif replay_count > 0:
        batch_status = "REPLAY_DETECTED"
    elif authentic_count == total:
        batch_status = "ALL_AUTHENTIC"
    else:
        batch_status = "MIXED"

    summary = BatchSummary(
        total=total,
        authentic=authentic_count,
        already_verified=replay_count,
        invalid=invalid_count,
        revoked=revoked_count,
        status=batch_status,
    )
    return BatchVerifyResponse(summary=summary, results=results)


@app.get("/v1/verify/{product_id}")
def verify_uri(product_id: str, request: Request):
    """QR landing point. Returns HTML scanner for web browsers or JSON for API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(get_scanner_html())
    return {
        "protocol": "OPAP",
        "version": "0.1",
        "product_id": product_id,
        "verification_endpoint": "/v1/verify",
        "lanes": ["MERCHANT", "CONSUMER"],
    }


@app.get("/v1/products/{product_id}/qr.svg")
def product_qr(product_id: str, db: Session = Depends(get_db)):
    from io import BytesIO
    import qrcode
    import qrcode.image.svg

    if not db.get(Product, product_id):
        raise HTTPException(404, "Product not found")
    uri = f"{get_settings().public_base_url}/v1/verify/{product_id}"
    image = qrcode.make(uri, image_factory=qrcode.image.svg.SvgImage)
    output = BytesIO()
    image.save(output)
    return Response(
        content=output.getvalue(),
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@app.post("/v1/products/{product_id}/revoke", dependencies=[Depends(require_api_key)])
def revoke_product(product_id: str, body: RevokeRequest, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    product.status = Status.REVOKED
    product.revoked_at = datetime.now(timezone.utc)
    audit(db, "api-key", "PRODUCT_REVOKED", product_id, {"reason": body.reason})
    db.commit()
    return {"product_id": product_id, "status": "REVOKED"}


@app.post("/v1/manufacturers/{manufacturer_id}/revoke", dependencies=[Depends(require_api_key)])
def revoke_manufacturer(manufacturer_id: str, body: RevokeRequest, db: Session = Depends(get_db)):
    manufacturer = db.get(Manufacturer, manufacturer_id)
    if not manufacturer:
        raise HTTPException(404, "Manufacturer not found")
    manufacturer.status = Status.REVOKED
    for key in manufacturer.keys:
        key.status = Status.REVOKED
        key.revoked_at = datetime.now(timezone.utc)
    audit(db, "api-key", "MANUFACTURER_REVOKED", manufacturer_id, {"reason": body.reason})
    db.commit()
    return {"manufacturer_id": manufacturer_id, "status": "REVOKED"}


@app.get("/v1/products/{product_id}")
def product_record(product_id: str, db: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    import hashlib
    from .crypto import canonical_bytes
    return {
        "product_id": p.product_id,
        "payload": p.canonical_payload,
        "key_id": p.key_id,
        "signature_b64url": b64url(p.signature),
        "digest_sha256": hashlib.sha256(canonical_bytes(p.canonical_payload)).hexdigest(),
        "status": p.status.value,
    }


# ==============================================================================
# ENTERPRISE PILLARS: GS1 DIGITAL LINK, EU DPP, EPCIS 2.0, FORENSICS & PACKAGING
# ==============================================================================

@app.get("/01/{gtin}/21/{serial}")
def resolve_gs1_digital_link(
    gtin: str,
    serial: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """GS1 Digital Link (Sunrise 2027) Resolver conforming to GS1 URI Syntax Standard v1.7.0.
    
    Supports dynamic content negotiation:
    - HTML: Consumer mobile passport & authentication view
    - JSON / JSON-LD: GS1 Digital Link compliant linkset
    - SVG: High-density packaging vector label
    """
    gtin14 = pad_gtin14(gtin)
    product = db.scalar(
        select(Product).where(
            Product.gtin == gtin14,
            Product.serial_number == serial,
        )
    )
    if not product:
        # Fallback by serial number or full product_id
        product = db.scalar(select(Product).where(Product.product_id == serial))
        if not product:
            product = db.scalar(select(Product).where(Product.serial_number == serial))

    if not product:
        raise HTTPException(404, detail="Product not found for the specified GS1 GTIN and Serial")

    mfr = db.get(Manufacturer, product.manufacturer_id)
    accept = request.headers.get("accept", "").lower()

    # 1. Industrial SVG Vector Label negotiation
    if "image/svg+xml" in accept:
        svg_content = generate_single_label_svg(
            product={
                "product_name": product.product_name,
                "product_code": product.product_code,
                "manufacturer": mfr.name if mfr else "OPAP Manufacturer",
                "gtin": product.gtin or gtin14,
                "batch_id": product.batch_id,
                "serial_number": product.serial_number,
                "product_id": product.product_id,
                "expiry_date": product.expiry_date.isoformat() if product.expiry_date else None,
            },
            qr_uri=f"{get_settings().public_base_url}/01/{product.gtin or gtin14}/21/{product.serial_number}",
        )
        return Response(content=svg_content, media_type="image/svg+xml")

    # 2. Web browser HTML redirect
    if "text/html" in accept and not ("application/json" in accept or "application/ld+json" in accept):
        return RedirectResponse(
            url=f"/ui?product_id={product.product_id}&gtin={gtin14}&serial={serial}"
        )

    # 3. GS1 Digital Link JSON-LD Linkset Specification
    base = get_settings().public_base_url
    dpp_url = f"{base}/v1/products/{product.product_id}/dpp"
    verify_url = f"{base}/v1/verify/{product.product_id}"
    custody_url = f"{base}/v1/products/{product.product_id}/custody"
    label_url = f"{base}/v1/products/{product.product_id}/label.svg"

    return {
        "@context": "https://ref.gs1.org/standards/digital-link/context.jsonld",
        "gtin": product.gtin or gtin14,
        "serial_number": product.serial_number,
        "batch_id": product.batch_id,
        "expiry_date": product.expiry_date.isoformat() if product.expiry_date else None,
        "product_id": product.product_id,
        "product_name": product.product_name,
        "manufacturer": mfr.name if mfr else "Unknown",
        "status": product.status.value,
        "linkset": [
            {
                "href": dpp_url,
                "title": "EU Ecodesign Digital Product Passport (DPP)",
                "type": "application/json",
                "rel": "gs1:dpp",
            },
            {
                "href": verify_url,
                "title": "OPAP Consumer Authentication & One-Time Verification",
                "type": "text/html",
                "rel": "gs1:verificationService",
            },
            {
                "href": custody_url,
                "title": "GS1 EPCIS 2.0 Custody Traceability",
                "type": "application/ld+json",
                "rel": "gs1:epcis",
            },
            {
                "href": label_url,
                "title": "Industrial Vector Packaging Label",
                "type": "image/svg+xml",
                "rel": "gs1:label",
            },
        ],
    }


@app.get("/v1/products/{product_id}/dpp", response_model=DPPResponse)
def get_product_dpp(product_id: str, db: Session = Depends(get_db)):
    """EU ESPR Digital Product Passport (DPP) compliance endpoint (Regulation EU 2024/1781)."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    mfr = db.get(Manufacturer, product.manufacturer_id)
    passport = product.passport

    import hashlib
    from .crypto import canonical_bytes
    digest = hashlib.sha256(canonical_bytes(product.canonical_payload)).hexdigest()

    # Verify Ed25519 signature
    mfr_key = db.scalar(
        select(ManufacturerKey).where(
            ManufacturerKey.key_id == product.key_id,
            ManufacturerKey.manufacturer_id == product.manufacturer_id,
        )
    )
    is_valid_sig = False
    if mfr_key:
        try:
            is_valid_sig = verify_signature(
                mfr_key.public_key,
                product.canonical_payload,
                product.signature,
            )
        except Exception:
            is_valid_sig = False

    custody_count = len(product.custody_events) if product.custody_events else 0
    gs1_uri = build_digital_link_uri(
        get_settings().public_base_url,
        product.gtin or "00000000000000",
        product.serial_number,
        product.batch_id,
        product.expiry_date.strftime("%y%m%d") if product.expiry_date else None,
    )

    return DPPResponse(
        product_id=product.product_id,
        product_name=product.product_name,
        product_code=product.product_code,
        gtin=product.gtin,
        manufacturer=mfr.name if mfr else "Unknown Manufacturer",
        manufacturer_id=product.manufacturer_id,
        batch_id=product.batch_id,
        serial_number=product.serial_number,
        issued_at=utc_iso(product.issued_at),
        status=product.status.value,
        materials_composition=passport.materials_composition if passport else {"bio_based_polymer": 75.0, "recycled_core": 25.0},
        carbon_footprint_kg=passport.carbon_footprint_kg if passport else 1.25,
        recycled_content_pct=passport.recycled_content_pct if passport else 25.0,
        repairability_score=passport.repairability_score if passport else 8.5,
        circularity_status=passport.circularity_status if passport else "RECYCLABLE",
        compliance_certs=passport.compliance_certs if passport else ["EU_ESPR_2024", "ISO_14040"],
        gs1_digital_link_uri=gs1_uri,
        ed25519_verified=is_valid_sig,
        digest_sha256=digest,
        custody_events_count=custody_count,
    )


@app.post("/v1/products/{product_id}/custody", response_model=CustodyEventResponse, dependencies=[Depends(require_api_key)])
def record_custody_event(product_id: str, body: CustodyEventCreate, db: Session = Depends(get_db)):
    """Appends an immutable GS1 EPCIS 2.0 custody track-and-trace event."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    ev = add_custody_event(
        db=db,
        product_id=product_id,
        business_step=body.business_step,
        disposition=body.disposition,
        location_name=body.location_name,
        custodian_id=body.custodian_id,
        custodian_name=body.custodian_name,
        location_gln=body.location_gln,
        geo_lat=body.geo_lat,
        geo_lon=body.geo_lon,
        notes=body.notes,
        metadata=body.metadata,
    )
    db.commit()
    return CustodyEventResponse(
        event_id=ev.event_id,
        product_id=ev.product_id,
        business_step=ev.business_step.value,
        disposition=ev.disposition.value,
        location_gln=ev.location_gln,
        location_name=ev.location_name,
        geo_lat=ev.geo_lat,
        geo_lon=ev.geo_lon,
        custodian_id=ev.custodian_id,
        custodian_name=ev.custodian_name,
        notes=ev.notes,
        occurred_at=utc_iso(ev.occurred_at),
        metadata=ev.metadata_json,
    )


@app.get("/v1/products/{product_id}/custody")
def get_custody_history(product_id: str, format: str = "json", db: Session = Depends(get_db)):
    """Fetches the complete supply chain custody chain. Supports standard EPCIS 2.0 JSON-LD."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    events = db.scalars(
        select(CustodyEvent)
        .where(CustodyEvent.product_id == product_id)
        .order_by(CustodyEvent.occurred_at.asc())
    ).all()

    if format.lower() in ("epcis", "epcis2", "json-ld"):
        return export_epcis2_document(product, list(events))

    return {
        "product_id": product_id,
        "count": len(events),
        "events": [
            {
                "event_id": ev.event_id,
                "business_step": ev.business_step.value,
                "disposition": ev.disposition.value,
                "location_gln": ev.location_gln,
                "location_name": ev.location_name,
                "geo_lat": ev.geo_lat,
                "geo_lon": ev.geo_lon,
                "custodian_id": ev.custodian_id,
                "custodian_name": ev.custodian_name,
                "notes": ev.notes,
                "occurred_at": utc_iso(ev.occurred_at),
                "metadata": ev.metadata_json,
            }
            for ev in events
        ],
    }


@app.post("/v1/epcis/capture", dependencies=[Depends(require_api_key)])
def capture_epcis_events(body: dict[str, Any], db: Session = Depends(get_db)):
    """Bulk captures and ingests a standard GS1 EPCIS 2.0 JSON-LD event document."""
    try:
        result = ingest_epcis2_document(db=db, epcis_doc=body)
        db.commit()
        return result
    except ValueError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"EPCIS 2.0 capture ingestion failed: {e}")


@app.get("/v1/products/{product_id}/forensics", response_model=ForensicThreatReport)
def get_product_forensics(product_id: str, db: Session = Depends(get_db)):
    """Generates an autonomous AI counterfeit forensic threat report for a product."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")

    mfr = db.get(Manufacturer, product.manufacturer_id)
    events = db.scalars(
        select(VerificationEvent)
        .where(VerificationEvent.product_id == product_id)
        .order_by(VerificationEvent.occurred_at.asc())
    ).all()

    lanes_db = db.scalars(select(VerificationLane).where(VerificationLane.product_id == product_id)).all()
    lanes = {l.lane.value: l.status.value for l in lanes_db}

    event_dicts = [
        {
            "event_id": ev.event_id,
            "lane": ev.lane.value,
            "result": ev.result,
            "occurred_at": ev.occurred_at,
            "geo_lat": ev.geo_lat,
            "geo_lon": ev.geo_lon,
            "city": ev.city,
            "risk_flag": ev.risk_flag,
        }
        for ev in events
    ]

    report = ForensicEngine.analyze_product_events(
        product={
            "product_id": product.product_id,
            "product_name": product.product_name,
            "product_code": product.product_code,
            "manufacturer": mfr.name if mfr else "Unknown",
            "batch_id": product.batch_id,
            "status": product.status.value,
        },
        events=event_dicts,
        lanes=lanes,
    )

    return ForensicThreatReport(**report)


@app.get("/v1/forensics/threats")
def list_global_threats(limit: int = 50, db: Session = Depends(get_db)):
    """Global AI surveillance feed: aggregates active replay attacks and impossible travel anomalies."""
    threat_events = db.scalars(
        select(VerificationEvent)
        .where(VerificationEvent.risk_flag.isnot(None))
        .order_by(VerificationEvent.occurred_at.desc())
        .limit(limit)
    ).all()

    return {
        "count": len(threat_events),
        "threats": [
            {
                "event_id": ev.event_id,
                "product_id": ev.product_id,
                "risk_flag": ev.risk_flag,
                "lane": ev.lane.value,
                "result": ev.result,
                "city": ev.city,
                "geo_lat": ev.geo_lat,
                "geo_lon": ev.geo_lon,
                "occurred_at": utc_iso(ev.occurred_at),
                "metadata": ev.metadata_json,
            }
            for ev in threat_events
        ],
    }


@app.get("/v1/products/{product_id}/label.svg")
def get_packaging_label_svg(
    product_id: str,
    width_mm: int = 100,
    height_mm: int = 50,
    db: Session = Depends(get_db),
):
    """Generates an industrial vector packaging label (SVG) for factory application."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    mfr = db.get(Manufacturer, product.manufacturer_id)

    qr_uri = build_digital_link_uri(
        get_settings().public_base_url,
        product.gtin or "00000000000000",
        product.serial_number,
        product.batch_id,
        product.expiry_date.strftime("%y%m%d") if product.expiry_date else None,
    )

    svg_content = generate_single_label_svg(
        product={
            "product_id": product.product_id,
            "product_name": product.product_name,
            "product_code": product.product_code,
            "manufacturer": mfr.name if mfr else "OPAP Manufacturer",
            "gtin": product.gtin or "N/A",
            "batch_id": product.batch_id,
            "serial_number": product.serial_number,
            "expiry_date": product.expiry_date.isoformat() if product.expiry_date else None,
        },
        qr_uri=qr_uri,
        width_mm=width_mm,
        height_mm=height_mm,
    )
    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/v1/manufacturers/{manufacturer_id}/labels/sheet", response_class=HTMLResponse)
def get_manufacturer_label_sheet(
    manufacturer_id: str,
    batch_id: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Generates an industrial multi-up sticker print sheet for mass packaging."""
    mfr = db.get(Manufacturer, manufacturer_id)
    if not mfr:
        raise HTTPException(404, "Manufacturer not found")

    query = select(Product).where(Product.manufacturer_id == manufacturer_id)
    if batch_id:
        query = query.where(Product.batch_id == batch_id)
    products_db = db.scalars(query.limit(limit)).all()

    product_dicts = [
        {
            "product_id": p.product_id,
            "product_name": p.product_name,
            "product_code": p.product_code,
            "manufacturer": mfr.name,
            "gtin": p.gtin or "N/A",
            "batch_id": p.batch_id,
            "serial_number": p.serial_number,
            "expiry_date": p.expiry_date.isoformat() if p.expiry_date else None,
        }
        for p in products_db
    ]

    html_sheet = generate_batch_label_sheet_html(
        products=product_dicts,
        base_url=get_settings().public_base_url,
    )
    return HTMLResponse(content=html_sheet)

