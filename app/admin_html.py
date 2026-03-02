"""
VerifyAP - Purchase Orders Admin Page
Updated: Mar 2, 2026 — Unified smart upload (CSV, PDF, image auto-detection).
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


def handle_tsv_upload(contents, purchase_orders):
    """Parse a TSV file and load POs into memory."""
    try:
        text = contents.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text), delimiter="\t")
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
    """Process a PO PDF/image via Claude Vision OCR and load into memory."""
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
            "heic": "image/heic",
            "gif": "image/gif",
            "webp": "image/webp",
            "tiff": "image/tiff",
            "tif": "image/tiff",
            "bmp": "image/bmp",
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
        total_items = 0
        for po in po_list:
            po_num = po.get("po_number", "")
            if not po_num:
                continue
            purchase_orders[po_num] = {
                "po_number": po_num,
                "vendor": po.get("vendor", ""),
                "date": po.get("date", ""),
                "ship_to": po.get("ship_to", ""),
                "total": po.get("total", 0),
                "items": po.get("items", []),
            }
            total_items += len(po.get("items", []))
            count += 1

        return {
            "success": True,
            "message": "Extracted " + str(count) + " purchase order(s) with " + str(total_items) + " line items from document.",
            "data": po_list,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_admin_html(purchase_orders):
    """Generate the Purchase Orders admin page with unified smart upload."""

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

        .file-mode-badge {
            display: inline-block; padding: 3px 8px; border-radius: 4px;
            font-size: 10px; font-weight: 700; text-transform: uppercase;
            margin-left: 8px;
        }
        .file-mode-badge.csv-mode { background: #ECFDF5; color: #059669; }
        .file-mode-badge.ai-mode { background: #FEF3C7; color: #D97706; }

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

        /* PO Table */
        .po-table-section {
            background: white; border-radius: 16px; border: 1px solid #E2E8F0;
            padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .po-table-section h2 { font-size: 18px; font-weight: 700; color: #0F172A; margin-bottom: 4px; }
        .po-table-section .subtitle { font-size: 13px; color: #64748B; margin-bottom: 20px; }
        .po-table {
            width: 100%; border-collapse: collapse;
        }
        .po-table th {
            text-align: left; padding: 10px 14px; font-size: 11px; font-weight: 600;
            color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;
            border-bottom: 2px solid #E2E8F0; background: #F8FAFC;
        }
        .po-table td {
            padding: 12px 14px; font-size: 13px; color: #334155;
            border-bottom: 1px solid #F1F5F9;
        }
        .po-table tr:hover td { background: #F8FAFC; }
        .po-badge {
            display: inline-block; padding: 3px 10px; border-radius: 6px;
            font-size: 11px; font-weight: 600; background: #EEF2FF; color: #4F46E5;
        }
        .empty-state {
            text-align: center; padding: 48px 24px; color: #94A3B8;
        }
        .empty-state-icon { font-size: 48px; margin-bottom: 12px; }
        .empty-state-text { font-size: 15px; font-weight: 500; }
        .empty-state-sub { font-size: 13px; margin-top: 4px; }

        @media (max-width: 768px) {
            .stat-grid { grid-template-columns: 1fr; }
        }
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

            <!-- Unified Upload Section -->
            <div class="upload-section">
                <h2>Upload Purchase Orders</h2>
                <p class="subtitle">Drop any PO document &mdash; we'll automatically detect the format and extract the data</p>

                <div class="tip-box">
                    <div class="tip-box-title">&#128161; Supported Formats:</div>
                    <ul>
                        <li><strong>PDF</strong> &mdash; Digital or scanned purchase orders (AI-powered extraction)</li>
                        <li><strong>Images</strong> (JPG, PNG) &mdash; Photos of printed POs (AI-powered extraction)</li>
                        <li><strong>CSV / TSV</strong> &mdash; Spreadsheet exports from your ERP (direct import)</li>
                    </ul>
                </div>

                <input type="file" id="poFileInput" class="file-input"
                       accept=".pdf,.jpg,.jpeg,.png,.csv,.tsv,.heic,.gif,.webp,.tiff,.tif,.bmp">

                <div class="drop-zone" id="poDropZone">
                    <div class="drop-zone-icon">&#128203;</div>
                    <div class="drop-zone-text">Drop your PO document here</div>
                    <div class="drop-zone-sub">or click to browse &bull; Any format accepted</div>
                    <div class="file-types">
                        <span class="file-type-badge">PDF</span>
                        <span class="file-type-badge">JPG</span>
                        <span class="file-type-badge">PNG</span>
                        <span class="file-type-badge">CSV</span>
                        <span class="file-type-badge">TSV</span>
                        <span class="file-type-badge">HEIC</span>
                    </div>
                </div>

                <div class="selected-file" id="poSelectedFile">
                    <span>&#128196;</span>
                    <span id="poFileName">document.pdf</span>
                    <span class="file-mode-badge" id="poModeBadge"></span>
                    <span class="selected-file-remove" id="poRemoveFile">&times;</span>
                </div>

                <button class="upload-btn" id="poUploadBtn" disabled>
                    &#128640; Upload &amp; Process
                </button>

                <div class="loading-spinner" id="poLoading">
                    <div class="spinner"></div>
                    <div class="loading-text" id="poLoadingText">Processing...</div>
                </div>
                <div class="status-msg" id="poStatus"></div>
            </div>

            <!-- PO Table -->
            <div class="po-table-section">
                <h2>Loaded Purchase Orders</h2>
                <p class="subtitle">"""
        + str(total_pos)
        + """ purchase orders with """
        + str(total_items)
        + """ line items</p>
"""
        + _build_po_table(purchase_orders)
        + """
            </div>
        </div>
    </div>

    <script>
        /* --- Unified Upload Logic --- */
        var poFile = null;
        var poFileType = 'unknown';  /* 'csv', 'tsv', or 'document' */
        var poDropZone = document.getElementById('poDropZone');
        var poFileInput = document.getElementById('poFileInput');

        poDropZone.addEventListener('click', function() { poFileInput.click(); });
        poDropZone.addEventListener('dragover', function(e) {
            e.preventDefault(); poDropZone.classList.add('drag-over');
        });
        poDropZone.addEventListener('dragleave', function() { poDropZone.classList.remove('drag-over'); });
        poDropZone.addEventListener('drop', function(e) {
            e.preventDefault(); poDropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length) handlePoFile(e.dataTransfer.files[0]);
        });
        poFileInput.addEventListener('change', function() {
            if (poFileInput.files.length) handlePoFile(poFileInput.files[0]);
        });

        function detectFileType(filename) {
            var ext = filename.toLowerCase().split('.').pop();
            if (ext === 'csv') return 'csv';
            if (ext === 'tsv') return 'tsv';
            return 'document';
        }

        function handlePoFile(file) {
            poFile = file;
            poFileType = detectFileType(file.name);

            document.getElementById('poFileName').textContent = file.name;
            document.getElementById('poSelectedFile').classList.add('show');
            poDropZone.style.display = 'none';

            /* Show mode badge */
            var badge = document.getElementById('poModeBadge');
            if (poFileType === 'csv' || poFileType === 'tsv') {
                badge.textContent = 'Direct Import';
                badge.className = 'file-mode-badge csv-mode';
            } else {
                badge.textContent = 'AI Extraction';
                badge.className = 'file-mode-badge ai-mode';
            }

            /* Update button label */
            var btn = document.getElementById('poUploadBtn');
            if (poFileType === 'csv' || poFileType === 'tsv') {
                btn.innerHTML = '&#128640; Upload &amp; Process ' + poFileType.toUpperCase();
            } else {
                btn.innerHTML = '&#129302; Upload &amp; Extract with AI';
            }
            btn.disabled = false;
        }

        document.getElementById('poRemoveFile').addEventListener('click', function() {
            poFile = null;
            poFileType = 'unknown';
            document.getElementById('poSelectedFile').classList.remove('show');
            poDropZone.style.display = 'block';
            document.getElementById('poUploadBtn').disabled = true;
            document.getElementById('poUploadBtn').innerHTML = '&#128640; Upload &amp; Process';
            poFileInput.value = '';
        });

        document.getElementById('poUploadBtn').addEventListener('click', function() {
            if (!poFile) return;
            var btn = document.getElementById('poUploadBtn');
            var loading = document.getElementById('poLoading');
            var loadingText = document.getElementById('poLoadingText');
            var status = document.getElementById('poStatus');

            btn.disabled = true;
            loading.classList.add('show');
            status.classList.remove('show');

            /* Set loading text based on file type */
            if (poFileType === 'csv' || poFileType === 'tsv') {
                loadingText.textContent = 'Processing ' + poFileType.toUpperCase() + ' file...';
            } else {
                loadingText.textContent = 'Analyzing document with AI... This may take a few seconds';
            }

            var fd = new FormData();
            fd.append('file', poFile);

            /* Route to correct endpoint based on type */
            var endpoint = '/api/upload-po';

            fetch(endpoint, { method: 'POST', body: fd })
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


def _build_po_table(purchase_orders):
    """Build the PO table HTML or empty state."""
    if not purchase_orders:
        return """
                <div class="empty-state">
                    <div class="empty-state-icon">&#128203;</div>
                    <div class="empty-state-text">No purchase orders loaded yet</div>
                    <div class="empty-state-sub">Upload a CSV, PDF, or photo above to get started</div>
                </div>
"""

    rows = ""
    for po_num, po in purchase_orders.items():
        vendor = po.get("vendor", "N/A")
        item_count = len(po.get("items", []))
        date = po.get("date", "")
        total = po.get("total", 0)

        total_display = ""
        if total and float(total) > 0:
            total_display = "$" + "{:,.2f}".format(float(total))
        else:
            # Try to calculate from items
            calc_total = 0
            for item in po.get("items", []):
                try:
                    qty = float(item.get("quantity", 0))
                    price = float(item.get("unit_price", 0))
                    calc_total += qty * price
                except (ValueError, TypeError):
                    pass
            if calc_total > 0:
                total_display = "$" + "{:,.2f}".format(calc_total)
            else:
                total_display = "&mdash;"

        rows += (
            """
                    <tr>
                        <td><span class="po-badge">"""
            + str(po_num)
            + """</span></td>
                        <td>"""
            + str(vendor)
            + """</td>
                        <td>"""
            + str(item_count)
            + """</td>
                        <td>"""
            + str(date if date else "&mdash;")
            + """</td>
                        <td>"""
            + total_display
            + """</td>
                    </tr>"""
        )

    return (
        """
                <table class="po-table">
                    <thead>
                        <tr>
                            <th>PO Number</th>
                            <th>Vendor</th>
                            <th>Line Items</th>
                            <th>Date</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>"""
        + rows
        + """
                    </tbody>
                </table>
"""
    )
