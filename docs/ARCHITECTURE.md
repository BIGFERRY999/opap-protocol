# OPAP Architecture & Technical Specification

## 1. Architectural Overview

The Open Product Authentication Protocol (OPAP) is designed to operate as a high-throughput, low-latency trust layer connecting industrial packaging systems, supply chain logistics handlers, retail point-of-sale systems, and consumer smartphones.

```
+-----------------------------------------------------------------------------+
|                            OPAP Trust Layer                                 |
+-----------------------------------------------------------------------------+
|                                                                             |
|   +-----------------------+     +--------------------+     +------------+   |
|   |  Industrial Packaging |     |  GS1 Digital Link  |     |   EU DPP   |   |
|   |  Vector & Sheet Engine|     |  v1.7.0 Resolver   |     |  Registry  |   |
|   +-----------+-----------+     +---------+----------+     +-----+------+   |
|               |                           |                      |          |
|               +---------------------+     |     +----------------+          |
|                                     |     |     |                           |
|                                     v     v     v                           |
|                      +----------------------------------+                   |
|                      |   Dual-Lane State Machine        |                   |
|                      |  - MERCHANT: One-time Ingestion  |                   |
|                      |  - CONSUMER: One-time Scan       |                   |
|                      +----------------+-----------------+                   |
|                                       |                                     |
|                                       v                                     |
|                      +----------------------------------+                   |
|                      |  Autonomous AI Threat Engine     |                   |
|                      |  - Haversine Geo-Velocity        |                   |
|                      |  - Replay Attack Clustering      |                   |
|                      +----------------+-----------------+                   |
|                                       |                                     |
|                                       v                                     |
|                      +----------------------------------+                   |
|                      |   GS1 EPCIS 2.0 Custody Engine   |                   |
|                      |   Multi-Hop Supply Chain Graph   |                   |
|                      +----------------+-----------------+                   |
|                                       |                                     |
|                                       v                                     |
|                      +----------------------------------+                   |
|                      |  Hardware Security Layer (HSM)   |                   |
|                      |  Ed25519 Canonical JSON Signer   |                   |
|                      +----------------------------------+                   |
+-----------------------------------------------------------------------------+
```

---

## 2. Cryptographic Protocol Specification

### 2.1 Canonical Payload Serialization
To guarantee deterministic byte representation across diverse platforms, programming languages, and hardware architectures, OPAP mandates deterministic JSON canonicalization:
1. Keys sorted lexicographically in ascending ASCII order.
2. UTF-8 character encoding with Unicode escaped sequences strictly prohibited.
3. Minimal separators: `","` between array elements and object members; `":"` between object keys and values (no extraneous whitespace).
4. IEEE 754 non-finite numbers (`NaN`, `Infinity`, `-Infinity`) rejected.

### 2.2 Digital Signatures (Ed25519 / RFC 8032)
Every item issued possesses a unique canonical payload signed with the manufacturer's active Ed25519 private key:
$$\text{Signature} = \text{Ed25519Sign}(K_{\text{priv}}, \text{CanonicalBytes}(\text{Payload}))$$
$$\text{Digest} = \text{SHA256}(\text{CanonicalBytes}(\text{Payload}))$$

Verification verifies that:
$$\text{Ed25519Verify}(K_{\text{pub}}, \text{CanonicalBytes}(\text{Payload}), \text{Signature}) \equiv \text{True}$$

### 2.3 Dual-Lane One-Time Consumption
Counterfeiting syndicates typically duplicate legitimate QR codes thousands of times onto fake packaging. OPAP stops this using dual-lane state transitions:
1. **Merchant Lane (`MERCHANT`)**: Consumed upon wholesale or retail delivery acceptance.
2. **Consumer Lane (`CONSUMER`)**: Consumed by the end-user upon purchase or unboxing.

State transition is executed atomically at the database layer:
```sql
UPDATE verification_lanes
SET status = 'VERIFIED', verified_at = CURRENT_TIMESTAMP, merchant_id = :merchant_id
WHERE product_id = :product_id AND lane = :lane AND status = 'UNUSED';
```
If the row count is $1$, verification succeeds (`AUTHENTIC`). If $0$, a replay attack is triggered (`ALREADY_VERIFIED`).

---

## 3. GS1 Digital Link (Sunrise 2027) Implementation

Conforming to **GS1 Digital Link URI Syntax Standard v1.7.0**, OPAP endpoints parse and resolve Application Identifiers (AIs):
- `(01)` Global Trade Item Number (GTIN-14)
- `(21)` Serial Number
- `(10)` Batch / Lot Number
- `(17)` Expiration Date (YYMMDD)

### URI Resolution Syntax
`https://{domain}/01/{gtin}/21/{serial}?10={batch}&17={expiry}`

Dynamic HTTP content negotiation is performed based on the client's `Accept` header:
- `text/html` $\rightarrow$ Redirects to interactive consumer smartphone authentication and passport web UI.
- `application/ld+json` $\rightarrow$ Returns a GS1 compliant linkset object linking to DPP, verification, EPCIS custody, and vector packaging labels.
- `image/svg+xml` $\rightarrow$ Renders the industrial high-density vector packaging label directly.

---

## 4. EU ESPR Digital Product Passport (DPP) Compliance

Under Regulation (EU) 2024/1781 (Ecodesign for Sustainable Products Regulation), industrial and consumer products must provide circularity data:
- **Materials Breakdown**: Quantified percentages of bio-based, recycled, and synthetic components.
- **Carbon Footprint**: Cradle-to-gate carbon equivalent emissions ($\text{kg CO}_2\text{e}$).
- **Circularity Indicators**: Repairability score ($0.0 - 10.0$) and recyclability rating.
- **Compliance Badges**: Cryptographically anchored certifications (e.g. `EU_ESPR_2024`, `ISO_14040`).

---

## 5. GS1 EPCIS 2.0 Custody & Multi-Hop Audit Trail

The supply chain custody engine records transitions across standard EPCIS 2.0 business steps:
- `COMMISSIONING`: Factory production seal and initial cryptographic assignment.
- `SHIPPING`: Dispatch into cold chain or freight logistics.
- `CUSTOMS_CLEARANCE`: Border inspection and regulatory stamp.
- `RECEIVING`: Arrival at regional distribution centers.
- `HOLDING`: Quarantine or inventory holding.
- `RETAIL_SELLING`: Point-of-sale transfer to consumer.

Exported documents conform to the official `https://ref.gs1.org/standards/epcis/2.0.0/epcis-context.jsonld` standard.

---

## 6. Autonomous AI Counterfeit Intelligence & Threat Forensics

### 6.1 Impossible Travel Geo-Velocity Anomaly Detection
Calculates the great-circle distance between consecutive verification events $(E_1, E_2)$ using the Haversine formula:
$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$
$$d = 2 R \cdot \operatorname{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$

Velocity is calculated as:
$$v = \frac{d}{\Delta t} \times 3600\text{ km/h}$$

If $d > 50\text{ km}$ and $v > 900\text{ km/h}$ (exceeding commercial flight speeds), the event is flagged as an `IMPOSSIBLE_TRAVEL_VELOCITY` anomaly, indicating physical cloning across separate geographic regions.

### 6.2 Threat Scoring
Combines replay counts, geo-velocity anomalies, and manufacturer revocation states to produce a normalized risk rating ($0 - 100$) and natural language consumer warnings.
