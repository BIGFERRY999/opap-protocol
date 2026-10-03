"""Web Scanner and Verification UI for OPAP Protocol.

Zero external CDN dependencies, fully self-contained modern HTML5/CSS3/Vanilla JS
supporting:
- Native BarcodeDetector QR scanning with camera viewfinder
- Image upload & clipboard paste decoding
- Consumer vs. Merchant lane verification
- Batch verification table & risk analysis
- Interactive Protocol Demo Sandbox
"""

def get_scanner_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OPAP v0.1 | Product Authentication & Scanner</title>
  <style>
    :root {
      --bg: #0b0f19;
      --surface: #131c2e;
      --surface-elevated: #1a263e;
      --border: #233554;
      --text: #f1f5f9;
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
      padding: 1rem 1.5rem;
      display: flex;
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
      gap: 0.5rem;
      background: var(--surface-elevated);
      padding: 0.25rem;
      border-radius: 10px;
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.4rem 0.9rem;
      border-radius: 7px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
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
      max-width: 900px;
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
      font-size: 1.2rem;
      font-weight: 600;
    }
    .card-header p {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
    }
    /* Controls */
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
    .lane-pill input[type="radio"] {
      display: none;
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
      padding: 0.75rem 1.5rem;
      border-radius: 8px;
      font-size: 0.95rem;
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
      background: var(--border);
    }
    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    /* Scanner Viewfinder */
    .viewfinder-wrapper {
      position: relative;
      background: #000;
      border-radius: 12px;
      overflow: hidden;
      aspect-ratio: 4 / 3;
      max-height: 380px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 1.25rem;
      border: 1px solid var(--border);
    }
    video#scanner-video {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .scanner-overlay {
      position: absolute;
      inset: 0;
      pointer-events: none;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .scanner-box {
      width: 220px;
      height: 220px;
      border: 2px solid rgba(56, 189, 248, 0.8);
      border-radius: 16px;
      position: relative;
      box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
    }
    .scanner-line {
      position: absolute;
      left: 10px;
      right: 10px;
      height: 2px;
      background: var(--primary);
      box-shadow: 0 0 10px var(--primary);
      animation: scan 2.2s infinite ease-in-out;
    }
    @keyframes scan {
      0%, 100% { top: 10px; }
      50% { top: 206px; }
    }
    .scanner-controls {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
      margin-bottom: 1.25rem;
    }
    /* Result Badges */
    .result-banner {
      border-radius: 10px;
      padding: 1.25rem;
      margin-top: 1.25rem;
      display: flex;
      align-items: flex-start;
      gap: 1rem;
      animation: fadeIn 0.25s ease;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .result-banner.authentic {
      background: var(--success-bg);
      border: 1px solid var(--success);
      color: #86efac;
    }
    .result-banner.already_verified {
      background: var(--warning-bg);
      border: 1px solid var(--warning);
      color: #fcd34d;
    }
    .result-banner.invalid, .result-banner.revoked {
      background: var(--danger-bg);
      border: 1px solid var(--danger);
      color: #fca5a5;
    }
    .result-icon {
      font-size: 2rem;
      line-height: 1;
    }
    .result-content h3 {
      font-size: 1.2rem;
      font-weight: 700;
      margin-bottom: 0.25rem;
    }
    .result-content p {
      font-size: 0.9rem;
      opacity: 0.95;
    }
    .details-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
      font-size: 0.85rem;
    }
    .details-table th, .details-table td {
      padding: 0.5rem 0.75rem;
      border-bottom: 1px solid var(--border);
      text-align: left;
    }
    .details-table th {
      color: var(--text-muted);
      width: 32%;
    }
    .details-table td {
      font-family: var(--font-mono);
      word-break: break-all;
    }
    /* Stats & Batch */
    .stats-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .stat-card {
      background: var(--surface-elevated);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1rem;
      text-align: center;
    }
    .stat-card .val {
      font-size: 1.75rem;
      font-weight: 800;
      margin-top: 0.25rem;
    }
    .stat-card.green .val { color: var(--success); }
    .stat-card.amber .val { color: var(--warning); }
    .stat-card.red .val { color: var(--danger); }
    .stat-card .lbl {
      font-size: 0.75rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .batch-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
      margin-top: 1rem;
    }
    .batch-table th, .batch-table td {
      padding: 0.6rem 0.75rem;
      border-bottom: 1px solid var(--border);
      text-align: left;
    }
    .badge {
      display: inline-block;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 700;
    }
    .badge.authentic { background: var(--success-bg); color: var(--success); border: 1px solid var(--success); }
    .badge.already_verified { background: var(--warning-bg); color: var(--warning); border: 1px solid var(--warning); }
    .badge.invalid { background: var(--danger-bg); color: var(--danger); border: 1px solid var(--danger); }
    .badge.revoked { background: var(--danger-bg); color: #f87171; border: 1px solid #f87171; }
    /* Demo Lab */
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
        <h1>OPAP Protocol v0.1</h1>
        <p>Open Product Authentication & Dual-Lane Verifier</p>
      </div>
    </div>
    <nav class="nav-tabs">
      <button class="tab-btn active" onclick="switchTab('single')">Single Scanner</button>
      <button class="tab-btn" onclick="switchTab('batch')">Batch Verify</button>
      <button class="tab-btn" onclick="switchTab('demo')">Demo Sandbox</button>
    </nav>
  </header>

  <main class="container">
    <!-- SINGLE SCANNER TAB -->
    <section id="tab-single">
      <div class="card">
        <div class="card-header">
          <h2>Product Authentication Scanner</h2>
          <p>Scan a product QR code or enter an OPAP Product ID to check authenticity.</p>
        </div>

        <!-- Lane Selection -->
        <div class="lane-selector">
          <label class="lane-pill selected" id="pill-consumer" onclick="selectLane('CONSUMER')">
            <input type="radio" name="lane" value="CONSUMER" checked>
            <span>🛍️ Consumer Lane (End-User)</span>
          </label>
          <label class="lane-pill" id="pill-merchant" onclick="selectLane('MERCHANT')">
            <input type="radio" name="lane" value="MERCHANT">
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

        <!-- Manual Product ID Input -->
        <div class="input-group">
          <label for="product-id-input">Product ID or Scanned URL</label>
          <div style="display:flex; gap:0.5rem;">
            <input type="text" id="product-id-input" class="input-field" placeholder="OPAP-NG-EXAMPLE-..." onkeydown="if(event.key==='Enter') verifySingle()">
            <button class="btn btn-primary" onclick="verifySingle()">Verify</button>
          </div>
        </div>

        <!-- Result Box -->
        <div id="single-result-area"></div>
      </div>
    </section>

    <!-- BATCH VERIFY TAB -->
    <section id="tab-batch" class="hidden">
      <div class="card">
        <div class="card-header">
          <h2>Batch Verification Engine</h2>
          <p>Verify multiple product identifiers at once. Ideal for supply chain ingestion and carton auditing.</p>
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

    <!-- DEMO SANDBOX TAB -->
    <section id="tab-demo" class="hidden">
      <div class="card">
        <div class="card-header">
          <h2>OPAP Protocol Live Sandbox</h2>
          <p>Quickly bootstrap a test manufacturer, issue cryptographically signed products, and test double-spend / replay defense.</p>
        </div>

        <div class="step-box">
          <div class="step-title">
            <span class="step-num">1</span> Register Demo Manufacturer & Key
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted);">Generates an active Ed25519 keypair and registers the manufacturer identity in the local registry.</p>
          <div style="margin-top:0.75rem;">
            <button class="btn btn-secondary" onclick="demoRegisterManufacturer()">Register Manufacturer (NG-MFR-TEST)</button>
          </div>
          <div id="demo-mfr-log" class="log-box hidden"></div>
        </div>

        <div class="step-box">
          <div class="step-title">
            <span class="step-num">2</span> Issue Signed Product Batch
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
            <span class="step-num">3</span> Active Signer & Hardware Status
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

    // Initialize Barcode Detector if supported
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
      if (tabId === 'single') {
        document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
        document.getElementById('tab-single').classList.remove('hidden');
      } else if (tabId === 'batch') {
        document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
        document.getElementById('tab-batch').classList.remove('hidden');
      } else {
        document.querySelector('.tab-btn:nth-child(3)').classList.add('active');
        document.getElementById('tab-demo').classList.remove('hidden');
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

    // Camera handling
    async function toggleCamera() {
      const btn = document.getElementById('btn-toggle-camera');
      const video = document.getElementById('scanner-video');
      const placeholder = document.getElementById('camera-placeholder');

      if (videoStream) {
        // Stop
        videoStream.getTracks().forEach(t => t.stop());
        videoStream = null;
        isScanning = false;
        video.srcObject = null;
        placeholder.style.display = 'block';
        btn.textContent = 'Start Camera';
        btn.classList.remove('btn-secondary');
        btn.classList.add('btn-primary');
        return;
      }

      try {
        videoStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' }
        });
        video.srcObject = videoStream;
        await video.play();
        placeholder.style.display = 'none';
        btn.textContent = 'Stop Camera';
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-secondary');
        isScanning = true;
        scanLoop();
      } catch (err) {
        alert('Could not access camera: ' + err.message + '\\nYou can still upload a QR photo or paste the Product ID.');
      }
    }

    async function scanLoop() {
      if (!isScanning) return;
      const video = document.getElementById('scanner-video');

      if (barcodeDetector && video.readyState === video.HAVE_ENOUGH_DATA) {
        try {
          const barcodes = await barcodeDetector.detect(video);
          if (barcodes.length > 0) {
            const rawValue = barcodes[0].rawValue;
            handleDetectedCode(rawValue);
            // Throttle after detection
            setTimeout(() => { if (isScanning) requestAnimationFrame(scanLoop); }, 1500);
            return;
          }
        } catch (e) {
          // Frame error, continue
        }
      }
      requestAnimationFrame(scanLoop);
    }

    function extractProductId(text) {
      if (!text) return '';
      text = text.trim();
      if (text.includes('/v1/verify/')) {
        return text.split('/v1/verify/')[1].split('?')[0].split('#')[0].trim();
      }
      return text;
    }

    function handleDetectedCode(code) {
      const pid = extractProductId(code);
      document.getElementById('product-id-input').value = pid;
      verifySingle(pid);
    }

    // Handle Image Upload File
    async function handleImageUpload(e) {
      const file = e.target.files[0];
      if (!file) return;

      if (!barcodeDetector) {
        alert('BarcodeDetector API is not supported in this browser. Please enter the Product ID manually.');
        return;
      }

      try {
        const imageBitmap = await createImageBitmap(file);
        const barcodes = await barcodeDetector.detect(imageBitmap);
        if (barcodes.length > 0) {
          handleDetectedCode(barcodes[0].rawValue);
        } else {
          alert('No QR code detected in the uploaded image.');
        }
      } catch (err) {
        alert('Error analyzing image: ' + err.message);
      }
    }

    // Verify Single Product
    async function verifySingle(explicitPid) {
      const pid = explicitPid || extractProductId(document.getElementById('product-id-input').value);
      if (!pid) {
        alert('Please provide or scan a Product ID.');
        return;
      }

      const area = document.getElementById('single-result-area');
      area.innerHTML = '<div style="color:var(--text-muted); padding:1rem; text-align:center;">Verifying cryptographic signature & consumption lane...</div>';

      const body = {
        product_id: pid,
        lane: currentLane,
        merchant_id: currentLane === 'MERCHANT' ? (document.getElementById('merchant-id-input').value || 'STORE-01') : null
      };

      try {
        const res = await fetch('/v1/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await res.json();
        renderSingleResult(data, pid);
      } catch (err) {
        area.innerHTML = `<div class="result-banner invalid"><div class="result-icon">⚠️</div><div class="result-content"><h3>Network / Server Error</h3><p>${err.message}</p></div></div>`;
      }
    }

    function renderSingleResult(data, pid) {
      const area = document.getElementById('single-result-area');
      const res = data.result;

      let bannerClass = 'invalid';
      let icon = '❌';
      let title = 'Invalid Product';
      let explanation = 'This product record or cryptographic signature could not be verified.';

      if (res === 'AUTHENTIC') {
        bannerClass = 'authentic';
        icon = '✅';
        title = 'Authentic Product Verified';
        explanation = `Genuine item issued under OPAP v0.1. Verified successfully in the ${data.verification.lane} lane.`;
      } else if (res === 'ALREADY_VERIFIED') {
        bannerClass = 'already_verified';
        icon = '⚠️';
        title = 'Duplicate / Already Verified';
        explanation = `This product was ALREADY VERIFIED in the ${data.verification.lane} lane! Possible clone or physical counterfeiting replay.`;
      } else if (res === 'REVOKED_PRODUCT') {
        bannerClass = 'revoked';
        icon = '⛔';
        title = 'Revoked Product';
        explanation = 'This product item or batch has been officially revoked or recalled by the manufacturer.';
      } else if (res === 'REVOKED_MANUFACTURER') {
        bannerClass = 'revoked';
        icon = '⛔';
        title = 'Revoked Manufacturer';
        explanation = 'The manufacturer or signing key has been revoked and is no longer trusted.';
      }

      let p = data.product || {};
      let html = `
        <div class="result-banner ${bannerClass}">
          <div class="result-icon">${icon}</div>
          <div class="result-content" style="flex:1;">
            <h3>${title}</h3>
            <p>${explanation}</p>
          </div>
        </div>
      `;

      if (p.product_id) {
        html += `
          <table class="details-table">
            <tr><th>Product Name</th><td><strong>${p.name || 'N/A'}</strong></td></tr>
            <tr><th>Product Code</th><td>${p.product_code || 'N/A'}</td></tr>
            <tr><th>Manufacturer</th><td>${p.manufacturer || p.manufacturer_id || 'N/A'}</td></tr>
            <tr><th>Batch ID</th><td>${p.batch || 'N/A'}</td></tr>
            <tr><th>Product ID</th><td>${p.product_id}</td></tr>
            <tr><th>Audit Event ID</th><td>${data.event_id || 'N/A'}</td></tr>
          </table>
        `;
      }

      area.innerHTML = html;
    }

    // Batch Verification
    async function runBatchVerification() {
      const text = document.getElementById('batch-input').value.trim();
      if (!text) {
        alert('Please enter one or more Product IDs.');
        return;
      }

      const lines = text.split(/[\\n,]+/).map(s => extractProductId(s)).filter(Boolean);
      if (lines.length === 0) {
        alert('No valid Product IDs found.');
        return;
      }

      const area = document.getElementById('batch-results-area');
      area.innerHTML = '<div style="color:var(--text-muted); padding:1rem; text-align:center;">Processing batch verification...</div>';

      const items = lines.map(pid => ({
        product_id: pid,
        lane: currentBatchLane,
        merchant_id: currentBatchLane === 'MERCHANT' ? (document.getElementById('batch-merchant-input').value || 'STORE-01') : null
      }));

      try {
        const res = await fetch('/v1/verify/batch', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            items: items,
            default_lane: currentBatchLane,
            default_merchant_id: currentBatchLane === 'MERCHANT' ? (document.getElementById('batch-merchant-input').value || 'STORE-01') : null
          })
        });
        const data = await res.json();
        renderBatchResults(data);
      } catch (err) {
        area.innerHTML = `<div class="result-banner invalid"><div class="result-icon">⚠️</div><div class="result-content"><h3>Batch Error</h3><p>${err.message}</p></div></div>`;
      }
    }

    function renderBatchResults(data) {
      const s = data.summary;
      const area = document.getElementById('batch-results-area');

      let rows = data.results.map(r => {
        let badgeClass = 'invalid';
        if (r.result === 'AUTHENTIC') badgeClass = 'authentic';
        else if (r.result === 'ALREADY_VERIFIED') badgeClass = 'already_verified';
        else if (r.result.includes('REVOKED')) badgeClass = 'revoked';

        let name = r.product ? r.product.name : 'Unknown';
        let batch = r.product ? r.product.batch : '-';

        return `
          <tr>
            <td><span class="badge ${badgeClass}">${r.result}</span></td>
            <td>${name}</td>
            <td>${batch}</td>
            <td style="font-family:var(--font-mono); font-size:0.75rem;">${r.product_id}</td>
          </tr>
        `;
      }).join('');

      area.innerHTML = `
        <div class="stats-row">
          <div class="stat-card"><div class="lbl">Total Items</div><div class="val">${s.total}</div></div>
          <div class="stat-card green"><div class="lbl">Authentic</div><div class="val">${s.authentic}</div></div>
          <div class="stat-card amber"><div class="lbl">Replays</div><div class="val">${s.already_verified}</div></div>
          <div class="stat-card red"><div class="lbl">Revoked</div><div class="val">${s.revoked}</div></div>
          <div class="stat-card red"><div class="lbl">Invalid</div><div class="val">${s.invalid}</div></div>
        </div>

        <table class="batch-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Product</th>
              <th>Batch</th>
              <th>Product ID</th>
            </tr>
          </thead>
          <tbody>
            ${rows}
          </tbody>
        </table>
      `;
    }

    // Demo Sandbox Actions
    let demoApiKey = 'dev-change-me';

    async function demoRegisterManufacturer() {
      const log = document.getElementById('demo-mfr-log');
      log.classList.remove('hidden');
      log.textContent = 'Checking active signer and registering NG-MFR-TEST...';

      try {
        const signerRes = await fetch('/v1/signer');
        const signer = await signerRes.json();

        const res = await fetch('/v1/manufacturers', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': demoApiKey
          },
          body: JSON.stringify({
            manufacturer_id: 'NG-MFR-TEST',
            name: 'Golden Standard AgriCorp Ltd.',
            key_id: 'KEY-TEST-001',
            public_key_b64: signer.public_key_b64
          })
        });

        if (res.status === 409) {
          log.textContent = 'Manufacturer NG-MFR-TEST is already registered and ready for product issuance.';
        } else {
          const data = await res.json();
          log.textContent = 'Registered successfully:\\n' + JSON.stringify(data, null, 2);
        }
      } catch (err) {
        log.textContent = 'Error: ' + err.message;
      }
    }

    async function demoIssueBatch() {
      const log = document.getElementById('demo-issue-log');
      const container = document.getElementById('demo-qr-container');
      log.classList.remove('hidden');
      log.textContent = 'Issuing 3 signed product records with Ed25519 signatures...';
      container.innerHTML = '';

      try {
        const res = await fetch('/v1/manufacturers/NG-MFR-TEST/products', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': demoApiKey
          },
          body: JSON.stringify({
            product_code: 'RICE-50KG',
            product_name: 'Golden Harvest Premium Rice',
            batch_id: 'BATCH-2026-X',
            quantity: 3
          })
        });

        const data = await res.json();
        log.textContent = `Issued ${data.count} signed products successfully.`;

        let batchIds = [];
        data.products.forEach(p => {
          batchIds.push(p.product_id);
          const card = document.createElement('div');
          card.className = 'qr-card';
          card.innerHTML = `
            <img src="/v1/products/${p.product_id}/qr.svg" alt="QR Code">
            <div class="pid">${p.product_id.substring(0, 18)}...</div>
            <button class="btn btn-primary" style="padding:0.3rem 0.6rem; font-size:0.75rem; margin-top:0.4rem; width:100%;" onclick="testVerifyFromDemo('${p.product_id}')">Scan / Verify</button>
          `;
          container.appendChild(card);
        });

        // Prepopulate batch textarea
        document.getElementById('batch-input').value = batchIds.join('\\n');
      } catch (err) {
        log.textContent = 'Error: ' + err.message;
      }
    }

    function testVerifyFromDemo(pid) {
      switchTab('single');
      document.getElementById('product-id-input').value = pid;
      verifySingle(pid);
    }

    async function checkSignerStatus() {
      const log = document.getElementById('demo-signer-log');
      log.classList.remove('hidden');
      log.textContent = 'Inspecting configured signer provider...';
      try {
        const res = await fetch('/v1/signer');
        const data = await res.json();
        log.textContent = JSON.stringify(data, null, 2);
      } catch (err) {
        log.textContent = 'Error: ' + err.message;
      }
    }
  </script>
</body>
</html>
"""
