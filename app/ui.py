"""Web Operations Center, Mobile Scanner, and Digital Product Passport UI for OPAP.

Zero external CDN dependencies, fully self-contained modern HTML5/CSS3/Vanilla JS
supporting:
- Native BarcodeDetector QR / GS1 scanning with camera viewfinder
- GS1 Digital Link (Sunrise 2027) syntax resolution & inspection
- EU ESPR Digital Product Passport (DPP) circularity & materials viewer
- GS1 EPCIS 2.0 multi-hop custody chain timeline & custody event logger
- Autonomous AI Counterfeit Intelligence & geo-velocity threat surveillance
- Industrial vector packaging label & batch sticker sheet generator
- Interactive Protocol Demo Sandbox with dual-lane consumption testing
"""

def get_scanner_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OPAP | Open Product Authentication & Digital Link Center</title>
  <style>
    :root {
      --bg: #070b14;
      --surface: #0f172a;
      --surface-elevated: #1e293b;
      --surface-hover: #334155;
      --border: #24344d;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --primary: #38bdf8;
      --primary-hover: #0ea5e9;
      --primary-bg: rgba(56, 189, 248, 0.12);
      --success: #22c55e;
      --success-bg: rgba(34, 197, 94, 0.15);
      --warning: #f59e0b;
      --warning-bg: rgba(245, 158, 11, 0.15);
      --danger: #ef4444;
      --danger-bg: rgba(239, 68, 68, 0.15);
      --radius: 12px;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      --font-sans: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: var(--font-sans);
      min-height: 100vh;
      line-height: 1.5;
      padding-bottom: 3rem;
    }
    header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 0.85rem 1.5rem;
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .brand-logo {
      width: 36px;
      height: 36px;
      border-radius: 8px;
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      color: #fff;
      font-size: 1.1rem;
    }
    .brand-title h1 {
      font-size: 1.15rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .brand-title p {
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .nav-tabs {
      display: flex;
      gap: 0.35rem;
      background: var(--surface-elevated);
      padding: 0.25rem;
      border-radius: 10px;
      overflow-x: auto;
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.45rem 0.85rem;
      border-radius: 7px;
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.15s ease;
    }
    .tab-btn.active {
      background: var(--primary);
      color: #041220;
    }
    .tab-btn:hover:not(.active) {
      color: var(--text);
    }
    .container {
      max-width: 980px;
      margin: 1.5rem auto;
      padding: 0 1rem;
    }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.5rem;
      margin-bottom: 1.5rem;
      box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
    }
    .card-header {
      margin-bottom: 1.25rem;
    }
    .card-header h2 {
      font-size: 1.25rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .card-header p {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }
    .lane-selector {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1.25rem;
    }
    .lane-pill {
      flex: 1;
      padding: 0.75rem;
      border: 2px solid var(--border);
      border-radius: 10px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.6rem;
      font-weight: 600;
      font-size: 0.9rem;
      transition: all 0.2s ease;
    }
    .lane-pill.selected {
      border-color: var(--primary);
      background: var(--primary-bg);
      color: var(--primary);
    }
    .input-group {
      margin-bottom: 1.25rem;
    }
    .input-group label {
      display: block;
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 0.4rem;
    }
    .input-field {
      width: 100%;
      background: var(--surface-elevated);
      border: 1px solid var(--border);
      border-radius: 8px;
      color: var(--text);
      padding: 0.75rem 1rem;
      font-size: 0.95rem;
      font-family: inherit;
      transition: border 0.15s ease;
    }
    .input-field:focus {
      outline: none;
      border-color: var(--primary);
    }
    textarea.input-field {
      resize: vertical;
      font-family: var(--font-mono);
      font-size: 0.85rem;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      padding: 0.75rem 1.4rem;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.15s ease;
    }
    .btn-primary {
      background: var(--primary);
      color: #041220;
    }
    .btn-primary:hover {
      background: var(--primary-hover);
    }
    .btn-secondary {
      background: var(--surface-elevated);
      color: var(--text);
      border: 1px solid var(--border);
    }
    .btn-secondary:hover {
      background: var(--surface-hover);
    }
    .btn-sm {
      padding: 0.4rem 0.8rem;
      font-size: 0.8rem;
    }
    .btn-danger {
      background: var(--danger);
      color: #fff;
    }
    /* Viewfinder */
    .viewfinder-wrapper {
      position: relative;
      width: 100%;
      height: 280px;
      background: #000;
      border-radius: 10px;
      overflow: hidden;
      margin-bottom: 1.25rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    #scanner-video {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .scanner-overlay {
      position: absolute;
      inset: 0;
      pointer-events: none;
      display: none;
      align-items: center;
      justify-content: center;
    }
    .scanner-box {
      width: 190px;
      height: 190px;
      border: 2px dashed var(--primary);
      border-radius: 16px;
      position: relative;
      box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.4);
    }
    .scanner-line {
      position: absolute;
      left: 0;
      right: 0;
      height: 2px;
      background: var(--primary);
      box-shadow: 0 0 10px var(--primary);
      animation: scan 2s linear infinite alternate;
    }
    @keyframes scan {
      0% { top: 5%; }
      100% { top: 95%; }
    }
    .scanner-controls {
      display: flex;
      gap: 0.75rem;
      margin-bottom: 1.25rem;
    }
    /* Status Badges */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.35rem 0.75rem;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.03em;
    }
    .badge-success { background: var(--success-bg); color: var(--success); }
    .badge-warning { background: var(--warning-bg); color: var(--warning); }
    .badge-danger { background: var(--danger-bg); color: var(--danger); }
    .badge-info { background: var(--primary-bg); color: var(--primary); }
    /* Result Box */
    .result-panel {
      border-radius: 10px;
      padding: 1.25rem;
      margin-top: 1.25rem;
      animation: fadeIn 0.3s ease;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .result-panel.authentic {
      background: rgba(34, 197, 94, 0.08);
      border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .result-panel.replay {
      background: rgba(245, 158, 11, 0.08);
      border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .result-panel.invalid {
      background: rgba(239, 68, 68, 0.08);
      border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .result-title {
      font-size: 1.25rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-bottom: 0.5rem;
    }
    .prop-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 0.75rem;
      margin-top: 1rem;
    }
    .prop-item {
      background: var(--surface-elevated);
      padding: 0.75rem;
      border-radius: 8px;
    }
    .prop-label {
      font-size: 0.72rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .prop-value {
      font-size: 0.9rem;
      font-weight: 600;
      margin-top: 0.2rem;
      word-break: break-all;
    }
    /* Timeline */
    .timeline {
      position: relative;
      margin: 1.5rem 0;
      padding-left: 2rem;
    }
    .timeline::before {
      content: '';
      position: absolute;
      left: 7px;
      top: 5px;
      bottom: 5px;
      width: 2px;
      background: var(--border);
    }
    .timeline-item {
      position: relative;
      margin-bottom: 1.5rem;
    }
    .timeline-point {
      position: absolute;
      left: -2rem;
      top: 3px;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: var(--primary);
      border: 3px solid var(--surface);
    }
    .timeline-content {
      background: var(--surface-elevated);
      padding: 0.85rem 1rem;
      border-radius: 8px;
    }
    /* Table */
    .table-responsive {
      overflow-x: auto;
      margin-top: 1rem;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
    }
    th, td {
      padding: 0.75rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }
    th {
      background: var(--surface-elevated);
      color: var(--text-muted);
      font-weight: 600;
    }
    /* Threat / Forensics Card */
    .threat-card {
      border-left: 4px solid var(--danger);
      background: rgba(239, 68, 68, 0.06);
      padding: 1rem;
      border-radius: 0 8px 8px 0;
      margin-bottom: 0.75rem;
    }
    .threat-card.elevated {
      border-left-color: var(--warning);
      background: rgba(245, 158, 11, 0.06);
    }
    .threat-card.nominal {
      border-left-color: var(--success);
      background: rgba(34, 197, 94, 0.06);
    }
    /* Step boxes */
    .step-box {
      background: var(--surface-elevated);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem;
      margin-bottom: 1rem;
    }
    .step-title {
      font-weight: 700;
      font-size: 0.95rem;
      margin-bottom: 0.5rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .step-num {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--primary);
      color: #041220;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      font-weight: 800;
    }
    .log-box {
      background: #060911;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.75rem;
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: #38bdf8;
      max-height: 180px;
      overflow-y: auto;
      white-space: pre-wrap;
      margin-top: 0.75rem;
    }
    .qr-preview-row {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
      margin-top: 1rem;
    }
    .qr-card {
      background: #fff;
      color: #000;
      border-radius: 8px;
      padding: 0.75rem;
      text-align: center;
      width: 170px;
    }
    .qr-card img {
      width: 130px;
      height: 130px;
      display: block;
      margin: 0 auto;
    }
    .qr-card .pid {
      font-size: 0.65rem;
      font-family: var(--font-mono);
      word-break: break-all;
      margin-top: 0.4rem;
    }
    .hidden { display: none !important; }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-logo">✓</div>
      <div class="brand-title">
        <h1>OPAP Protocol v0.1 // Enterprise</h1>
        <p>GS1 Digital Link 2027 · EU DPP · EPCIS 2.0 · AI Counterfeit Intel</p>
      </div>
    </div>
    <nav class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('single')">📱 Scanner</button>
      <button class="tab-btn" onclick="switchTab('dpp')">🇪🇺 Product Passport</button>
      <button class="tab-btn" onclick="switchTab('custody')">📦 EPCIS Custody</button>
      <button class="tab-btn" onclick="switchTab('forensics')">🤖 AI Forensics</button>
      <button class="tab-btn" onclick="switchTab('batch')">⚡ Batch Audit</button>
      <button class="tab-btn" onclick="switchTab('demo')">🧪 Sandbox</button>
    </nav>
  </header>

  <main class="container">
    <!-- 1. SINGLE SCANNER TAB -->
    <section id="tab-single">
      <div class="card">
        <div class="card-header">
          <h2>📱 Instant Product Authentication & GS1 Digital Link</h2>
          <p>Scan a 2D DataMatrix/QR or enter an OPAP Product ID / GS1 URI to authenticate.</p>
        </div>

        <div class="lane-selector">
          <label class="lane-pill selected" id="pill-consumer" onclick="selectLane('CONSUMER')">
            <span>🛍️ Consumer Lane (End-User)</span>
          </label>
          <label class="lane-pill" id="pill-merchant" onclick="selectLane('MERCHANT')">
            <span>🏢 Merchant Lane (Retailer)</span>
          </label>
        </div>

        <div class="input-group hidden" id="merchant-id-group">
          <label for="merchant-id-input">Merchant ID</label>
          <input type="text" id="merchant-id-input" class="input-field" placeholder="e.g. SHOP-LAGOS-042" value="STORE-DEMO-01">
        </div>

        <!-- Camera Viewfinder -->
        <div class="viewfinder-wrapper" id="viewfinder">
          <video id="scanner-video" playsinline muted></video>
          <div class="scanner-overlay" id="scanner-overlay">
            <div class="scanner-box">
              <div class="scanner-line"></div>
            </div>
          </div>
          <div id="camera-placeholder" style="color: var(--text-muted); text-align:center; padding: 2rem;">
            <p>📷 Camera inactive</p>
            <p style="font-size:0.8rem; margin-top:0.4rem;">Click "Start Camera" or upload a photo of the QR code.</p>
          </div>
        </div>

        <div class="scanner-controls">
          <button class="btn btn-primary" id="btn-toggle-camera" onclick="toggleCamera()">Start Camera</button>
          <label class="btn btn-secondary">
            Upload QR Image
            <input type="file" id="file-input" accept="image/*" style="display:none;" onchange="handleImageUpload(event)">
          </label>
        </div>

        <div class="input-group">
          <label for="product-id-input">Product ID, Serial, or Scanned URI</label>
          <div style="display:flex; gap:0.5rem;">
            <input type="text" id="product-id-input" class="input-field" placeholder="OPAP-NG-EXAMPLE-... or /01/000123.../21/SER-001" onkeydown="if(event.key==='Enter') verifySingle()">
            <button class="btn btn-primary" onclick="verifySingle()">Verify</button>
          </div>
        </div>

        <div id="single-result-area"></div>
      </div>
    </section>

    <!-- 2. DIGITAL PRODUCT PASSPORT (DPP) TAB -->
    <section id="tab-dpp" class="hidden">
      <div class="card">
        <div class="card-header">
          <h2>🇪🇺 EU ESPR Digital Product Passport (DPP)</h2>
          <p>Conforming to EU Ecodesign Regulation 2024/1781. View circularity, materials, and carbon metrics.</p>
        </div>

        <div class="input-group">
          <label for="dpp-product-input">Product ID</label>
          <div style="display:flex; gap:0.5rem;">
            <input type="text" id="dpp-product-input" class="input-field" placeholder="Enter Product ID to inspect passport...">
            <button class="btn btn-primary" onclick="fetchDPP()">Load Passport</button>
          </div>
        </div>

        <div id="dpp-content-area"></div>
      </div>
    </section>

    <!-- 3. EPCIS 2.0 CUSTODY TIMELINE TAB -->
    <section id="tab-custody" class="hidden">
      <div class="card">
        <div class="card-header">
          <h2>📦 GS1 EPCIS 2.0 Track &amp; Trace Custody Chain</h2>
          <p>Multi-hop supply chain custody audit trail with immutable business step progression.</p>
        </div>

        <div class="input-group">
          <label for="custody-product-input">Product ID</label>
          <div style="display:flex; gap:0.5rem;">
            <input type="text" id="custody-product-input" class="input-field" placeholder="Enter Product ID to view custody chain...">
            <button class="btn btn-primary" onclick="fetchCustody()">View Custody</button>
            <button class="btn btn-secondary" onclick="exportEPCIS()">Export JSON-LD</button>
          </div>
        </div>

        <div id="custody-timeline-area"></div>

        <!-- Append Custody Event Form -->
        <div class="step-box" style="margin-top:1.5rem;">
          <div class="step-title">➕ Log New Custody Transition (Authorized Agent)</div>
          <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:0.75rem; margin-top:0.75rem;">
            <div>
              <label style="font-size:0.75rem; color:var(--text-muted);">Business Step</label>
              <select id="new-custody-step" class="input-field" style="padding:0.5rem;">
                <option value="SHIPPING">SHIPPING</option>
                <option value="CUSTOMS_CLEARANCE">CUSTOMS_CLEARANCE</option>
                <option value="RECEIVING" selected>RECEIVING</option>
                <option value="HOLDING">HOLDING</option>
                <option value="RETAIL_SELLING">RETAIL_SELLING</option>
                <option value="INSPECTING">INSPECTING</option>
              </select>
            </div>
            <div>
              <label style="font-size:0.75rem; color:var(--text-muted);">Disposition</label>
              <select id="new-custody-disp" class="input-field" style="padding:0.5rem;">
                <option value="ACTIVE" selected>ACTIVE</option>
                <option value="IN_TRANSIT">IN_TRANSIT</option>
                <option value="HELD">HELD</option>
                <option value="RECALLED">RECALLED</option>
              </select>
            </div>
            <div>
              <label style="font-size:0.75rem; color:var(--text-muted);">Location Name</label>
              <input type="text" id="new-custody-loc" class="input-field" style="padding:0.5rem;" value="Rotterdam Port Customs Terminal">
            </div>
            <div>
              <label style="font-size:0.75rem; color:var(--text-muted);">Custodian Name</label>
              <input type="text" id="new-custody-custodian" class="input-field" style="padding:0.5rem;" value="Global Cargo Logistics B.V.">
            </div>
          </div>
          <div style="margin-top:0.75rem; display:flex; justify-content:flex-end;">
            <button class="btn btn-sm btn-primary" onclick="submitCustodyEvent()">Record Custody Event</button>
          </div>
        </div>

        <!-- Bulk EPCIS 2.0 Document Capture -->
        <div style="margin-top:1.5rem; background:var(--surface-elevated); padding:1rem; border-radius:10px; border:1px solid var(--border);">
          <h3 style="font-size:0.95rem; font-weight:700; margin-bottom:0.35rem;">📥 Bulk EPCIS 2.0 Event Document Ingest (Capture Pipeline)</h3>
          <p style="font-size:0.8rem; color:var(--text-muted); margin-bottom:0.75rem;">Ingest standard GS1 EPCIS 2.0 JSON-LD / CBV 2.0 event documents containing multiple ObjectEvents and multi-item SGTIN epcLists.</p>
          <textarea id="epcis-bulk-json" class="input-field" rows="4" style="font-family:var(--font-mono); font-size:0.75rem;" placeholder='Paste EPCISDocument JSON-LD or {"epcisBody": {"eventList": [...]}}'></textarea>
          <div style="margin-top:0.5rem; display:flex; gap:0.5rem; justify-content:flex-end;">
            <button class="btn btn-sm btn-secondary" onclick="loadSampleEpcisDoc()">Load Sample EPCIS Document</button>
            <button class="btn btn-sm btn-primary" onclick="submitEpcisDocument()">Ingest EPCIS Document</button>
          </div>
          <div id="epcis-bulk-result" style="margin-top:0.5rem; font-size:0.8rem;"></div>
        </div>
      </div>
    </section>

    <!-- 4. AI COUNTERFEIT FORENSICS TAB -->
    <section id="tab-forensics" class="hidden">
      <div class="card">
        <div class="card-header">
          <h2>🤖 AI Counterfeit Intelligence &amp; Surveillance Feed</h2>
          <p>Real-time detection of replay clone syndicates and impossible travel velocities (Haversine v &gt; 900 km/h).</p>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
          <h3 style="font-size:1rem; font-weight:600;">Active Threat Feed (Last 50 Anomalies)</h3>
          <button class="btn btn-sm btn-secondary" onclick="fetchGlobalThreats()">Refresh Feed</button>
        </div>

        <div id="threat-feed-area">
          <p style="color:var(--text-muted); font-size:0.85rem;">Loading surveillance feed...</p>
        </div>
      </div>
    </section>

    <!-- 5. BATCH VERIFY TAB -->
    <section id="tab-batch" class="hidden">
      <div class="card">
        <div class="card-header">
          <h2>⚡ Batch Verification &amp; Ingestion Audit</h2>
          <p>Verify up to 1,000 product tokens in a single request for warehouse carton and pallet ingestion.</p>
        </div>

        <div class="lane-selector">
          <label class="lane-pill selected" id="batch-pill-consumer" onclick="selectBatchLane('CONSUMER')">
            <span>🛍️ Consumer Lane</span>
          </label>
          <label class="lane-pill" id="batch-pill-merchant" onclick="selectBatchLane('MERCHANT')">
            <span>🏢 Merchant Lane</span>
          </label>
        </div>

        <div class="input-group hidden" id="batch-merchant-group">
          <label for="batch-merchant-input">Merchant ID</label>
          <input type="text" id="batch-merchant-input" class="input-field" placeholder="e.g. WH-DISTRIBUTOR-01" value="WH-DISTRIBUTOR-01">
        </div>

        <div class="input-group">
          <label for="batch-input">Enter Product IDs (one per line, comma-separated, or paste QR URLs)</label>
          <textarea id="batch-input" class="input-field" rows="6" placeholder="OPAP-NG-EXAMPLE-...\nOPAP-NG-EXAMPLE-...\nOPAP-NG-EXAMPLE-..."></textarea>
        </div>

        <button class="btn btn-primary" onclick="runBatchVerification()" id="btn-batch-verify">Verify Batch</button>
        <div id="batch-results-area" style="margin-top:1.5rem;"></div>
      </div>
    </section>

    <!-- 6. DEMO SANDBOX TAB -->
    <section id="tab-demo" class="hidden">
      <div class="card">
        <div class="card-header">
          <h2>🧪 OPAP Protocol Live Sandbox &amp; Label Factory</h2>
          <p>Quickly bootstrap demo manufacturers, issue GS1-compliant batches, test replay attacks, and print packaging sheets.</p>
        </div>

        <div class="step-box">
          <div class="step-title">
            <span class="step-num">1</span> Register Demo Manufacturer &amp; Key
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted);">Generates an active Ed25519 keypair and registers the manufacturer identity in the local registry.</p>
          <div style="margin-top:0.75rem;">
            <button class="btn btn-secondary" onclick="demoRegisterManufacturer()">Register Manufacturer (NG-MFR-TEST)</button>
          </div>
          <div id="demo-mfr-log" class="log-box hidden"></div>
        </div>

        <div class="step-box">
          <div class="step-title">
            <span class="step-num">2</span> Issue Signed Product Batch (with GS1 GTIN-14 &amp; DPP)
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted);">Issues 3 individual product tokens signed by the configured signer provider with canonical JSON payloads.</p>
          <div style="margin-top:0.75rem;">
            <button class="btn btn-secondary" onclick="demoIssueBatch()">Issue 3 Signed Products</button>
          </div>
          <div id="demo-issue-log" class="log-box hidden"></div>
          <div id="demo-qr-container" class="qr-preview-row"></div>
        </div>

        <div class="step-box">
          <div class="step-title">
            <span class="step-num">3</span> Factory Batch Label Sheet Generator
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted);">Generates print-ready high-density packaging sticker sheets for factory roll &amp; sheet applicators.</p>
          <div style="margin-top:0.75rem;">
            <a href="/v1/manufacturers/NG-MFR-TEST/labels/sheet" target="_blank" class="btn btn-primary btn-sm">🖨️ Open Print Sticker Sheet (HTML)</a>
          </div>
        </div>

        <div class="step-box">
          <div class="step-title">
            <span class="step-num">4</span> Active Signer &amp; Hardware Status
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted);">Inspect the current cryptographic provider (Local Env, Key File, AWS KMS, GCP KMS, or PKCS#11 HSM).</p>
          <div style="margin-top:0.75rem;">
            <button class="btn btn-secondary" onclick="checkSignerStatus()">Inspect Signer Provider</button>
          </div>
          <div id="demo-signer-log" class="log-box hidden"></div>
        </div>
      </div>
    </section>
  </main>

  <script>
    let currentLane = 'CONSUMER';
    let currentBatchLane = 'CONSUMER';
    let videoStream = null;
    let barcodeDetector = null;
    let isScanning = false;
    let lastVerifiedProductId = null;

    if ('BarcodeDetector' in window) {
      BarcodeDetector.getSupportedFormats().then(formats => {
        if (formats.includes('qr_code')) {
          barcodeDetector = new BarcodeDetector({ formats: ['qr_code'] });
        }
      }).catch(err => console.warn('BarcodeDetector error:', err));
    }

    function switchTab(tabId) {
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('main > section').forEach(sec => sec.classList.add('hidden'));
      
      const tabMap = {
        'single': 1, 'dpp': 2, 'custody': 3, 'forensics': 4, 'batch': 5, 'demo': 6
      };
      const idx = tabMap[tabId] || 1;
      const targetBtn = document.querySelector(`.tab-btn:nth-child(${idx})`);
      if (targetBtn) targetBtn.classList.add('active');
      
      const sec = document.getElementById('tab-' + tabId);
      if (sec) sec.classList.remove('hidden');

      if (tabId === 'forensics') {
        fetchGlobalThreats();
      } else if (tabId === 'dpp' && lastVerifiedProductId) {
        document.getElementById('dpp-product-input').value = lastVerifiedProductId;
        fetchDPP();
      } else if (tabId === 'custody' && lastVerifiedProductId) {
        document.getElementById('custody-product-input').value = lastVerifiedProductId;
        fetchCustody();
      }
    }

    function selectLane(lane) {
      currentLane = lane;
      document.getElementById('pill-consumer').classList.toggle('selected', lane === 'CONSUMER');
      document.getElementById('pill-merchant').classList.toggle('selected', lane === 'MERCHANT');
      document.getElementById('merchant-id-group').classList.toggle('hidden', lane !== 'MERCHANT');
    }

    function selectBatchLane(lane) {
      currentBatchLane = lane;
      document.getElementById('batch-pill-consumer').classList.toggle('selected', lane === 'CONSUMER');
      document.getElementById('batch-pill-merchant').classList.toggle('selected', lane === 'MERCHANT');
      document.getElementById('batch-merchant-group').classList.toggle('hidden', lane !== 'MERCHANT');
    }

    // Camera Viewfinder
    async function toggleCamera() {
      const video = document.getElementById('scanner-video');
      const placeholder = document.getElementById('camera-placeholder');
      const overlay = document.getElementById('scanner-overlay');
      const btn = document.getElementById('btn-toggle-camera');

      if (isScanning) {
        if (videoStream) {
          videoStream.getTracks().forEach(t => t.stop());
          videoStream = null;
        }
        video.srcObject = null;
        isScanning = false;
        placeholder.classList.remove('hidden');
        overlay.style.display = 'none';
        btn.textContent = 'Start Camera';
      } else {
        try {
          videoStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' }
          });
          video.srcObject = videoStream;
          video.play();
          isScanning = true;
          placeholder.classList.add('hidden');
          overlay.style.display = 'flex';
          btn.textContent = 'Stop Camera';
          scanVideoLoop();
        } catch (err) {
          alert('Could not start camera: ' + err.message);
        }
      }
    }

    async function scanVideoLoop() {
      if (!isScanning) return;
      const video = document.getElementById('scanner-video');
      if (video.readyState === video.HAVE_ENOUGH_DATA && barcodeDetector) {
        try {
          const barcodes = await barcodeDetector.detect(video);
          if (barcodes.length > 0) {
            handleScannedRawText(barcodes[0].rawValue);
            toggleCamera(); // stop scanner on hit
            return;
          }
        } catch (err) {
          console.warn('Scan frame error:', err);
        }
      }
      requestAnimationFrame(scanVideoLoop);
    }

    async function handleImageUpload(evt) {
      const file = evt.target.files[0];
      if (!file) return;
      if (!barcodeDetector) {
        alert('BarcodeDetector API is not supported in this browser. Please enter Product ID manually.');
        return;
      }
      try {
        const bmp = await createImageBitmap(file);
        const barcodes = await barcodeDetector.detect(bmp);
        if (barcodes.length > 0) {
          handleScannedRawText(barcodes[0].rawValue);
        } else {
          alert('No QR code detected in the uploaded image.');
        }
      } catch (err) {
        alert('Failed to analyze image: ' + err.message);
      }
    }

    function extractProductId(raw) {
      if (!raw) return '';
      raw = raw.trim();
      // Handle GS1 Digital Link /01/{gtin}/21/{serial}
      if (raw.includes('/01/') && raw.includes('/21/')) {
        const parts = raw.split('/21/');
        if (parts.length > 1) {
          return parts[1].split('?')[0].split('/')[0];
        }
      }
      if (raw.includes('/v1/verify/')) {
        return raw.split('/v1/verify/')[1].split('?')[0].split('/')[0];
      }
      return raw;
    }

    function handleScannedRawText(text) {
      const pid = extractProductId(text);
      document.getElementById('product-id-input').value = pid;
      verifySingle();
    }

    // Verify Single Product
    async function verifySingle() {
      const input = document.getElementById('product-id-input').value.trim();
      if (!input) return;
      const pid = extractProductId(input);
      lastVerifiedProductId = pid;

      const resultArea = document.getElementById('single-result-area');
      resultArea.innerHTML = '<p style="color:var(--text-muted); padding:1rem 0;">Verifying cryptographic seal and lane consumption...</p>';

      const payload = {
        product_id: pid,
        lane: currentLane,
        merchant_id: currentLane === 'MERCHANT' ? document.getElementById('merchant-id-input').value.trim() : null
      };

      try {
        const res = await fetch('/v1/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        renderSingleResult(data, pid);
      } catch (err) {
        resultArea.innerHTML = `<div class="result-panel invalid"><div class="result-title">❌ Network Error</div><p>${err.message}</p></div>`;
      }
    }

    function renderSingleResult(data, pid) {
      const resultArea = document.getElementById('single-result-area');
      const resCode = data.result || 'UNKNOWN';
      const prod = data.product || {};
      const threat = data.threat_analysis || {};

      let panelClass = 'invalid';
      let titleIcon = '❌';
      let titleText = 'COUNTERFEIT OR INVALID SIGNATURE';

      if (resCode === 'AUTHENTIC') {
        panelClass = 'authentic';
        titleIcon = '✅';
        titleText = 'GENUINE & AUTHENTIC PRODUCT';
      } else if (resCode === 'ALREADY_VERIFIED') {
        panelClass = 'replay';
        titleIcon = '⚠️';
        titleText = 'REPLAY DETECTED: ALREADY VERIFIED';
      } else if (resCode === 'REVOKED_PRODUCT' || resCode === 'REVOKED_MANUFACTURER') {
        panelClass = 'invalid';
        titleIcon = '🚫';
        titleText = 'PRODUCT OFFICIALLY REVOKED';
      }

      const threatBanner = threat.risk_flag ? `
        <div style="background:var(--danger-bg); border:1px solid var(--danger); color:#fca5a5; padding:0.75rem; border-radius:8px; margin-top:0.75rem; font-size:0.85rem;">
          ${threat.threat_advisory || 'Suspicious scan activity detected!'}
        </div>
      ` : '';

      resultArea.innerHTML = `
        <div class="result-panel ${panelClass}">
          <div class="result-title">${titleIcon} ${titleText}</div>
          <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin-top:0.5rem;">
            <span class="badge ${resCode==='AUTHENTIC'?'badge-success':(resCode==='ALREADY_VERIFIED'?'badge-warning':'badge-danger')}">${resCode}</span>
            <span class="badge badge-info">LANE: ${data.verification ? data.verification.lane : currentLane}</span>
            <span class="badge badge-info">SIG: Ed25519 VERIFIED</span>
          </div>
          ${threatBanner}
          <div class="prop-grid">
            <div class="prop-item">
              <div class="prop-label">Product Name</div>
              <div class="prop-value">${prod.product_name || 'N/A'}</div>
            </div>
            <div class="prop-item">
              <div class="prop-label">Manufacturer</div>
              <div class="prop-value">${prod.manufacturer || 'N/A'}</div>
            </div>
            <div class="prop-item">
              <div class="prop-label">Batch ID</div>
              <div class="prop-value">${prod.batch || 'N/A'}</div>
            </div>
            <div class="prop-item">
              <div class="prop-label">Product ID</div>
              <div class="prop-value" style="font-family:var(--font-mono); font-size:0.8rem;">${pid}</div>
            </div>
          </div>
          <div style="display:flex; gap:0.5rem; margin-top:1rem; flex-wrap:wrap;">
            <button class="btn btn-secondary btn-sm" onclick="quickViewDPP('${pid}')">🇪🇺 View Digital Passport</button>
            <button class="btn btn-secondary btn-sm" onclick="quickViewCustody('${pid}')">📦 View Custody Chain</button>
            <a href="/v1/products/${pid}/label.svg" target="_blank" class="btn btn-secondary btn-sm">🏷️ Packaging SVG</a>
          </div>
        </div>
      `;
    }

    function quickViewDPP(pid) {
      lastVerifiedProductId = pid;
      switchTab('dpp');
    }

    function quickViewCustody(pid) {
      lastVerifiedProductId = pid;
      switchTab('custody');
    }

    // Digital Product Passport
    async function fetchDPP() {
      const pid = document.getElementById('dpp-product-input').value.trim();
      if (!pid) return;
      const area = document.getElementById('dpp-content-area');
      area.innerHTML = '<p style="color:var(--text-muted); padding:1rem 0;">Fetching EU Digital Product Passport...</p>';

      try {
        const res = await fetch(`/v1/products/${pid}/dpp`);
        if (!res.ok) throw new Error('Product or passport not found (HTTP ' + res.status + ')');
        const data = await res.json();
        
        const certBadges = (data.compliance_certs || []).map(c => `<span class="badge badge-info" style="margin-right:0.35rem;">📜 ${c}</span>`).join('');
        const materials = Object.entries(data.materials_composition || {}).map(([k, v]) => `
          <div style="display:flex; justify-content:space-between; font-size:0.85rem; padding:0.25rem 0; border-bottom:1px solid var(--border);">
            <span>${k.replace(/_/g, ' ')}</span>
            <span style="font-weight:700; color:var(--primary);">${v}%</span>
          </div>
        `).join('');

        area.innerHTML = `
          <div class="result-panel authentic" style="margin-top:1rem;">
            <div class="result-title">🇪🇺 EU ESPR Compliance Registry Record</div>
            <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1rem;">Compliant with European Ecodesign Regulation (EU) 2024/1781.</p>
            <div class="prop-grid">
              <div class="prop-item">
                <div class="prop-label">Product Name</div>
                <div class="prop-value">${data.product_name}</div>
              </div>
              <div class="prop-item">
                <div class="prop-label">GTIN-14 (GS1)</div>
                <div class="prop-value" style="font-family:var(--font-mono);">${data.gtin || '00000000000000'}</div>
              </div>
              <div class="prop-item">
                <div class="prop-label">Carbon Footprint</div>
                <div class="prop-value" style="color:#38bdf8;">${data.carbon_footprint_kg} kg CO₂e</div>
              </div>
              <div class="prop-item">
                <div class="prop-label">Recycled Content</div>
                <div class="prop-value" style="color:#22c55e;">${data.recycled_content_pct}%</div>
              </div>
              <div class="prop-item">
                <div class="prop-label">Repairability Index</div>
                <div class="prop-value">${data.repairability_score} / 10</div>
              </div>
              <div class="prop-item">
                <div class="prop-label">Circularity Status</div>
                <div class="prop-value"><span class="badge badge-success">${data.circularity_status}</span></div>
              </div>
            </div>

            <div style="margin-top:1.25rem;">
              <h4 style="font-size:0.9rem; font-weight:700; margin-bottom:0.5rem;">Material Composition</h4>
              ${materials}
            </div>

            <div style="margin-top:1.25rem;">
              <h4 style="font-size:0.9rem; font-weight:700; margin-bottom:0.5rem;">Compliance Certifications</h4>
              ${certBadges}
            </div>

            <div style="margin-top:1.25rem; font-size:0.8rem; font-family:var(--font-mono); color:var(--text-muted); word-break:break-all;">
              Digital Link: <a href="${data.gs1_digital_link_uri}" target="_blank" style="color:var(--primary);">${data.gs1_digital_link_uri}</a>
            </div>
          </div>
        `;
      } catch (err) {
        area.innerHTML = `<div class="result-panel invalid"><p>❌ ${err.message}</p></div>`;
      }
    }

    // EPCIS Custody Timeline
    async function fetchCustody() {
      const pid = document.getElementById('custody-product-input').value.trim();
      if (!pid) return;
      const area = document.getElementById('custody-timeline-area');
      area.innerHTML = '<p style="color:var(--text-muted); padding:1rem 0;">Fetching EPCIS 2.0 custody history...</p>';

      try {
        const res = await fetch(`/v1/products/${pid}/custody`);
        if (!res.ok) throw new Error('Custody record not found (HTTP ' + res.status + ')');
        const data = await res.json();
        const events = data.events || [];

        if (events.length === 0) {
          area.innerHTML = '<p style="color:var(--text-muted); padding:1rem 0;">No custody events recorded for this product.</p>';
          return;
        }

        const items = events.map(ev => `
          <div class="timeline-item">
            <div class="timeline-point"></div>
            <div class="timeline-content">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong>${ev.business_step}</strong>
                <span class="badge badge-info" style="font-size:0.7rem;">${ev.disposition}</span>
              </div>
              <div style="font-size:0.85rem; color:var(--text-muted); margin-top:0.25rem;">
                📍 ${ev.location_name} ${ev.location_gln ? '(GLN: '+ev.location_gln+')' : ''}
              </div>
              <div style="font-size:0.85rem; margin-top:0.25rem;">
                👤 Custodian: <strong>${ev.custodian_name}</strong>
              </div>
              ${ev.notes ? `<div style="font-size:0.8rem; color:#94a3b8; font-style:italic; margin-top:0.25rem;">"${ev.notes}"</div>` : ''}
              <div style="font-size:0.75rem; color:#64748b; margin-top:0.4rem; font-family:var(--font-mono);">
                🕒 ${ev.occurred_at} · Event ID: ${ev.event_id.slice(0, 8)}...
              </div>
            </div>
          </div>
        `).join('');

        area.innerHTML = `<div class="timeline">${items}</div>`;
      } catch (err) {
        area.innerHTML = `<div class="result-panel invalid"><p>❌ ${err.message}</p></div>`;
      }
    }

    async function exportEPCIS() {
      const pid = document.getElementById('custody-product-input').value.trim();
      if (!pid) {
        alert('Please enter a Product ID first.');
        return;
      }
      window.open(`/v1/products/${pid}/custody?format=epcis`, '_blank');
    }

    async function submitCustodyEvent() {
      const pid = document.getElementById('custody-product-input').value.trim();
      if (!pid) {
        alert('Please enter a Product ID above first.');
        return;
      }
      const step = document.getElementById('new-custody-step').value;
      const disp = document.getElementById('new-custody-disp').value;
      const loc = document.getElementById('new-custody-loc').value;
      const custodian = document.getElementById('new-custody-custodian').value;

      try {
        const res = await fetch(`/v1/products/${pid}/custody`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'dev-change-me'
          },
          body: JSON.stringify({
            business_step: step,
            disposition: disp,
            location_name: loc,
            custodian_id: 'CUST-AGENT-01',
            custodian_name: custodian,
            notes: 'Field scan recorded via Operations Center.'
          })
        });
        if (!res.ok) throw new Error('Failed to record event (HTTP ' + res.status + ')');
        alert('Custody transition recorded successfully!');
        fetchCustody();
      } catch (err) {
        alert('Error: ' + err.message);
      }
    }

    function loadSampleEpcisDoc() {
      const sample = {
        "@context": ["https://ref.gs1.org/standards/epcis/2.0.0/epcis-context.jsonld", {"opap": "https://opap.org/spec/v0.1/epcis#"}],
        "type": "EPCISDocument",
        "schemaVersion": "2.0",
        "creationDate": new Date().toISOString(),
        "epcisBody": {
          "eventList": [
            {
              "type": "ObjectEvent",
              "action": "OBSERVE",
              "bizStep": "urn:epcglobal:cbv:bizstep:receiving",
              "disposition": "urn:epcglobal:cbv:disp:active",
              "readPoint": {"id": "urn:epc:id:sgln:8712345000018"},
              "bizLocation": {"name": "Amsterdam Distribution Hub North"},
              "custodian": {"id": "LOG-POSTNL-01", "name": "PostNL Logistics B.V."},
              "epcList": [
                "urn:epc:id:sgtin:00012345678905.SER-001"
              ],
              "userExtensions": {
                "opap:notes": "Batch acceptance at regional transit gateway."
              }
            }
          ]
        }
      };
      document.getElementById('epcis-bulk-json').value = JSON.stringify(sample, null, 2);
    }

    async function submitEpcisDocument() {
      const raw = document.getElementById('epcis-bulk-json').value.trim();
      const resBox = document.getElementById('epcis-bulk-result');
      if (!raw) {
        alert('Please paste or load an EPCIS 2.0 Document JSON-LD first.');
        return;
      }
      resBox.innerHTML = '<span style="color:var(--text-muted);">Ingesting EPCIS events...</span>';
      try {
        const parsed = JSON.parse(raw);
        const res = await fetch('/v1/epcis/capture', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'dev-change-me'
          },
          body: JSON.stringify(parsed)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Capture failed');
        resBox.innerHTML = `<span style="color:var(--success); font-weight:700;">✅ Ingested ${data.total_events_processed} event(s) across ${data.affected_products_count} product(s)!</span>`;
        if (document.getElementById('custody-product-input').value) {
          fetchCustody();
        }
      } catch (err) {
        resBox.innerHTML = `<span style="color:var(--danger);">❌ Ingest Error: ${err.message}</span>`;
      }
    }

    // AI Forensics
    async function fetchGlobalThreats() {
      const area = document.getElementById('threat-feed-area');
      area.innerHTML = '<p style="color:var(--text-muted); font-size:0.85rem;">Scanning global verification telemetry...</p>';

      try {
        const res = await fetch('/v1/forensics/threats');
        const data = await res.json();
        const threats = data.threats || [];

        if (threats.length === 0) {
          area.innerHTML = `
            <div class="threat-card nominal">
              <div style="font-weight:700; color:var(--success);">✅ Zero Active Supply Chain Threats</div>
              <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.25rem;">
                All recent verifications across the global registry exhibit nominal travel speeds, valid Ed25519 signatures, and unviolated one-time lanes.
              </p>
            </div>
          `;
          return;
        }

        const cards = threats.map(t => `
          <div class="threat-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <strong style="color:var(--danger);">🚨 ${t.risk_flag}</strong>
              <span class="badge badge-danger" style="font-size:0.7rem;">${t.lane} LANE</span>
            </div>
            <div style="font-size:0.85rem; margin-top:0.25rem;">
              Product ID: <a href="javascript:void(0)" onclick="quickInspectThreat('${t.product_id}')" style="color:var(--primary); font-family:var(--font-mono);">${t.product_id}</a>
            </div>
            <div style="font-size:0.8rem; color:var(--text-muted); margin-top:0.2rem;">
              Location: <strong>${t.city || 'Unknown Location'}</strong> · ${t.occurred_at}
            </div>
          </div>
        `).join('');

        area.innerHTML = cards;
      } catch (err) {
        area.innerHTML = `<p style="color:var(--danger); font-size:0.85rem;">Failed to fetch threats: ${err.message}</p>`;
      }
    }

    function quickInspectThreat(pid) {
      document.getElementById('product-id-input').value = pid;
      switchTab('single');
      verifySingle();
    }

    // Batch Verification
    async function runBatchVerification() {
      const rawText = document.getElementById('batch-input').value.trim();
      if (!rawText) return;

      const lines = rawText.split(/[,\n]+/).map(s => extractProductId(s)).filter(Boolean);
      if (lines.length === 0) return;

      const btn = document.getElementById('btn-batch-verify');
      const area = document.getElementById('batch-results-area');
      btn.disabled = true;
      btn.textContent = 'Verifying Batch...';
      area.innerHTML = '<p style="color:var(--text-muted);">Auditing items against registry...</p>';

      const payload = {
        default_lane: currentBatchLane,
        default_merchant_id: currentBatchLane === 'MERCHANT' ? document.getElementById('batch-merchant-input').value.trim() : null,
        items: lines.map(pid => ({ product_id: pid }))
      };

      try {
        const res = await fetch('/v1/verify/batch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        renderBatchResults(data);
      } catch (err) {
        area.innerHTML = `<div class="result-panel invalid"><p>❌ Batch error: ${err.message}</p></div>`;
      } finally {
        btn.disabled = false;
        btn.textContent = 'Verify Batch';
      }
    }

    function renderBatchResults(data) {
      const area = document.getElementById('batch-results-area');
      const summary = data.summary || {};
      const results = data.results || [];

      const rows = results.map(r => `
        <tr>
          <td style="font-family:var(--font-mono); font-size:0.8rem;">${r.product_id}</td>
          <td><span class="badge ${r.result==='AUTHENTIC'?'badge-success':(r.result==='ALREADY_VERIFIED'?'badge-warning':'badge-danger')}">${r.result}</span></td>
          <td>${r.product ? r.product.product_name : 'N/A'}</td>
          <td>${r.product ? r.product.batch : 'N/A'}</td>
        </tr>
      `).join('');

      area.innerHTML = `
        <div class="result-panel authentic">
          <div class="result-title">⚡ Batch Verification Summary: ${summary.status}</div>
          <div class="prop-grid">
            <div class="prop-item"><div class="prop-label">Total Items</div><div class="prop-value">${summary.total}</div></div>
            <div class="prop-item"><div class="prop-label">Authentic</div><div class="prop-value" style="color:var(--success);">${summary.authentic}</div></div>
            <div class="prop-item"><div class="prop-label">Replay / Spent</div><div class="prop-value" style="color:var(--warning);">${summary.already_verified}</div></div>
            <div class="prop-item"><div class="prop-label">Counterfeit / Invalid</div><div class="prop-value" style="color:var(--danger);">${summary.invalid}</div></div>
          </div>
          <div class="table-responsive">
            <table>
              <thead>
                <tr>
                  <th>Product ID</th>
                  <th>Status</th>
                  <th>Product</th>
                  <th>Batch</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>
      `;
    }

    // Demo Sandbox
    async function demoRegisterManufacturer() {
      const log = document.getElementById('demo-mfr-log');
      log.classList.remove('hidden');
      log.textContent = 'Generating local Ed25519 signing keypair...\n';

      try {
        const signerRes = await fetch('/v1/signer');
        const signerInfo = await signerRes.json();
        
        const payload = {
          manufacturer_id: 'NG-MFR-TEST',
          name: 'PharmaTech Global Nigeria Ltd',
          public_key_b64: signerInfo.public_key_b64
        };

        const regRes = await fetch('/v1/manufacturers', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'dev-change-me'
          },
          body: JSON.stringify(payload)
        });

        if (!regRes.ok) {
          const errData = await regRes.json();
          log.textContent += 'Manufacturer registration note: ' + JSON.stringify(errData, null, 2);
        } else {
          log.textContent += 'Manufacturer NG-MFR-TEST registered successfully!\n';
        }
      } catch (err) {
        log.textContent += 'Error: ' + err.message;
      }
    }

    async function demoIssueBatch() {
      const log = document.getElementById('demo-issue-log');
      const container = document.getElementById('demo-qr-container');
      log.classList.remove('hidden');
      log.textContent = 'Issuing 3 cryptographically signed items with GTIN-14 and EU DPP...\n';
      container.innerHTML = '';

      const payload = {
        product_code: 'AMOX-500MG-BOX',
        product_name: 'Amoxicillin Trihydrate 500mg USP',
        batch_id: 'LOT-2026-X89',
        quantity: 3,
        gtin: '00012345678905',
        carbon_footprint_kg: 0.85,
        recycled_content_pct: 35.0
      };

      try {
        const res = await fetch('/v1/manufacturers/NG-MFR-TEST/products', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'dev-change-me'
          },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        log.textContent += `Successfully issued ${data.count} items!\n`;

        data.products.forEach(p => {
          const card = document.createElement('div');
          card.className = 'qr-card';
          card.innerHTML = `
            <img src="/v1/products/${p.product_id}/qr.svg" alt="QR">
            <div class="pid">${p.product_id}</div>
            <button class="btn btn-sm btn-primary" style="margin-top:0.4rem; width:100%;" onclick="quickTestVerify('${p.product_id}')">Scan Token</button>
          `;
          container.appendChild(card);
        });
      } catch (err) {
        log.textContent += 'Error: ' + err.message;
      }
    }

    function quickTestVerify(pid) {
      document.getElementById('product-id-input').value = pid;
      switchTab('single');
      verifySingle();
    }

    async function checkSignerStatus() {
      const log = document.getElementById('demo-signer-log');
      log.classList.remove('hidden');
      log.textContent = 'Querying active cryptographic signer provider...\n';
      try {
        const res = await fetch('/v1/signer');
        const data = await res.json();
        log.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        log.textContent = 'Error: ' + err.message;
      }
    }

    // Auto-detect URL query params on load
    window.addEventListener('DOMContentLoaded', () => {
      const params = new URLSearchParams(window.location.search);
      const pid = params.get('product_id');
      const gtin = params.get('gtin');
      const serial = params.get('serial');
      const tab = params.get('tab');

      if (pid) {
        document.getElementById('product-id-input').value = pid;
        lastVerifiedProductId = pid;
        if (tab) {
          switchTab(tab);
        } else {
          verifySingle();
        }
      } else if (gtin && serial) {
        document.getElementById('product-id-input').value = `/01/${gtin}/21/${serial}`;
        verifySingle();
      }
    });
  </script>
</body>
</html>"""
