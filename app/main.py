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
    Lane,
    LaneStatus,
    Manufacturer,
    ManufacturerKey,
    Product,
    Status,
    VerificationEvent,
    VerificationLane,
)
from .schemas import (
    BatchSummary,
    BatchVerifyRequest,
    BatchVerifyResponse,
    BatchVerifyResultItem,
    ManufacturerCreate,
    ProductIssue,
    RevokeRequest,
    SignerStatusResponse,
    VerifyRequest,
)
from .signer import SignerConfigError, SignerError, get_signer
from .ui import get_scanner_html


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
            "issued_at": utc_iso(issued),
        }

        try:
            signature = signer.sign(payload)
        except SignerError as e:
            raise HTTPException(503, f"Cryptographic signing failure: {e}")

        db.add(
            Product(
                product_id=pid,
                manufacturer_id=manufacturer_id,
                key_id=key.key_id,
                product_code=body.product_code,
                product_name=body.product_name,
                batch_id=body.batch_id,
                serial_number=serial,
                issued_at=issued,
                canonical_payload=payload,
                signature=signature,
            )
        )
        db.add_all([
            VerificationLane(product_id=pid, lane=Lane.MERCHANT),
            VerificationLane(product_id=pid, lane=Lane.CONSUMER),
        ])
        uri = f"{get_settings().public_base_url}/v1/verify/{pid}"
        products.append({
            "product_id": pid,
            "serial_number": serial,
            "payload": payload,
            "key_id": key.key_id,
            "signature_b64url": b64url(signature),
            "qr_uri": uri,
        })

    audit(db, manufacturer_id, "PRODUCTS_ISSUED", body.batch_id, {"quantity": body.quantity})
    db.commit()
    return {"count": len(products), "products": products}


# --- Verification Core ---

def verify_one(db: Session, req: VerifyRequest, commit: bool = True) -> dict:
    lane = Lane(req.lane.value)
    product = db.get(Product, req.product_id)
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

    ev = VerificationEvent(product_id=req.product_id, lane=lane, result=result)
    db.add(ev)
    if commit:
        db.commit()

    mfr = db.get(Manufacturer, product.manufacturer_id) if product else None
    product_info = None if product is None else {
        "product_id": product.product_id,
        "name": product.product_name,
        "product_code": product.product_code,
        "manufacturer_id": product.manufacturer_id,
        "manufacturer": mfr.name if mfr else None,
        "batch": product.batch_id,
    }
    return {
        "result": result,
        "product": product_info,
        "verification": {
            "lane": lane.value,
            "status": "VERIFIED" if result == "AUTHENTIC" else ("ALREADY_VERIFIED" if result == "ALREADY_VERIFIED" else None),
        },
        "event_id": ev.event_id,
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
