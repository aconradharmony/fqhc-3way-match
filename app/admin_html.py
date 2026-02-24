def get_admin_html():
    """Generate modern admin page HTML for managing POs"""
    from .sidebar_component import get_sidebar_html, get_sidebar_styles
    
    sidebar_html = get_sidebar_html("admin")
    sidebar_styles = get_sidebar_styles()
    
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Purchase Orders - VerifyAP</title>
    """ + sidebar_styles + """
    <style>
        /* CARDS */
        .card {
            background: white;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        .card-header {
            margin-bottom: 20px;
        }
        
        .card-title {
            font-size: 18px;
            font-weight: 600;
            color: #0F172A;
            margin-bottom: 4px;
        }
        
        .card-subtitle {
            font-size: 14px;
            color: #64748B;
        }
        
        /* STATS GRID */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 32px;
        }
        
        .stat-card {
            background: white;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            padding: 20px;
            transition: all 0.2s;
        }
        
        .stat-card:hover {
            border-color: #4F46E5;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1);
            transform: translateY(-2px);
        }
        
        .stat-label {
            font-size: 13px;
            font-weight: 500;
            color: #64748B;
            margin-bottom: 8px;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #0F172A;
        }
        
        .stat-value.success {
            color: #10B981;
        }
        
        /* UPLOAD AREA */
        .upload-area {
            border: 2px dashed #E2E8F0;
            border-radius: 12px;
            padding: 48px;
            text-align: center;
            background: #F8FAFC;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .upload-area:hover {
            border-color: #4F46E5;
            background: #EEF2FF;
        }
        
        .upload-area.dragover {
            border-color: #4F46E5;
            background: #E0E7FF;
        }
        
        /* INFO BOX */
        .info-box {
            background: #EFF6FF;
            border-left: 4px solid #3B82F6;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 24px;
        }
        
        .info-box h3 {
            color: #1E40AF;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .info-box ul {
            margin-left: 20px;
            color: #1E40AF;
            font-size: 13px;
        }
        
        .info-box li {
            margin: 4px 0;
        }
        
        /* BUTTONS */
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
        }
        
        .btn-primary {
            background: #4F46E5;
            color: white;
        }
        
        .btn-primary:hover {
            background: #4338CA;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }
        
        .btn-primary:disabled {
            background: #CBD5E1;
            cursor: not-allowed;
            transform: none;
        }
        
        /* MESSAGE */
        .message {
            padding: 12px 16px;
            border-radius: 8px;
            margin-top: 16px;
            display: none;
        }
        
        .message.success {
            background: #D1FAE5;
            color: #065F46;
            border-left: 4px solid #10B981;
        }
        
        .message.error {
            background: #FEE2E2;
            color: #991B1B;
            border-left: 4px solid #EF4444;
        }
        
        /* CONTAINER */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 32px;
        }
        
        .page-header {
            margin-bottom: 32px;
        }
        
        .page-title {
            font-size: 28px;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 8px;
        }
        
        .page-subtitle {
            font-size: 14px;
            color: #64748B;
        }
    </style>
</head>
<body>
    """ + sidebar_html + """
    
    <div class="verifyap-main-content">
        <div class="container">
            <div class="page-header">
                <h1 class="page-title">Purchase Orders</h1>
                <p class="page-subtitle">NetSuite integration & PO management</p>
            </div>
            
            <!-- Data Health Stats -->
            <div class="stats-grid" id="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Active POs</div>
                    <div class="stat-value success">0</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Line Items</div>
                    <div class="stat-value">0</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Active Vendors</div>
                    <div class="stat-value">0</div>
                </div>
            </div>
            
            <!-- Upload Card -->
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Upload NetSuite CSV</h2>
                    <p class="card-subtitle">Import purchase orders from NetSuite export</p>
                </div>
                
                <div class="info-box">
                    <h3>📋 How to export from NetSuite:</h3>
                    <ul>
                        <li>Go to Reports → Saved Searches → Open POs</li>
                        <li>Click "Export" → CSV format</li>
                        <li>Ensure columns include: PO Number, Vendor, Item Description, Quantity, Unit Price</li>
                        <li>Upload the .csv file below</li>
                    </ul>
                </div>
                
                <div class="upload-area" id="upload-area">
                    <div style="font-size: 48px; margin-bottom: 16px;">📊</div>
                    <p style="font-size: 16px; font-weight: 600; color: #0F172A; margin-bottom: 8px;">
                        Drop CSV file here
                    </p>
                    <p style="font-size: 14px; color: #64748B; margin-bottom: 16px;">
                        or click to browse • Accepts .csv files
                    </p>
                    <input type="file" id="file-input" accept=".csv" style="display: none;">
                    <button class="btn btn-primary" id="upload-btn" disabled>
                        <span>📤</span>
                        <span>Upload & Process CSV</span>
                    </button>
                </div>
                
                <div class="message" id="message"></div>
            </div>
            
            <!-- Instructions Card -->
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">💡 Tips for Best Results</h2>
                </div>
                
                <div style="font-size: 14px; color: #334155; line-height: 1.6;">
                    <p style="margin-bottom: 12px;">
                        <strong>Required CSV Columns:</strong><br>
                        The CSV must include these columns (exact names may vary):
                    </p>
                    <ul style="margin-left: 20px; margin-bottom: 16px;">
                        <li>PO Number / Purchase Order #</li>
                        <li>Vendor Name / Supplier</li>
                        <li>Item / Description</li>
                        <li>Quantity Ordered / Qty</li>
                        <li>Unit Price / Price</li>
                    </ul>
                    <p style="margin-bottom: 12px;">
                        <strong>CSV Format Tips:</strong>
                    </p>
                    <ul style="margin-left: 20px;">
                        <li>Keep headers in the first row</li>
                        <li>One line item per row</li>
                        <li>Remove any summary rows or totals</li>
                        <li>Ensure numeric values don't have currency symbols</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        const uploadBtn = document.getElementById('upload-btn');
        const message = document.getElementById('message');
        let selectedFile = null;
        
        // Click to browse
        uploadArea.addEventListener('click', (e) => {
            if (e.target.tagName !== 'BUTTON') fileInput.click();
        });
        
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
                handleFile(files[0]);
            }
        });
        
        // File selected
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
        
        function handleFile(file) {
            if (!file.name.endsWith('.csv')) {
                message.className = 'message error';
                message.textContent = '❌ Please select a CSV file';
                message.style.display = 'block';
                return;
            }
            
            selectedFile = file;
            uploadArea.querySelector('p').textContent = `Selected: ${file.name}`;
            uploadBtn.disabled = false;
            message.style.display = 'none';
        }
        
        // Upload
        uploadBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            
            uploadBtn.disabled = true;
            uploadBtn.textContent = '⏳ Processing...';
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
                    message.textContent = `✓ ${data.message || 'CSV uploaded successfully!'}`;
                    message.style.display = 'block';
                    
                    // Reload stats
                    setTimeout(loadStats, 1000);
                    
                    // Reset
                    selectedFile = null;
                    fileInput.value = '';
                    uploadArea.querySelector('p').textContent = 'Drop CSV file here';
                    uploadBtn.disabled = true;
                    uploadBtn.innerHTML = '<span>📤</span><span>Upload & Process CSV</span>';
                } else {
                    throw new Error(data.detail || 'Upload failed');
                }
            } catch (error) {
                message.className = 'message error';
                message.textContent = `❌ Error: ${error.message}`;
                message.style.display = 'block';
                uploadBtn.disabled = false;
                uploadBtn.innerHTML = '<span>📤</span><span>Upload & Process CSV</span>';
            }
        });
        
        // Load stats
        async function loadStats() {
            try {
                const response = await fetch('/api/po-stats');
                const data = await response.json();
                
                const statsHTML = `
                    <div class="stat-card">
                        <div class="stat-label">Active POs</div>
                        <div class="stat-value success">${data.po_count || 0}</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Line Items</div>
                        <div class="stat-value">${data.line_item_count || 0}</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-label">Active Vendors</div>
                        <div class="stat-value">${data.vendor_count || 0}</div>
                    </div>
                `;
                
                document.getElementById('stats-grid').innerHTML = statsHTML;
            } catch (error) {
                console.error('Failed to load stats:', error);
            }
        }
        
        // Load on page load
        loadStats();
    </script>
</body>
</html>
    """
    
    return html
