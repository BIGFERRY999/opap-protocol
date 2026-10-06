-- OPAP Protocol Enterprise Reference DDL (PostgreSQL 15+).
-- SQLAlchemy models in app/models.py are authoritative.

-- Enumerations
CREATE TYPE status AS ENUM ('ACTIVE', 'REVOKED');
CREATE TYPE lane AS ENUM ('MERCHANT', 'CONSUMER');
CREATE TYPE lane_status AS ENUM ('UNUSED', 'VERIFIED');
CREATE TYPE custody_step AS ENUM (
  'COMMISSIONING', 'SHIPPING', 'CUSTOMS_CLEARANCE',
  'RECEIVING', 'HOLDING', 'RETAIL_SELLING', 'INSPECTING'
);
CREATE TYPE custody_disposition AS ENUM (
  'IN_TRANSIT', 'ACTIVE', 'HELD', 'IN_PROGRESS', 'RECALLED', 'DESTROYED'
);

-- Manufacturers & Keys
CREATE TABLE manufacturers (
  id varchar(64) PRIMARY KEY,
  name varchar(200) NOT NULL,
  status status NOT NULL DEFAULT 'ACTIVE',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE manufacturer_keys (
  id serial PRIMARY KEY,
  manufacturer_id varchar(64) NOT NULL REFERENCES manufacturers(id),
  key_id varchar(80) NOT NULL,
  public_key bytea NOT NULL CHECK (octet_length(public_key) = 32),
  status status NOT NULL DEFAULT 'ACTIVE',
  created_at timestamptz NOT NULL DEFAULT now(),
  revoked_at timestamptz,
  UNIQUE(manufacturer_id, key_id)
);

-- Serialized Products with GS1 GTIN & Timestamps
CREATE TABLE products (
  product_id varchar(128) PRIMARY KEY,
  manufacturer_id varchar(64) NOT NULL REFERENCES manufacturers(id),
  key_id varchar(80) NOT NULL,
  product_code varchar(100) NOT NULL,
  product_name varchar(300) NOT NULL,
  batch_id varchar(120) NOT NULL,
  serial_number varchar(80) NOT NULL,
  gtin varchar(14),
  issued_at timestamptz NOT NULL,
  expiry_date timestamptz,
  status status NOT NULL DEFAULT 'ACTIVE',
  canonical_payload jsonb NOT NULL,
  signature bytea NOT NULL CHECK (octet_length(signature) = 64),
  revoked_at timestamptz
);
CREATE INDEX ix_products_gtin ON products(gtin);
CREATE INDEX ix_products_batch ON products(batch_id);

-- Dual-Lane One-Time Verification State Machine
CREATE TABLE verification_lanes (
  id serial PRIMARY KEY,
  product_id varchar(128) NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  lane lane NOT NULL,
  status lane_status NOT NULL DEFAULT 'UNUSED',
  merchant_id varchar(128),
  verified_at timestamptz,
  UNIQUE(product_id, lane)
);
CREATE INDEX ix_lane_state ON verification_lanes(product_id, lane, status);

-- Verification Telemetry & Geo-Spatial AI Forensics
CREATE TABLE verification_events (
  id serial PRIMARY KEY,
  event_id uuid NOT NULL UNIQUE,
  product_id varchar(128) NOT NULL,
  lane lane NOT NULL,
  result varchar(40) NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  risk_flag varchar(80),
  geo_lat double precision,
  geo_lon double precision,
  city varchar(120),
  ip_address varchar(64),
  metadata jsonb NOT NULL DEFAULT '{}'
);
CREATE INDEX ix_verification_events_product_id ON verification_events(product_id);
CREATE INDEX ix_verification_events_risk_flag ON verification_events(risk_flag);

-- GS1 EPCIS 2.0 Multi-Hop Custody Chain
CREATE TABLE custody_events (
  id serial PRIMARY KEY,
  event_id uuid NOT NULL UNIQUE,
  product_id varchar(128) NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  business_step custody_step NOT NULL,
  disposition custody_disposition NOT NULL DEFAULT 'ACTIVE',
  location_gln varchar(64),
  location_name varchar(200) NOT NULL,
  geo_lat double precision,
  geo_lon double precision,
  custodian_id varchar(128) NOT NULL,
  custodian_name varchar(200) NOT NULL,
  notes text,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  metadata jsonb NOT NULL DEFAULT '{}'
);
CREATE INDEX ix_custody_events_product_id ON custody_events(product_id);

-- EU ESPR Digital Product Passport (DPP) Sustainability Registry
CREATE TABLE product_passports (
  id serial PRIMARY KEY,
  product_id varchar(128) NOT NULL UNIQUE REFERENCES products(product_id) ON DELETE CASCADE,
  materials_composition jsonb NOT NULL DEFAULT '{}',
  carbon_footprint_kg double precision NOT NULL DEFAULT 0.0,
  recycled_content_pct double precision NOT NULL DEFAULT 0.0,
  repairability_score double precision NOT NULL DEFAULT 8.5,
  circularity_status varchar(100) NOT NULL DEFAULT 'RECYCLABLE',
  compliance_certs jsonb NOT NULL DEFAULT '[]',
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Immutable Operational Audit Log
CREATE TABLE audit_events (
  id serial PRIMARY KEY,
  event_id uuid NOT NULL UNIQUE,
  actor varchar(128) NOT NULL,
  action varchar(80) NOT NULL,
  subject varchar(160) NOT NULL,
  occurred_at timestamptz NOT NULL DEFAULT now(),
  details jsonb NOT NULL DEFAULT '{}'
);
CREATE INDEX ix_audit_events_occurred_at ON audit_events(occurred_at);
