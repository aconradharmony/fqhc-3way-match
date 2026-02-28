"""
VerifyAP - Purchase Orders Admin Page
Updated: Feb 26, 2026 — Generalized (removed NetSuite branding), added PDF upload.
"""

import csv
import io
import os
import json
import base64

from .sidebar_component import get_sidebar_html, get_sidebar_styles


def handle_csv_upload(contents, purchase_orders):
    """Parse a CSV file and load POs into memory."""
    try:
        text = contents.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        count = 0
        for row in reader:
            po_num = row.get("PO Number", row.get("po_number", row.get("PO#", "")))
            if not po_num:
                continue
            po_num = po_num.strip()

            if po_num not in purchase_orders:
                purchase_orders[po_num] = {
                    "po_number": po_num,
                    "vendor": row.get("Vendor", row.get("vendor", "")),
                    "items": [],
                }

            purchase_orders[po_num]["items"].append({
                "description": row.get("Item Description", row.get("description", row.get("Item", ""))),
                "quantity": row.get("Quantity", row.get("quantity", row.get("Qty", "0"))),
                "unit_price": row.get("Unit Price", row.get("unit_price", row.get("Price", "0"))),
            })
            count += 1

        return {"success": True, "message": "Imported " + str(count) + " line items across " + str(len(purchase_orders)) + " POs."}

    except Exception as e:
        return {"success": False, "error": str(e)}


async def handle_po_pdf_upload(contents, filename, purchase_orders):
    """Process a PO PDF via Claude Vision OCR and load into memory."""
    try:
        import anthropic
        from .po_vision_prompt import get_po_vision_prompt

        b64_data = base64.b64encode(contents).decode("utf-8")

        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "pdf"
        media_map = {
            "pdf": "application/pdf",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
        }
        media_type = media_map.get(ext, "application/pdf")

        # Save file
        filepath = os.path.join("uploads", filename)
        with open(filepath, "wb") as f:
            f.write(contents)

        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        if media_type == "application/pdf":
            source_block = {
                "type": "document",
                "source": {
                    "type": "base64",
                    "media_type": "application/pdf",
                    "data": b64_data,
                },
            }
        else:
            source_block = {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": b64_data,
                },
            }

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        source_block,
                        {"type": "text", "text": get_po_vision_prompt()},
                    ],
                }
            ],
        )

        response_text = message.content[0].text

        # Extract JSON
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        po_data = json.loads(json_str)

        # Handle single PO or list of POs
        po_list = po_data if isinstance(po_data, list) else [po_data]

        count = 0
        for po in po_list:
            po_num = po.get("po_number", "")
            if not po_num:
                continue
            purchase_orders[po_num] = {
                "po_number": po_num,
                "vendor": po.get("vendor", ""),
                "items": po.get("items", []),
            }
            count += 1

        return {
            "success": True,
            "message": "Extracted " + str(count) + " purchase order(s) from PDF.",
            "data": po_list,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_admin_html(purchase_orders):
    """Generate the Purchase Orders admin page."""

    sidebar_html = get_sidebar_html("purchase_orders")
    sidebar_styles = get_sidebar_styles()

    total_pos = len(purchase_orders)
    total_items = sum(len(po.get("items", [])) for po in purchase_orders.values())
    vendors = set()
    for po in purchase_orders.values():
        v = po.get("vendor", "")
        if v:
            vendors.add(v)
    total_vendors = len(vendors)

    html = (
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VerifyAP - Purchase Orders</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    """
        + sidebar_styles
        + """
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, sans-serif; background: #F8FAFC; color: #1E293B; }

        .page-header {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #9333EA 100%);
            padding: 36px 40px 32px 40px;
            color: white;
        }
        .page-header h1 { font-size: 28px; font-weight: 800; letter-spacing: -0.5px; }
        .page-header p { margin-top: 4px; font-size: 14px; color: rgba(255,255,255,0.75); }

        .page-body { padding: 32px 40px; }

        /* Stat Cards */
        .stat-grid {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 28px;
        }
        .stat-card {
            background: white; border-radius: 12px; border: 1px solid #E2E8F0;
            padding: 24px; transition: all 0.2s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
        .stat-card-label {
            font-size: 12px; font-weight: 600; color: #64748B;
            text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;
        }
        .stat-card-value { font-size: 32px; font-weight: 800; color: #0F172A; line-height: 1; }
        .stat-card-value.green { color: #10B981; }

        /* Upload Section */
        .upload-section {
            background: white; border-radius: 16px; border: 1px solid #E2E8F0;
            padding: 32px; margin-bottom: 28px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .upload-section h2 { font-size: 18px; font-weight: 700; color: #0F172A; margin-bottom: 4px; }
        .upload-section .subtitle { font-size: 13px; color: #64748B; margin-bottom: 20px; }

        /* Tabs */
        .upload-tabs {
            display: flex; gap: 0; margin-bottom: 24px;
            border-bottom: 2px solid #E2E8F0;
        }
        .upload-tab {
            padding: 10px 20px; font-size: 13px; font-weight: 600;
            color: #64748B; cursor: pointer; border-bottom: 2px solid transparent;
            margin-bottom: -2px; transition: all 0.2s ease;
            background: none; border-top: none; border-left: none; border-right: none;
        }
        .upload-tab:hover { color: #4F46E5; }
        .upload-tab.active { color: #4F46E5; border-bottom-color: #4F46E5; }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* Tip box */
        .tip-box {
            background: #EEF2FF; border-left: 4px solid #4F46E5;
            border-radius: 0 8px 8px 0; padding: 16px 20px; margin-bottom: 20px;
        }
        .tip-box-title { font-size: 13px; font-weight: 700; color: #4F46E5; margin-bottom: 6px; }
        .tip-box ul { padding-left: 18px; font-size: 13px; color: #475569; line-height: 1.8; }

        /* Drop zone */
        .drop-zone {
            border: 2px dashed #CBD5E1; border-radius: 12px;
            padding: 48px 24px; text-align: center; background: #F8FAFC;
            cursor: pointer; transition: all 0.2s ease; margin-bottom: 20px;
        }
        .drop-zone:hover, .drop-zone.drag-over {
            border-color: #4F46E5; background: #EEF2FF;
        }
        .drop-zone-icon { font-size: 48px; margin-bottom: 12px; }
        .drop-zone-text { font-size: 15px; font-weight: 600; color: #334155; margin-bottom: 4px; }
        .drop-zone-sub { font-size: 13px; color: #94A3B8; }

        .file-types {
            display: flex; gap: 8px; justify-content: center; margin-top: 12px; flex-wrap: wrap;
        }
        .file-type-badge {
            display: inline-block; padding: 4px 10px; border-radius: 6px;
            font-size: 11px; font-weight: 600; background: #EEF2FF; color: #4F46E5;
            text-transform: uppercase;
        }

        .selected-file {
            display: none; align-items: center; gap: 10px;
            padding: 12px 16px; background: #EEF2FF; border-radius: 8px;
            margin-bottom: 16px; font-size: 13px; color: #4F46E5; font-weight: 500;
        }
        .selected-file.show { display: flex; }
        .selected-file-remove {
            margin-left: auto; cursor: pointer; color: #94A3B8; font-size: 16px;
        }
        .selected-file-remove:hover { color: #EF4444; }

        .upload-btn {
            display: inline-flex; align-items: center; gap: 8px;
            padding: 12px 28px;
            background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
            color: white; border: none; border-radius: 8px;
            font-size: 14px; font-weight: 600; cursor: pointer;
            transition: all 0.2s ease; box-shadow: 0 2px 8px rgba(79,70,229,0.3);
        }
        .upload-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(79,70,229,0.4); }
        .upload-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

        .file-input { display: none; }

        .loading-spinner { display: none; text-align: center; padding: 32px; }
        .loading-spinner.show { display: block; }
        .spinner {
            width: 40px; height: 40px; border: 3px solid #E2E8F0;
            border-top: 3px solid #4F46E5; border-radius: 50%;
            animation: spin 0.8s linear infinite; margin: 0 auto 12px auto;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading-text { font-size: 14px; color: #64748B; font-weight: 500; }

        .status-msg {
            display: none; padding: 16px; border-radius: 8px;
            font-size: 13px; margin-top: 12px;
        }
        .status-msg.show { display: block; }
        .status-msg.success { background: #ECFDF5; border: 1px solid #A7F3D0; color: #059669; }
        .status-msg.error { background: #FEF2F2; border: 1px solid #FECACA; color: #DC2626; }
    </style>
</head>
<body>
    """
        + sidebar_html
        + """
    <div class="verifyap-main-content">
        <div class="page-header">
            <h1>Purchase Orders</h1>
            <p>Import and manage purchase order data</p>
        </div>

        <div class="page-body">
            <!-- Stats -->
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-card-label">Active POs</div>
                    <div class="stat-card-value green">"""
        + str(total_pos)
        + """</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Line Items</div>
                    <div class="stat-card-value">"""
        + str(total_items)
        + """</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Active Vendors</div>
                    <div class="stat-card-value">"""
        + str(total_vendors)
        + """</div>
                </div>
            </div>

            <!-- Upload Section -->
            <div class="upload-section">
                <h2>Upload Purchase Orders</h2>
                <p class="subtitle">Import purchase orders from a CSV file or upload a PO document (PDF/image) for AI extraction</p>

                <div class="upload-tabs">
                    <button class="upload-tab active" id="tabCsv" onclick="switchTab('csv')">&#128196; CSV Upload</button>
                    <button class="upload-tab" id="tabPdf" onclick="switchTab('pdf')">&#128209; PDF / Image Upload</button>
                </div>

                <!-- CSV Tab -->
                <div class="tab-content active" id="tabContentCsv">
                    <div class="tip-box">
                        <div class="tip-box-title">&#128214; CSV Format Guide:</div>
                        <ul>
                            <li>Required columns: PO Number, Vendor, Item Description, Quantity, Unit Price</li>
                            <li>Export from your ERP or accounting system as CSV</li>
                            <li>One row per line item (multiple rows per PO is fine)</li>
                        </ul>
                    </div>

                    <input type="file" id="csvFileInput" class="file-input" accept=".csv">

                    <div class="drop-zone" id="csvDropZone">
                        <div class="drop-zone-icon">&#128202;</div>
                        <div class="drop-zone-text">Drop CSV file here</div>
                        <div class="drop-zone-sub">or click to browse &bull; Accepts .csv files</div>
                    </div>

                    <div class="selected-file" id="csvSelectedFile">
                        <span>&#128196;</span>
                        <span id="csvFileName">file.csv</span>
                        <span class="selected-file-remove" id="csvRemoveFile">&times;</span>
                    </div>

                    <button class="upload-btn" id="csvUploadBtn" disabled>
                        &#128640; Upload &amp; Process CSV
                    </button>

                    <div class="loading-spinner" id="csvLoading">
                        <div class="spinner"></div>
                        <div class="loading-text">Processing CSV...</div>
                    </div>
                    <div class="status-msg" id="csvStatus"></div>
                </div>

                <!-- PDF Tab -->
                <div class="tab-content" id="tabContentPdf">
                    <div class="tip-box">
                        <div class="tip-box-title">&#129302; AI-Powered Extraction:</div>
                        <ul>
                            <li>Upload a PDF or photo of your purchase order</li>
                            <li>Our AI will extract PO number, vendor, line items, and quantities</li>
                            <li>Works with scanned documents, photos, and digital PDFs</li>
                        </ul>
                    </div>

                    <input type="file" id="pdfFileInput" class="file-input"
                           accept=".pdf,.jpg,.jpeg,.png">

                    <div class="drop-zone" id="pdfDropZone">
                        <div class="drop-zone-icon">&#128209;</div>
                        <div class="drop-zone-text">Drop PO document here</div>
                        <div class="drop-zone-sub">or click to browse</div>
                        <div class="file-types">
                            <span class="file-type-badge">PDF</span>
                            <span class="file-type-badge">JPG</span>
                            <span class="file-type-badge">PNG</span>
                        </div>
                    </div>

                    <div class="selected-file" id="pdfSelectedFile">
                        <span>&#128196;</span>
                        <span id="pdfFileName">document.pdf</span>
                        <span class="selected-file-remove" id="pdfRemoveFile">&times;</span>
                    </div>

                    <button class="upload-btn" id="pdfUploadBtn" disabled>
                        &#129302; Upload &amp; Extract with AI
                    </button>

                    <div class="loading-spinner" id="pdfLoading">
                        <div class="spinner"></div>
                        <div class="loading-text">Analyzing document with AI...</div>
                    </div>
                    <div class="status-msg" id="pdfStatus"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        /* --- Tab Switching --- */
        function switchTab(tab) {
            document.getElementById('tabCsv').classList.toggle('active', tab === 'csv');
            document.getElementById('tabPdf').classList.toggle('active', tab === 'pdf');
            document.getElementById('tabContentCsv').classList.toggle('active', tab === 'csv');
            document.getElementById('tabContentPdf').classList.toggle('active', tab === 'pdf');
        }

        /* --- CSV Upload Logic --- */
        var csvFile = null;
        var csvDropZone = document.getElementById('csvDropZone');
        var csvFileInput = document.getElementById('csvFileInput');

        csvDropZone.addEventListener('click', function() { csvFileInput.click(); });
        csvDropZone.addEventListener('dragover', function(e) {
            e.preventDefault(); csvDropZone.classList.add('drag-over');
        });
        csvDropZone.addEventListener('dragleave', function() { csvDropZone.classList.remove('drag-over'); });
        csvDropZone.addEventListener('drop', function(e) {
            e.preventDefault(); csvDropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length) handleCsvFile(e.dataTransfer.files[0]);
        });
        csvFileInput.addEventListener('change', function() {
            if (csvFileInput.files.length) handleCsvFile(csvFileInput.files[0]);
        });

        function handleCsvFile(file) {
            csvFile = file;
            document.getElementById('csvFileName').textContent = file.name;
            document.getElementById('csvSelectedFile').classList.add('show');
            csvDropZone.style.display = 'none';
            document.getElementById('csvUploadBtn').disabled = false;
        }

        document.getElementById('csvRemoveFile').addEventListener('click', function() {
            csvFile = null;
            document.getElementById('csvSelectedFile').classList.remove('show');
            csvDropZone.style.display = 'block';
            document.getElementById('csvUploadBtn').disabled = true;
            csvFileInput.value = '';
        });

        document.getElementById('csvUploadBtn').addEventListener('click', function() {
            if (!csvFile) return;
            var btn = document.getElementById('csvUploadBtn');
            var loading = document.getElementById('csvLoading');
            var status = document.getElementById('csvStatus');

            btn.disabled = true;
            loading.classList.add('show');
            status.classList.remove('show');

            var fd = new FormData();
            fd.append('file', csvFile);

            fetch('/api/upload-csv', { method: 'POST', body: fd })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    loading.classList.remove('show');
                    status.classList.add('show');
                    if (data.success) {
                        status.className = 'status-msg show success';
                        status.textContent = data.message;
                        setTimeout(function() { location.reload(); }, 1500);
                    } else {
                        status.className = 'status-msg show error';
                        status.textContent = 'Error: ' + (data.error || 'Unknown error');
                        btn.disabled = false;
                    }
                })
                .catch(function(err) {
                    loading.classList.remove('show');
                    status.className = 'status-msg show error';
                    status.textContent = 'Network error: ' + err.message;
                    status.classList.add('show');
                    btn.disabled = false;
                });
        });

        /* --- PDF Upload Logic --- */
        var pdfFile = null;
        var pdfDropZone = document.getElementById('pdfDropZone');
        var pdfFileInput = document.getElementById('pdfFileInput');

        pdfDropZone.addEventListener('click', function() { pdfFileInput.click(); });
        pdfDropZone.addEventListener('dragover', function(e) {
            e.preventDefault(); pdfDropZone.classList.add('drag-over');
        });
        pdfDropZone.addEventListener('dragleave', function() { pdfDropZone.classList.remove('drag-over'); });
        pdfDropZone.addEventListener('drop', function(e) {
            e.preventDefault(); pdfDropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length) handlePdfFile(e.dataTransfer.files[0]);
        });
        pdfFileInput.addEventListener('change', function() {
            if (pdfFileInput.files.length) handlePdfFile(pdfFileInput.files[0]);
        });

        function handlePdfFile(file) {
            pdfFile = file;
            document.getElementById('pdfFileName').textContent = file.name;
            document.getElementById('pdfSelectedFile').classList.add('show');
            pdfDropZone.style.display = 'none';
            document.getElementById('pdfUploadBtn').disabled = false;
        }

        document.getElementById('pdfRemoveFile').addEventListener('click', function() {
            pdfFile = null;
            document.getElementById('pdfSelectedFile').classList.remove('show');
            pdfDropZone.style.display = 'block';
            document.getElementById('pdfUploadBtn').disabled = true;
            pdfFileInput.value = '';
        });

        document.getElementById('pdfUploadBtn').addEventListener('click', function() {
            if (!pdfFile) return;
            var btn = document.getElementById('pdfUploadBtn');
            var loading = document.getElementById('pdfLoading');
            var status = document.getElementById('pdfStatus');

            btn.disabled = true;
            loading.classList.add('show');
            status.classList.remove('show');

            var fd = new FormData();
            fd.append('file', pdfFile);

            fetch('/api/upload-po-pdf', { method: 'POST', body: fd })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    loading.classList.remove('show');
                    status.classList.add('show');
                    if (data.success) {
                        status.className = 'status-msg show success';
                        status.textContent = data.message;
                        setTimeout(function() { location.reload(); }, 1500);
                    } else {
                        status.className = 'status-msg show error';
                        status.textContent = 'Error: ' + (data.error || 'Unknown error');
                        btn.disabled = false;
                    }
                })
                .catch(function(err) {
                    loading.classList.remove('show');
                    status.className = 'status-msg show error';
                    status.textContent = 'Network error: ' + err.message;
                    status.classList.add('show');
                    btn.disabled = false;
                });
        });
    </script>
</body>
</html>"""
    )

    return html
