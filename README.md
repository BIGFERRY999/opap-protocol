# OPAP Technical Protocol v0.1

Runnable reference backend and interactive web client for the Open Product Authentication Protocol (OPAP) v0.1.

The system provides manufacturer registration, per-item batch issuance, Ed25519 digital signatures, QR verification URIs/SVGs, independent one-time merchant and consumer lanes, batch verification, pluggable HSM/KMS cryptographic signing, a mobile-ready Web Scanner interface, revocation, and event/audit records.

---

## Key Features & Extensions

### 1. Web Scanner & Verification UI (`GET /` or `/scanner`)
- **Native Barcode Detector**: High-speed hardware-accelerated QR scanning using the browser `BarcodeDetector` API.
- **Photo Upload & Clipboard Paste**: Decodes QR codes from uploaded photos, file drops, or pasted screenshots.
- **Dual-Lane Verification**: Instant toggle between Consumer Lane (shoppers) and Merchant Lane (with retailer/merchant IDs).
- **Interactive Sandbox Lab**: One-click demo panel to register a test manufacturer, issue signed products, and test single & replay verifications live in the browser.

### 2. Batch Verification Engine (`POST /v1/verify/batch`)
- Verify up to 500 items in a single atomic transaction.
- Designed for distribution centers, warehouse receiving, and merchant carton checks.
- Returns comprehensive batch metrics (`total`, `authentic`, `already_verified`, `revoked`, `invalid`) and automated threat detection (`ALL_AUTHENTIC`, `COUNTERFEIT_DETECTED`, `REVOKED_ITEMS_PRESENT`, `REPLAY_DETECTED`).

### 3. Pluggable Signer Architecture (HSM / KMS / File / Env)
The cryptographic signer in `app/signer.py` provides an extensible `SignerProvider` interface:
- **`env`** (`LocalEnvSigner`): In-memory 32-byte Ed25519 key (for development/testing).
- **`file`** (`FileKeySigner`): Protected key file path (Raw 32-byte binary, Hex string, or PKCS#8 PEM).
- **`aws_kms`** (`AwsKmsSigner`): Asymmetric signing via AWS KMS Ed25519 keys (with simulated fallback).
- **`gcp_kms`** (`GcpKmsSigner`): Google Cloud KMS asymmetric signing adapter.
- **`pkcs11`** (`Pkcs11HsmSigner`): Hardware Security Module driver integration (SoftHSM, YubiHSM, CloudHSM).

Inspect active signer status via `GET /v1/signer`.

---

## Trust and Key Handling

The signed canonical record is UTF-8 JSON serialized with sorted keys, compact separators, Unicode preserved, and non-finite numbers rejected. Ed25519 signs those exact bytes; SHA-256 is exposed as the record digest. The verifier checks the registered active manufacturer key and signature before state changes. A lane is consumed using one conditional SQL `UPDATE ... WHERE status='UNUSED'`, so concurrent requests can only transition one row successfully.

The QR URL is a locator, not proof. Its URI is `https://verify.example.org/v1/verify/{product_id}` and it can be fetched as SVG at `/v1/products/{product_id}/qr.svg`.

---

## Quick Start

### Option A: Local Python with `uv`

```sh
# Run tests
uv run --python 3.12 --with-requirements requirements.txt python -m pytest

# Start development server
uv run --python 3.12 --with-requirements requirements.txt uvicorn app.main:app --reload --port 8000
```
Open **`http://localhost:8000`** to access the Web Scanner & Sandbox, or `http://localhost:8000/docs` for the interactive OpenAPI documentation.

### Option B: Docker Compose

```sh
docker compose up --build
```

---

## API Outline

All management endpoints require `X-API-Key`. Verification and Scanner UI are public by default.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` or `/scanner` | Responsive Web Scanner, Batch Verifier & Demo UI |
| `GET` | `/health` | Service health check |
| `GET` | `/v1/signer` | Active cryptographic signer status & public key |
| `POST` | `/v1/manufacturers` | Register manufacturer and its Ed25519 public key |
| `POST` | `/v1/manufacturers/{id}/products` | Issue 1–5000 uniquely identified signed product records |
| `POST` | `/v1/verify` | Verify and consume single merchant or consumer lane |
| `POST` | `/v1/verify/batch` | Batch verify multiple product IDs in one request |
| `GET` | `/v1/verify/{product_id}` | QR landing metadata (HTML for browsers, JSON for APIs) |
| `GET` | `/v1/products/{product_id}/qr.svg` | Generated QR code SVG |
| `GET` | `/v1/products/{product_id}` | Signed public record and SHA-256 digest |
| `POST` | `/v1/products/{id}/revoke` | Revoke product |
| `POST` | `/v1/manufacturers/{id}/revoke` | Revoke manufacturer and its keys |

---

## Sample Requests

### 1. Batch Verification

```sh
curl -X POST http://localhost:8000/v1/verify/batch \
  -H 'Content-Type: application/json' \
  -d '{
    "default_lane": "CONSUMER",
    "items": [
      {"product_id": "OPAP-NG-MFR1-ABC12345"},
      {"product_id": "OPAP-NG-MFR1-XYZ67890"}
    ]
  }'
```

Response:
```json
{
  "summary": {
    "total": 2,
    "authentic": 2,
    "already_verified": 0,
    "invalid": 0,
    "revoked": 0,
    "status": "ALL_AUTHENTIC"
  },
  "results": [...]
}
```

---

## Tests

Execute the complete test suite:
```sh
uv run --python 3.12 --with-requirements requirements.txt python -m pytest
```

Tests cover:
- Protocol canonicalization & tamper detection
- Dual independent lanes & replay detection
- Batch verification with mixed states (authentic, replay, revoked, invalid)
- Pluggable Signer providers (Env, File, AWS KMS, GCP KMS, PKCS#11 HSM)
- Content negotiation (HTML vs JSON) for web scanners
- Product and manufacturer revocation workflows
