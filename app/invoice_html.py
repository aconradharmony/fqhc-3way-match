def get_invoice_html():
    """Generate invoice upload and management page"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invoice Management - FQHC 3-Way Match</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #2d3748;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: relative;
        }
        .dashboard-link {
            position: absolute;
            top: 2rem;
            right: 2rem;
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s;
        }
        .dashboard-link:hover {
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        h2 {
            color: #2d3748;
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
        }
        .upload-area {
            border: 2px dashed #cbd5e0;
            border-radius: 8px;
            padding: 3rem;
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
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 1rem;
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
        .message {
            padding: 1rem;
            border-radius: 6px;
            margin-top: 1rem;
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
        .message.warning {
            background: #feebc8;
            color: #744210;
            border-left: 4px solid #ed8936;
        }
        .info-box {
            background: #ebf8ff;
            border-left: 4px solid #4299e1;
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 2rem;
        }
        .info-box h3 {
            color: #2c5282;
            font-size: 1rem;
            margin-bottom: 0.5rem;
        }
        .info-box p {
            color: #2c5282;
            font-size: 0.9rem;
        }
        .invoice-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1.5rem;
        }
        .invoice-table th {
            background: #f7fafc;
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
            color: #4a5568;
            border-bottom: 2px solid #e2e8f0;
        }
        .invoice-table td {
            padding: 0.75rem;
            border-bottom: 1px solid #e2e8f0;
        }
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .status-badge.approved {
            background: #c6f6d5;
            color: #22543d;
        }
        .status-badge.review {
            background: #feebc8;
            color: #744210;
        }
        .status-badge.reject {
            background: #fed7d7;
            color: #742a2a;
        }
        .status-badge.pending {
            background: #e6fffa;
            color: #234e52;
        }
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: #a0aec0;
        }
    </style>
</head>
<body>
    <div class="header">
        <a href="/" class="dashboard-link">📊 Dashboard</a>
        <h1>💰 Invoice Management</h1>
        <p>Upload and verify invoices against POs and packing slips</p>
    </div>

    <div class="container">
        <div class="card">
            <h2>📤 Upload Invoice</h2>
            
            <div class="info-box">
                <h3>💡 How 3-Way Matching Works</h3>
                <p>The system compares your invoice against the PO (what you ordered) and packing slip (what you received). 
                   It will flag discrepancies like price differences, quantity mismatches, or items you're being billed 
                   for that you didn't receive.</p>
            </div>

            <div class="upload-area" id="upload-area">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" style="margin: 0 auto; color: #a0aec0;">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="12" y1="18" x2="12" y2="12"></line>
                    <line x1="9" y1="15" x2="15" y2="15"></line>
                </svg>
                <p style="margin-top: 1rem; color: #4a5568; font-weight: 500;">Drop invoice PDF or photo here</p>
                <p style="margin-top: 0.5rem; color: #a0aec0; font-size: 0.9rem;">Accepts PDF, JPG, PNG files</p>
                <input type="file" id="file-input" accept=".pdf,.jpg,.jpeg,.png">
            </div>

            <button class="btn" id="upload-btn" disabled>Upload Invoice</button>
            
            <div class="message" id="message"></div>
        </div>

        <div class="card">
            <h2>📋 Recent Invoices</h2>
            <table class="invoice-table" id="invoice-table">
                <thead>
                    <tr>
                        <th>Invoice #</th>
                        <th>PO #</th>
                        <th>Vendor</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Uploaded</th>
                    </tr>
                </thead>
                <tbody id="invoice-tbody">
                    <tr>
                        <td colspan="6" class="empty-state">
                            No invoices uploaded yet. Upload one above to get started! 📄
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        const uploadBtn = document.getElementById('upload-btn');
        const message = document.getElementById('message');
        let selectedFile = null;

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
            uploadBtn.textContent = 'Processing...';
            message.style.display = 'none';

            const formData = new FormData();
            formData.append('file', selectedFile);

            try {
                const response = await fetch('/api/upload-invoice', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (response.ok) {
                    if (data.match_status === 'APPROVE') {
                        message.className = 'message success';
                        message.textContent = `✓ ${data.message}`;
                    } else if (data.match_status === 'REVIEW') {
                        message.className = 'message warning';
                        message.textContent = `⚠ ${data.message}`;
                    } else {
                        message.className = 'message error';
                        message.textContent = `✗ ${data.message}`;
                    }
                    message.style.display = 'block';
                    
                    // Reload invoice list
                    setTimeout(loadInvoices, 1000);
                    
                    // Reset
                    selectedFile = null;
                    fileInput.value = '';
                    uploadArea.querySelector('p').textContent = 'Drop invoice PDF or photo here';
                } else {
                    throw new Error(data.detail || 'Upload failed');
                }
            } catch (error) {
                message.className = 'message error';
                message.textContent = `Error: ${error.message}`;
                message.style.display = 'block';
            } finally {
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload Invoice';
            }
        });

        // Load invoices
        async function loadInvoices() {
            try {
                const response = await fetch('/api/invoices');
                const invoices = await response.json();
                
                const tbody = document.getElementById('invoice-tbody');
                
                if (invoices.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No invoices uploaded yet. Upload one above to get started! 📄</td></tr>';
                    return;
                }
                
                tbody.innerHTML = invoices.map(inv => `
                    <tr>
                        <td><strong>${inv.invoice_number || 'N/A'}</strong></td>
                        <td>${inv.po_number || 'N/A'}</td>
                        <td>${inv.vendor || 'N/A'}</td>
                        <td>$${inv.total_amount ? inv.total_amount.toFixed(2) : '0.00'}</td>
                        <td><span class="status-badge ${inv.match_status.toLowerCase()}">${inv.match_status}</span></td>
                        <td>${new Date(inv.timestamp).toLocaleString()}</td>
                    </tr>
                `).join('');
            } catch (error) {
                console.error('Failed to load invoices:', error);
            }
        }

        // Load on page load
        loadInvoices();
    </script>
</body>
</html>
    """
