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
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[Status] = mapped_column(Enum(Status), default=Status.ACTIVE, nullable=False)
    canonical_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    signature: Mapped[bytes] = mapped_column(LargeBinary(64), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    subject: Mapped[str] = mapped_column(String(160), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
