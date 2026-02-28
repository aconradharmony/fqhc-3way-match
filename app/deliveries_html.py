"""
VerifyAP - Deliveries Page
Created: Feb 26, 2026
Purpose: Dedicated page for uploading and reviewing packing slips / delivery receipts.
Supports PDF, JPG, PNG, HEIC uploads.
"""

from .sidebar_component import get_sidebar_html, get_sidebar_styles


def get_deliveries_html():
    """Generate the Deliveries page HTML."""

    sidebar_html = get_sidebar_html("deliveries")
    sidebar_styles = get_sidebar_styles()

    html = (
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VerifyAP - Deliveries</title>
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
        .page-header h1 {
            font-size: 28px; font-weight: 800; letter-spacing: -0.5px;
            display: flex; align-items: center; gap: 10px;
        }
        .page-header p {
            margin-top: 4px; font-size: 14px;
            color: rgba(255,255,255,0.75); font-weight: 400;
        }

        .page-body { padding: 32px 40px; max-width: 960px; }

        .upload-card {
            background: white;
            border-radius: 16px;
            border: 1px solid #E2E8F0;
            padding: 32px;
            margin-bottom: 28px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .upload-card h2 {
            font-size: 18px; font-weight: 700; color: #0F172A; margin-bottom: 4px;
        }
        .upload-card .subtitle {
            font-size: 13px; color: #64748B; margin-bottom: 24px;
        }

        .drop-zone {
            border: 2px dashed #CBD5E1;
            border-radius: 12px;
            padding: 48px 24px;
            text-align: center;
            background: #F8FAFC;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-bottom: 20px;
        }
        .drop-zone:hover, .drop-zone.drag-over {
            border-color: #4F46E5;
            background: #EEF2FF;
        }
        .drop-zone-icon { font-size: 48px; margin-bottom: 12px; }
        .drop-zone-text { font-size: 15px; font-weight: 600; color: #334155; margin-bottom: 4px; }
        .drop-zone-sub { font-size: 13px; color: #94A3B8; }

        .file-types {
            display: flex; gap: 8px; justify-content: center; margin-top: 12px; flex-wrap: wrap;
        }
        .file-type-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            background: #EEF2FF;
            color: #4F46E5;
            text-transform: uppercase;
        }

        .upload-btn {
            display: inline-flex; align-items: center; gap: 8px;
            padding: 12px 28px;
            background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
            color: white; border: none; border-radius: 8px;
            font-size: 14px; font-weight: 600; cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(79,70,229,0.3);
        }
        .upload-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(79,70,229,0.4);
        }
        .upload-btn:disabled {
            opacity: 0.5; cursor: not-allowed; transform: none;
        }

        .file-input { display: none; }

        .selected-file {
            display: none;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            background: #EEF2FF;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 13px;
            color: #4F46E5;
            font-weight: 500;
        }
        .selected-file.show { display: flex; }
        .selected-file-icon { font-size: 18px; }
        .selected-file-remove {
            margin-left: auto;
            cursor: pointer;
            color: #94A3B8;
            font-size: 16px;
        }
        .selected-file-remove:hover { color: #EF4444; }

        /* Results area */
        .results-area { display: none; margin-top: 28px; }
        .results-area.show { display: block; }

        .result-card {
            background: white;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            padding: 24px;
            margin-bottom: 16px;
        }
        .result-card h3 { font-size: 16px; font-weight: 700; margin-bottom: 12px; }

        .result-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .badge-approve { background: #ECFDF5; color: #059669; }
        .badge-review { background: #FFFBEB; color: #D97706; }
        .badge-reject { background: #FEF2F2; color: #DC2626; }

        .result-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            font-size: 13px;
        }
        .result-table th {
            text-align: left;
            padding: 10px 12px;
            background: #F8FAFC;
            border-bottom: 2px solid #E2E8F0;
            font-weight: 600;
            color: #64748B;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .result-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #F1F5F9;
            color: #334155;
        }

        .loading-spinner {
            display: none;
            text-align: center;
            padding: 32px;
        }
        .loading-spinner.show { display: block; }
        .spinner {
            width: 40px; height: 40px;
            border: 3px solid #E2E8F0;
            border-top: 3px solid #4F46E5;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 12px auto;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading-text { font-size: 14px; color: #64748B; font-weight: 500; }

        .error-msg {
            display: none;
            padding: 16px;
            background: #FEF2F2;
            border: 1px solid #FECACA;
            border-radius: 8px;
            color: #DC2626;
            font-size: 13px;
            margin-top: 12px;
        }
        .error-msg.show { display: block; }
    </style>
</head>
<body>
    """
        + sidebar_html
        + """
    <div class="verifyap-main-content">
        <div class="page-header">
            <h1>&#128230; Deliveries</h1>
            <p>Upload packing slips and delivery receipts to verify against purchase orders</p>
        </div>

        <div class="page-body">
            <div class="upload-card">
                <h2>Upload Packing Slip</h2>
                <p class="subtitle">Take or upload a photo/PDF to verify against purchase orders</p>

                <input type="file" id="fileInput" class="file-input"
                       accept=".pdf,.jpg,.jpeg,.png,.heic">

                <div class="drop-zone" id="dropZone">
                    <div class="drop-zone-icon">&#128230;</div>
                    <div class="drop-zone-text">Drop packing slip here</div>
                    <div class="drop-zone-sub">or click to browse</div>
                    <div class="file-types">
                        <span class="file-type-badge">PDF</span>
                        <span class="file-type-badge">JPG</span>
                        <span class="file-type-badge">PNG</span>
                        <span class="file-type-badge">HEIC</span>
                    </div>
                </div>

                <div class="selected-file" id="selectedFile">
                    <span class="selected-file-icon">&#128196;</span>
                    <span id="selectedFileName">file.jpg</span>
                    <span class="selected-file-remove" id="removeFile">&times;</span>
                </div>

                <button class="upload-btn" id="uploadBtn" disabled>
                    &#128666; Upload &amp; Process
                </button>

                <div class="loading-spinner" id="loadingSpinner">
                    <div class="spinner"></div>
                    <div class="loading-text">Analyzing packing slip with AI...</div>
                </div>

                <div class="error-msg" id="errorMsg"></div>
            </div>

            <div class="results-area" id="resultsArea"></div>
        </div>
    </div>

    <script>
        var selectedFileData = null;

        var dropZone = document.getElementById('dropZone');
        var fileInput = document.getElementById('fileInput');
        var uploadBtn = document.getElementById('uploadBtn');
        var selectedFile = document.getElementById('selectedFile');
        var selectedFileName = document.getElementById('selectedFileName');
        var removeFileBtn = document.getElementById('removeFile');
        var loadingSpinner = document.getElementById('loadingSpinner');
        var errorMsg = document.getElementById('errorMsg');
        var resultsArea = document.getElementById('resultsArea');

        dropZone.addEventListener('click', function() { fileInput.click(); });

        dropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });
        dropZone.addEventListener('dragleave', function() {
            dropZone.classList.remove('drag-over');
        });
        dropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                handleFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                handleFile(fileInput.files[0]);
            }
        });

        function handleFile(file) {
            selectedFileData = file;
            selectedFileName.textContent = file.name + ' (' + (file.size / 1024).toFixed(1) + ' KB)';
            selectedFile.classList.add('show');
            dropZone.style.display = 'none';
            uploadBtn.disabled = false;
            errorMsg.classList.remove('show');
        }

        removeFileBtn.addEventListener('click', function() {
            selectedFileData = null;
            selectedFile.classList.remove('show');
            dropZone.style.display = 'block';
            uploadBtn.disabled = true;
            fileInput.value = '';
        });

        uploadBtn.addEventListener('click', function() {
            if (!selectedFileData) return;

            uploadBtn.disabled = true;
            loadingSpinner.classList.add('show');
            errorMsg.classList.remove('show');
            resultsArea.classList.remove('show');

            var formData = new FormData();
            formData.append('file', selectedFileData);

            fetch('/api/upload-packing-slip', {
                method: 'POST',
                body: formData
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                loadingSpinner.classList.remove('show');
                if (data.success) {
                    displayResults(data);
                } else {
                    errorMsg.textContent = 'Error: ' + (data.error || 'Unknown error');
                    errorMsg.classList.add('show');
                }
                uploadBtn.disabled = false;
            })
            .catch(function(err) {
                loadingSpinner.classList.remove('show');
                errorMsg.textContent = 'Network error: ' + err.message;
                errorMsg.classList.add('show');
                uploadBtn.disabled = false;
            });
        });

        function displayResults(data) {
            var d = data.data || {};
            var m = data.match || {};
            var status = (m.status || 'REVIEW').toUpperCase();
            var badgeClass = status === 'APPROVE' ? 'badge-approve' : status === 'REJECT' ? 'badge-reject' : 'badge-review';

            var html = '<div class="result-card">';
            html += '<h3>Extraction Results <span class="result-badge ' + badgeClass + '">' + status + '</span></h3>';

            html += '<table class="result-table">';
            html += '<tr><th>Field</th><th>Value</th></tr>';
            html += '<tr><td>PO Number</td><td>' + (d.po_number || 'N/A') + '</td></tr>';
            html += '<tr><td>Vendor</td><td>' + (d.vendor || 'N/A') + '</td></tr>';
            html += '<tr><td>Date</td><td>' + (d.date || 'N/A') + '</td></tr>';
            html += '</table>';

            if (d.items && d.items.length > 0) {
                html += '<h3 style="margin-top:20px;">Line Items</h3>';
                html += '<table class="result-table">';
                html += '<tr><th>Description</th><th>Qty</th></tr>';
                for (var i = 0; i < d.items.length; i++) {
                    html += '<tr><td>' + (d.items[i].description || d.items[i].item || 'N/A') + '</td>';
                    html += '<td>' + (d.items[i].quantity || 'N/A') + '</td></tr>';
                }
                html += '</table>';
            }

            if (m.discrepancies && m.discrepancies.length > 0) {
                html += '<h3 style="margin-top:20px;">Discrepancies</h3>';
                html += '<table class="result-table">';
                html += '<tr><th>Issue</th><th>Details</th></tr>';
                for (var j = 0; j < m.discrepancies.length; j++) {
                    html += '<tr><td>' + (m.discrepancies[j].type || 'Issue') + '</td>';
                    html += '<td>' + (m.discrepancies[j].message || m.discrepancies[j].detail || '') + '</td></tr>';
                }
                html += '</table>';
            }

            html += '</div>';
            resultsArea.innerHTML = html;
            resultsArea.classList.add('show');
        }
    </script>
</body>
</html>"""
    )

    return html
