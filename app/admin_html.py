def get_admin_html():
    """Generate admin page HTML for uploading PO CSV"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin - FQHC 3-Way Match</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1a202c;
            font-size: 28px;
            margin-bottom: 8px;
        }
        .subtitle {
            color: #718096;
            font-size: 14px;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .card h2 {
            color: #2d3748;
            font-size: 20px;
            margin-bottom: 20px;
        }
        .upload-area {
            border: 2px dashed #cbd5e0;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            background: #f7fafc;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover {
            border-color: #667eea;
            background: #edf2f7;
        }
        .upload-area.dragover {
            border-color: #667eea;
            background: #e6fffa;
        }
        input[type="file"] {
            display: none;
        }
        .btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 16px;
        }
        .btn:hover {
            background: #5a67d8;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        .btn:disabled {
            background: #cbd5e0;
            cursor: not-allowed;
            transform: none;
        }
        .btn-secondary {
            background: #48bb78;
        }
        .btn-secondary:hover {
            background: #38a169;
        }
        .message {
            padding: 12px 16px;
            border-radius: 6px;
            margin-top: 16px;
            display: none;
        }
        .message.success {
            background: #c6f6d5;
            color: #22543d;
            border-left: 4px solid #48bb78;
        }
        .message.error {
            background: #fed7d7;
            color: #742a2a;
            border-left: 4px solid #f56565;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }
        .stat-box {
            background: #f7fafc;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .stat-label {
            color: #718096;
            font-size: 14px;
            margin-bottom: 8px;
        }
        .stat-value {
            color: #2d3748;
            font-size: 32px;
            font-weight: bold;
        }
        .instructions {
            background: #fffbeb;
            border-left: 4px solid #f6ad55;
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 20px;
        }
        .instructions h3 {
            color: #744210;
            font-size: 16px;
            margin-bottom: 12px;
        }
        .instructions ol {
            color: #744210;
            margin-left: 20px;
        }
        .instructions li {
            margin-bottom: 8px;
        }
        .nav-link {
            display: inline-block;
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            margin-top: 16px;
        }
        .nav-link:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 Admin Panel</h1>
            <p class="subtitle">Upload and manage purchase order data</p>
        </div>

        <div class="card">
            <h2>📊 Current Status</h2>
            <div class="stats" id="stats">
                <div class="stat-box">
                    <div class="stat-label">POs Loaded</div>
                    <div class="stat-value" id="po-count">Loading...</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Line Items</div>
                    <div class="stat-value" id="item-count">Loading...</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Vendors</div>
                    <div class="stat-value" id="vendor-count">Loading...</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📤 Upload Netsuite PO Export</h2>
            
            <div class="instructions">
                <h3>How to export from Netsuite:</h3>
                <ol>
                    <li>Go to Netsuite → Transactions → Purchase Orders</li>
                    <li>Filter for "Open" or "Pending Receipt" POs</li>
                    <li>Click "Export to CSV"</li>
                    <li>Make sure columns include: PO Number, Vendor, Item, Description, Quantity Ordered, Unit Price</li>
                    <li>Upload the CSV file below</li>
                </ol>
            </div>

            <div class="upload-area" id="upload-area">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" style="margin: 0 auto; color: #a0aec0;">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="17 8 12 3 7 8"></polyline>
                    <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
                <p style="margin-top: 16px; color: #4a5568;">Drop CSV file here or click to browse</p>
                <p style="margin-top: 8px; color: #a0aec0; font-size: 14px;">Accepts .csv files</p>
                <input type="file" id="file-input" accept=".csv">
            </div>

            <button class="btn" id="upload-btn" disabled>Upload CSV</button>
            
            <div class="message" id="message"></div>
        </div>

        <div class="card">
            <a href="/" class="nav-link">← Back to Dashboard</a>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        const uploadBtn = document.getElementById('upload-btn');
        const message = document.getElementById('message');
        let selectedFile = null;

        // Load current stats
        async function loadStats() {
            try {
                const response = await fetch('/api/po-stats');
                const data = await response.json();
                document.getElementById('po-count').textContent = data.po_count || 0;
                document.getElementById('item-count').textContent = data.line_item_count || 0;
                document.getElementById('vendor-count').textContent = data.vendor_count || 0;
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }

        // Click to browse
        uploadArea.addEventListener('click', () => fileInput.click());

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                selectedFile = files[0];
                fileInput.files = files;
                updateUI();
            }
        });

        // File selected
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                selectedFile = e.target.files[0];
                updateUI();
            }
        });

        function updateUI() {
            if (selectedFile) {
                uploadArea.querySelector('p').textContent = `Selected: ${selectedFile.name}`;
                uploadBtn.disabled = false;
            }
        }

        // Upload
        uploadBtn.addEventListener('click', async () => {
            if (!selectedFile) return;

            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Uploading...';
            message.style.display = 'none';

            const formData = new FormData();
            formData.append('file', selectedFile);

            try {
                const response = await fetch('/api/upload-po-csv', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    message.className = 'message success';
                    message.textContent = data.message;
                    message.style.display = 'block';
                    
                    // Reload stats
                    setTimeout(loadStats, 1000);
                    
                    // Reset
                    selectedFile = null;
                    fileInput.value = '';
                    uploadArea.querySelector('p').textContent = 'Drop CSV file here or click to browse';
                } else {
                    throw new Error(data.detail || 'Upload failed');
                }
            } catch (error) {
                message.className = 'message error';
                message.textContent = `Error: ${error.message}`;
                message.style.display = 'block';
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload CSV';
            }
        });

        // Load stats on page load
        loadStats();
    </script>
</body>
</html>
    """
