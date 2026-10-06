"""Industrial packaging label generator & batch print-sheet exporter for OPAP.

Generates compliant, print-ready SVG labels and multi-up sticker grids for
Zebra ZPL, Avery Dennison, and high-speed factory automated label applicators.
"""

from __future__ import annotations

from io import BytesIO
from typing import Any
import qrcode
import qrcode.image.svg


def generate_single_label_svg(
    product: dict[str, Any],
    qr_uri: str,
    width_mm: int = 100,
    height_mm: int = 50,
) -> str:
    """Generates an industrial single-unit vector packaging label in SVG format."""
    # Generate QR code SVG as XML string
    img = qrcode.make(qr_uri, image_factory=qrcode.image.svg.SvgImage)
    out = BytesIO()
    img.save(out)
    qr_svg_content = out.getvalue().decode("utf-8")
    
    # Strip <?xml ...?> from QR SVG to embed directly
    if "<svg" in qr_svg_content:
        qr_inner = qr_svg_content[qr_svg_content.find("<svg"):qr_svg_content.rfind("</svg>") + 6]
    else:
        qr_inner = qr_svg_content

    p_name = product.get("product_name", "AUTHENTIC PRODUCT")[:35]
    p_code = product.get("product_code", "PROD-001")
    mfr = product.get("manufacturer", "OPAP CERTIFIED")[:30]
    gtin = product.get("gtin", "N/A")
    batch = product.get("batch_id", "N/A")
    serial = product.get("serial_number", "N/A")
    pid = product.get("product_id", "")
    exp = product.get("expiry_date", "2028-12-31")[:10] if product.get("expiry_date") else "SEE PACKAGING"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200" width="{width_mm}mm" height="{height_mm}mm" style="background:#ffffff; font-family: ui-monospace, Menlo, Consolas, sans-serif;">
  <!-- Border & Cut Guide -->
  <rect x="2" y="2" width="396" height="196" rx="8" fill="#ffffff" stroke="#0f172a" stroke-width="3"/>
  <rect x="8" y="8" width="384" height="34" rx="4" fill="#0f172a"/>
  
  <!-- Header / Manufacturer -->
  <text x="18" y="30" fill="#ffffff" font-size="14" font-weight="bold" letter-spacing="1">{mfr.upper()}</text>
  <text x="382" y="30" fill="#38bdf8" font-size="11" font-weight="bold" text-anchor="end">OPAP // ED25519</text>

  <!-- Left: QR Code Block -->
  <g transform="translate(14, 52) scale(0.38)">
    {qr_inner}
  </g>
  <text x="75" y="185" fill="#64748b" font-size="9" text-anchor="middle" font-weight="bold">SCAN TO AUTHENTICATE</text>

  <!-- Right: Technical Serialization & GS1 Block -->
  <!-- Product Name -->
  <text x="150" y="65" fill="#0f172a" font-size="15" font-weight="800">{p_name}</text>
  <text x="150" y="80" fill="#475569" font-size="10">CODE: <tspan font-weight="bold" fill="#0f172a">{p_code}</tspan></text>

  <!-- Key Identification Grid -->
  <line x1="150" y1="88" x2="385" y2="88" stroke="#cbd5e1" stroke-width="1"/>

  <text x="150" y="105" fill="#64748b" font-size="10">GTIN (01):</text>
  <text x="220" y="105" fill="#0f172a" font-size="11" font-weight="bold">{gtin}</text>

  <text x="150" y="123" fill="#64748b" font-size="10">LOT / BATCH (10):</text>
  <text x="255" y="123" fill="#0f172a" font-size="11" font-weight="bold">{batch}</text>

  <text x="150" y="141" fill="#64748b" font-size="10">SERIAL NO (21):</text>
  <text x="240" y="141" fill="#0284c7" font-size="11" font-weight="bold">{serial}</text>

  <text x="150" y="159" fill="#64748b" font-size="10">EXPIRY DATE (17):</text>
  <text x="255" y="159" fill="#0f172a" font-size="11" font-weight="bold">{exp}</text>

  <!-- Footer Security Hash -->
  <rect x="150" y="168" width="235" height="20" rx="3" fill="#f1f5f9"/>
  <text x="155" y="182" fill="#475569" font-size="8.5">ID: {pid[:32]}...</text>
</svg>"""


def generate_batch_label_sheet_html(
    products: list[dict[str, Any]],
    base_url: str,
) -> str:
    """Generates a complete, printable HTML sticker sheet (e.g. 2 columns x N rows) for factory batches."""
    labels_html = []
    for p in products:
        uri = f"{base_url}/v1/verify/{p['product_id']}"
        svg_content = generate_single_label_svg(p, uri, width_mm=95, height_mm=48)
        labels_html.append(f"""
        <div class="label-item">
          {svg_content}
        </div>
        """)

    all_labels = "\n".join(labels_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>OPAP Industrial Batch Label Sheet</title>
  <style>
    @page {{
      size: A4;
      margin: 10mm;
    }}
    body {{
      font-family: system-ui, -apple-system, sans-serif;
      background: #f8fafc;
      margin: 0;
      padding: 20px;
    }}
    .print-bar {{
      max-width: 900px;
      margin: 0 auto 20px auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #0f172a;
      color: #fff;
      padding: 12px 20px;
      border-radius: 8px;
    }}
    .print-btn {{
      background: #38bdf8;
      color: #0f172a;
      border: none;
      padding: 8px 16px;
      font-weight: bold;
      border-radius: 6px;
      cursor: pointer;
    }}
    .sheet-grid {{
      max-width: 900px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 15px;
    }}
    .label-item {{
      background: #fff;
      display: flex;
      justify-content: center;
      align-items: center;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    @media print {{
      body {{ background: transparent; padding: 0; }}
      .print-bar {{ display: none; }}
      .sheet-grid {{ gap: 5mm; }}
    }}
  </style>
</head>
<body>
  <div class="print-bar">
    <div>
      <strong>OPAP Production Packaging Labels ({len(products)} units)</strong>
      <div style="font-size: 12px; color: #94a3b8;">Formatted for Standard Industrial Roll &amp; Sheet Printers</div>
    </div>
    <button class="print-btn" onclick="window.print()">Print Labels / PDF</button>
  </div>
  <div class="sheet-grid">
    {all_labels}
  </div>
</body>
</html>"""
