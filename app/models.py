import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, JSON, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


def now_utc():
    return datetime.now(timezone.utc)


class Status(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class Lane(str, enum.Enum):
    MERCHANT = "MERCHANT"
    CONSUMER = "CONSUMER"


class LaneStatus(str, enum.Enum):
    UNUSED = "UNUSED"
    VERIFIED = "VERIFIED"


class Manufacturer(Base):
    __tablename__ = "manufacturers"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    keys: Mapped[list["ManufacturerKey"]] = relationship(back_populates="manufacturer")


class ManufacturerKey(Base):
    __tablename__ = "manufacturer_keys"
    __table_args__ = (UniqueConstraint("manufacturer_id", "key_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    manufacturer_id: Mapped[str] = mapped_column(ForeignKey("manufacturers.id"), index=True)
    key_id: Mapped[str] = mapped_column(String(80), nullable=False)
    public_key: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.ACTIVE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    manufacturer: Mapped[Manufacturer] = relationship(back_populates="keys")


class Product(Base):
    __tablename__ = "products"
    product_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    manufacturer_id: Mapped[str] = mapped_column(ForeignKey("manufacturers.id"), index=True)
    key_id: Mapped[str] = mapped_column(String(80), nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), nullable=False)
    product_name: Mapped[str] = mapped_column(String(300), nullable=False)
    batch_id: Mapped[str] = mapped_column(String(120), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(80), nullable=False)
    gtin: Mapped[str | None] = mapped_column(String(14), index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.ACTIVE, nullable=False)
    canonical_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature: Mapped[bytes] = mapped_column(LargeBinary(64), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    passport: Mapped["ProductPassport | None"] = relationship(back_populates="product", uselist=False)
    custody_events: Mapped[list["CustodyEvent"]] = relationship(back_populates="product", order_by="CustodyEvent.occurred_at")


class VerificationLane(Base):
    __tablename__ = "verification_lanes"
    __table_args__ = (UniqueConstraint("product_id", "lane"), Index("ix_lane_state", "product_id", "lane", "status"))
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    lane: Mapped[Lane] = mapped_column(Enum(Lane), nullable=False)
    status: Mapped[LaneStatus] = mapped_column(Enum(LaneStatus), default=LaneStatus.UNUSED, nullable=False)
    merchant_id: Mapped[str | None] = mapped_column(String(128))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VerificationEvent(Base):
    __tablename__ = "verification_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    product_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    lane: Mapped[Lane] = mapped_column(Enum(Lane), nullable=False)
    result: Mapped[str] = mapped_column(String(40), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    risk_flag: Mapped[str | None] = mapped_column(String(80))
    geo_lat: Mapped[float | None] = mapped_column()
    geo_lon: Mapped[float | None] = mapped_column()
    city: Mapped[str | None] = mapped_column(String(120))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)


class CustodyBusinessStep(str, enum.Enum):
    COMMISSIONING = "COMMISSIONING"
    SHIPPING = "SHIPPING"
    CUSTOMS_CLEARANCE = "CUSTOMS_CLEARANCE"
    RECEIVING = "RECEIVING"
    HOLDING = "HOLDING"
    RETAIL_SELLING = "RETAIL_SELLING"
    INSPECTING = "INSPECTING"


class CustodyDisposition(str, enum.Enum):
    IN_TRANSIT = "IN_TRANSIT"
    ACTIVE = "ACTIVE"
    HELD = "HELD"
    IN_PROGRESS = "IN_PROGRESS"
    RECALLED = "RECALLED"
    DESTROYED = "DESTROYED"


class CustodyEvent(Base):
    """GS1 EPCIS 2.0 compliant supply chain custody & track-and-trace event."""
    __tablename__ = "custody_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id", ondelete="CASCADE"), index=True, nullable=False)
    business_step: Mapped[CustodyBusinessStep] = mapped_column(Enum(CustodyBusinessStep), nullable=False)
    disposition: Mapped[CustodyDisposition] = mapped_column(Enum(CustodyDisposition), default=CustodyDisposition.ACTIVE, nullable=False)
    location_gln: Mapped[str | None] = mapped_column(String(64))
    location_name: Mapped[str] = mapped_column(String(200), nullable=False)
    geo_lat: Mapped[float | None] = mapped_column()
    geo_lon: Mapped[float | None] = mapped_column()
    custodian_id: Mapped[str] = mapped_column(String(128), nullable=False)
    custodian_name: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    product: Mapped[Product] = relationship(back_populates="custody_events")


class ProductPassport(Base):
    """EU ESPR Digital Product Passport (DPP) sustainability & provenance model."""
    __tablename__ = "product_passports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.product_id", ondelete="CASCADE"), unique=True, nullable=False)
    materials_composition: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    carbon_footprint_kg: Mapped[float] = mapped_column(default=0.0, nullable=False)
    recycled_content_pct: Mapped[float] = mapped_column(default=0.0, nullable=False)
    repairability_score: Mapped[float] = mapped_column(default=8.5, nullable=False)
    circularity_status: Mapped[str] = mapped_column(String(100), default="RECYCLABLE", nullable=False)
    compliance_certs: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    product: Mapped[Product] = relationship(back_populates="passport")


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    subject: Mapped[str] = mapped_column(String(160), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

