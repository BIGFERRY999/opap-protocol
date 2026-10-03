-- PostgreSQL reference DDL. The SQLAlchemy models are authoritative for app startup.
CREATE TYPE status AS ENUM ('ACTIVE', 'REVOKED');
CREATE TYPE lane AS ENUM ('MERCHANT', 'CONSUMER');
CREATE TYPE lane_status AS ENUM ('UNUSED', 'VERIFIED');
CREATE TABLE manufacturers (
  id varchar(64) PRIMARY KEY, name varchar(200) NOT NULL,
  status status NOT NULL DEFAULT 'ACTIVE', created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE manufacturer_keys (
  id serial PRIMARY KEY, manufacturer_id varchar(64) NOT NULL REFERENCES manufacturers(id),
  key_id varchar(80) NOT NULL, public_key bytea NOT NULL CHECK (octet_length(public_key)=32),
  status status NOT NULL DEFAULT 'ACTIVE', created_at timestamptz NOT NULL DEFAULT now(), revoked_at timestamptz,
  UNIQUE(manufacturer_id,key_id)
);
CREATE TABLE products (
  product_id varchar(128) PRIMARY KEY, manufacturer_id varchar(64) NOT NULL REFERENCES manufacturers(id),
  key_id varchar(80) NOT NULL, product_code varchar(100) NOT NULL, product_name varchar(300) NOT NULL,
  batch_id varchar(120) NOT NULL, serial_number varchar(80) NOT NULL, issued_at timestamptz NOT NULL,
  status status NOT NULL DEFAULT 'ACTIVE', canonical_payload jsonb NOT NULL,
  signature bytea NOT NULL CHECK (octet_length(signature)=64), revoked_at timestamptz
);
CREATE TABLE verification_lanes (
  id serial PRIMARY KEY, product_id varchar(128) NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
  lane lane NOT NULL, status lane_status NOT NULL DEFAULT 'UNUSED', merchant_id varchar(128), verified_at timestamptz,
  UNIQUE(product_id,lane)
);
CREATE INDEX ix_lane_state ON verification_lanes(product_id,lane,status);
CREATE TABLE verification_events (
  id serial PRIMARY KEY, event_id uuid NOT NULL UNIQUE, product_id varchar(128) NOT NULL,
  lane lane NOT NULL, result varchar(40) NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(),
  risk_flag varchar(80), metadata jsonb NOT NULL DEFAULT '{}'
);
CREATE INDEX ix_verification_events_product_id ON verification_events(product_id);
CREATE TABLE audit_events (
  id serial PRIMARY KEY, event_id uuid NOT NULL UNIQUE, actor varchar(128) NOT NULL,
  action varchar(80) NOT NULL, subject varchar(160) NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now(), details jsonb NOT NULL DEFAULT '{}'
);
