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


class VerifyRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=128)
    lane: LaneName
    merchant_id: str | None = Field(default=None, max_length=128)


class RevokeRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class BatchVerifyItem(BaseModel):
    product_id: str = Field(min_length=1, max_length=128)
    lane: LaneName | None = None
    merchant_id: str | None = Field(default=None, max_length=128)


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
