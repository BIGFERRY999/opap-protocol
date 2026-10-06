from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class LaneName(str, Enum):
    merchant = "MERCHANT"
    consumer = "CONSUMER"


class ManufacturerCreate(BaseModel):
    manufacturer_id: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9._-]+$")
    name: str = Field(min_length=1, max_length=200)
    key_id: str = Field(min_length=1, max_length=80)
    public_key_b64: str


class ProductIssue(BaseModel):
    product_code: str = Field(min_length=1, max_length=100)
    product_name: str = Field(min_length=1, max_length=300)
    batch_id: str = Field(min_length=1, max_length=120)
    quantity: int = Field(ge=1, le=5000)
    issued_at: str | None = None
    gtin: str | None = Field(default=None, max_length=14, pattern=r"^\d{8,14}$")
    expiry_date: str | None = None
    # Optional DPP initialization
    materials_composition: dict[str, float] | None = None
    carbon_footprint_kg: float | None = None
    recycled_content_pct: float | None = None
    repairability_score: float | None = None
    circularity_status: str | None = None
    compliance_certs: list[str] | None = None


class VerifyRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=128)
    lane: LaneName
    merchant_id: str | None = Field(default=None, max_length=128)
    geo_lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    geo_lon: float | None = Field(default=None, ge=-180.0, le=180.0)
    city: str | None = Field(default=None, max_length=120)
    ip_address: str | None = Field(default=None, max_length=64)


class RevokeRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class BatchVerifyItem(BaseModel):
    product_id: str = Field(min_length=1, max_length=128)
    lane: LaneName | None = None
    merchant_id: str | None = Field(default=None, max_length=128)
    geo_lat: float | None = None
    geo_lon: float | None = None
    city: str | None = None


class BatchVerifyRequest(BaseModel):
    items: list[BatchVerifyItem] = Field(min_length=1, max_length=500)
    default_lane: LaneName = LaneName.consumer
    default_merchant_id: str | None = Field(default=None, max_length=128)


class BatchVerifyResultItem(BaseModel):
    product_id: str
    lane: LaneName
    result: str
    product: dict[str, Any] | None = None
    verification: dict[str, Any] | None = None
    event_id: str | None = None
    threat_analysis: dict[str, Any] | None = None


class BatchSummary(BaseModel):
    total: int
    authentic: int
    already_verified: int
    invalid: int
    revoked: int
    status: str


class BatchVerifyResponse(BaseModel):
    summary: BatchSummary
    results: list[BatchVerifyResultItem]


class SignerStatusResponse(BaseModel):
    provider: str
    public_key_b64: str
    public_key_bytes: int
    details: dict[str, Any] = Field(default_factory=dict)


# --- GS1 Digital Link & EPCIS 2.0 Schemas ---

class CustodyEventCreate(BaseModel):
    business_step: str = Field(default="RECEIVING", description="COMMISSIONING, SHIPPING, CUSTOMS_CLEARANCE, RECEIVING, HOLDING, RETAIL_SELLING")
    disposition: str = Field(default="ACTIVE", description="IN_TRANSIT, ACTIVE, HELD, RECALLED")
    location_gln: str | None = Field(default=None, max_length=64)
    location_name: str = Field(min_length=1, max_length=200)
    geo_lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    geo_lon: float | None = Field(default=None, ge=-180.0, le=180.0)
    custodian_id: str = Field(min_length=1, max_length=128)
    custodian_name: str = Field(min_length=1, max_length=200)
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustodyEventResponse(BaseModel):
    event_id: str
    product_id: str
    business_step: str
    disposition: str
    location_gln: str | None
    location_name: str
    geo_lat: float | None
    geo_lon: float | None
    custodian_id: str
    custodian_name: str
    notes: str | None
    occurred_at: str
    metadata: dict[str, Any]


class DPPResponse(BaseModel):
    product_id: str
    product_name: str
    product_code: str
    gtin: str | None
    manufacturer: str
    manufacturer_id: str
    batch_id: str
    serial_number: str
    issued_at: str
    status: str
    # Sustainability & Circularity
    materials_composition: dict[str, float]
    carbon_footprint_kg: float
    recycled_content_pct: float
    repairability_score: float
    circularity_status: str
    compliance_certs: list[str]
    # Digital Link & Cryptographic Seal
    gs1_digital_link_uri: str
    ed25519_verified: bool
    digest_sha256: str
    custody_events_count: int


class GS1ResolveResponse(BaseModel):
    gtin: str
    serial_number: str
    batch_id: str | None
    expiry_date: str | None
    product_id: str
    product_name: str
    manufacturer: str
    status: str
    dpp_url: str
    verify_url: str


class ForensicThreatReport(BaseModel):
    product_id: str
    risk_level: str  # NOMINAL, ELEVATED, CRITICAL
    total_scans: int
    consumer_status: str
    merchant_status: str
    geo_anomalies: list[dict[str, Any]]
    threat_indicators: list[str]
    ai_advisory: str

