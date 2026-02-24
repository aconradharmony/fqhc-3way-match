"""
FQHC 3-Way Match System - Main FastAPI Application
Handles packing slip uploads, vision processing, and PO matching
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import anthropic
import os
import base64
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional
from .po_matcher import POManager, MatchResult
from .vision_prompt import get_vision_prompt
from .admin_html import get_admin_html
from .invoice_html import get_invoice_html
from .invoice_vision_prompt import get_invoice_vision_prompt
from .invoice_matcher import ThreeWayMatcher, parse_invoice_from_vision
from .sidebar_component import get_sidebar_html, get_sidebar_styles

app = FastAPI(title="FQHC 3-Way Match System")

# Initialize components
po_manager = POManager()
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
three_way_matcher = ThreeWayMatcher()

# Store processing results
processing_history: List[Dict] = []
invoice_history: List[Dict] = []

# Create required directories if they don't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("data", exist_ok=True)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.on_event("startup")
async def startup_event():
    """Load PO data on startup"""
    csv_path = Path("data/open_pos.csv")
    if csv_path.exists():
        po_manager.load_from_csv(str(csv_path))
        print(f"✓ Loaded {len(po_manager.po_dict)} POs from CSV")
    else:
        print("⚠ No CSV file found. Please add data/open_pos.csv")


@app.post("/api/upload-packing-slip")
async def upload_packing_slip(file: UploadFile = File(...)):
    """
    Endpoint to receive packing slip images from clinic staff
    Simulates nurse texting/emailing a photo
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(400, "File must be an image")
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        filepath = Path("uploads") / filename
        
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        # Process with Claude Vision
        vision_result = await process_with_vision(content, file.content_type)
        
        # Match against PO database
        match_result = po_manager.match_packing_slip(vision_result)
        
        # Store result
        result = {
            "id": len(processing_history) + 1,
            "timestamp": timestamp,
            "filename": filename,
            "filepath": str(filepath),
            "vision_data": vision_result,
            "match_result": match_result.to_dict(),
            "has_discrepancies": match_result.has_discrepancies
        }
        processing_history.append(result)
        
        return JSONResponse(content={
            "success": True,
            "result": result
        })
        
    except Exception as e:
        raise HTTPException(500, f"Processing error: {str(e)}")


async def process_with_vision(image_content: bytes, content_type: str) -> Dict:
    """
    Process packing slip image with Claude Vision API
    Handles low-quality clinic photos with shadows, blur, etc.
    """
    # Encode image to base64
    base64_image = base64.standard_b64encode(image_content).decode("utf-8")
    
    # Determine media type
    media_type = content_type if content_type else "image/jpeg"
    
    # Call Claude Vision API with specialized prompt
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": get_vision_prompt()
                    }
                ],
            }
        ],
    )
    
    # Extract JSON response
    response_text = message.content[0].text
    
    # Parse JSON from response (handle markdown code blocks)
    try:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
        
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # Fallback: return raw response
        return {
            "error": "Failed to parse JSON",
            "raw_response": response_text,
            "parse_error": str(e)
        }


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Finance Dashboard - shows all uploaded slips and match status"""
    return generate_dashboard_html()


@app.get("/api/history")
async def get_history():
    """Get processing history as JSON"""
    return JSONResponse(content=processing_history)


@app.delete("/api/clear-history")
async def clear_history():
    """Clear all processing history"""
    processing_history.clear()
    return {"success": True, "message": "History cleared"}


def generate_dashboard_html() -> str:
    """Generate HTML dashboard for finance team"""
    
    discrepancy_count = sum(1 for r in processing_history if r.get("has_discrepancies"))
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VerifyAP - Dashboard</title>
        {get_sidebar_styles()}
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f7fa;
                color: #2d3748;
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 2rem;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                position: relative;
            }}
            
            .admin-link {{
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
            }}
            
            .admin-link:hover {{
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
            }}
            
            .header h1 {{
                font-size: 2rem;
                margin-bottom: 0.5rem;
            }}
            
            .header p {{
                opacity: 0.9;
            }}
            
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 1.5rem;
                padding: 2rem;
                max-width: 1600px;
                margin: 0 auto;
                padding: 2rem;
            }}
            
            /* STATS GRID */
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 20px;
                margin-bottom: 32px;
            }}
            
            .stat-card {{
                background: white;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
                padding: 24px;
                transition: all 0.2s;
                cursor: pointer;
            }}
            
            .stat-card:hover {{
                border-color: #4F46E5;
                box-shadow: 0 4px 12px rgba(79, 70, 229, 0.1);
                transform: translateY(-2px);
            }}
            
            .stat-label {{
                font-size: 13px;
                font-weight: 500;
                color: #64748B;
                margin-bottom: 8px;
            }}
            
            .stat-value {{
                font-size: 32px;
                font-weight: 700;
                color: #0F172A;
                margin-bottom: 4px;
            }}
            
            .stat-value.warning {{
                color: #F59E0B;
            }}
            
            .stat-value.success {{
                color: #10B981;
            }}
            
            .stat-change {{
                font-size: 13px;
                font-weight: 600;
                color: #64748B;
            }}
            
            /* PROCESS FLOW */
            .process-flow {{
                background: white;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
                padding: 32px;
                margin-bottom: 32px;
            }}
            
            .process-header {{
                margin-bottom: 24px;
            }}
            
            .process-title {{
                font-size: 18px;
                font-weight: 600;
                color: #0F172A;
                margin-bottom: 4px;
            }}
            
            .process-subtitle {{
                font-size: 14px;
                color: #64748B;
            }}
            
            .process-steps {{
                display: flex;
                align-items: center;
                justify-content: space-between;
            }}
            
            .process-step {{
                flex: 1;
                text-align: center;
            }}
            
            .step-icon {{
                width: 72px;
                height: 72px;
                margin: 0 auto 16px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                border: 3px solid;
            }}
            
            .step-icon.complete {{
                background: #D1FAE5;
                border-color: #10B981;
            }}
            
            .step-icon.active {{
                background: #DBEAFE;
                border-color: #4F46E5;
                box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1);
                animation: pulse 2s infinite;
            }}
            
            .step-icon.pending {{
                background: #FEF3C7;
                border-color: #F59E0B;
            }}
            
            @keyframes pulse {{
                0%, 100% {{ box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1); }}
                50% {{ box-shadow: 0 0 0 8px rgba(79, 70, 229, 0.15); }}
            }}
            
            .step-label {{
                font-size: 14px;
                font-weight: 600;
                color: #0F172A;
                margin-bottom: 8px;
            }}
            
            .step-count {{
                font-size: 28px;
                font-weight: 700;
                color: #4F46E5;
                margin-bottom: 4px;
            }}
            
            .step-status {{
                font-size: 12px;
                color: #64748B;
            }}
            
            .process-arrow {{
                font-size: 32px;
                color: #CBD5E1;
                padding: 0 16px;
            }}
            
            /* QUICK ACTIONS */
            .actions-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 32px;
            }}
            
            .action-card {{
                background: white;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
                padding: 24px;
                cursor: pointer;
                transition: all 0.2s;
            }}
            
            .action-card:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 24px rgba(79, 70, 229, 0.15);
                border-color: #4F46E5;
            }}
            
            .action-icon {{
                width: 56px;
                height: 56px;
                background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 28px;
                margin-bottom: 16px;
            }}
            
            .action-title {{
                font-size: 18px;
                font-weight: 600;
                color: #0F172A;
                margin-bottom: 8px;
            }}
            
            .action-desc {{
                font-size: 14px;
                color: #64748B;
                margin-bottom: 16px;
            }}
            
            /* CARDS */
            .card {{
                background: white;
                border-radius: 12px;
                border: 1px solid #E2E8F0;
                padding: 24px;
                margin-bottom: 24px;
            }}
            
            .card-header {{
                margin-bottom: 20px;
            }}
            
            .card-title {{
                font-size: 18px;
                font-weight: 600;
                color: #0F172A;
                margin-bottom: 4px;
            }}
            
            .card-subtitle {{
                font-size: 14px;
                color: #64748B;
            }}
            
            /* BADGES */
            .badge {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }}
            
            .badge-success {{
                background: #D1FAE5;
                color: #065F46;
            }}
            
            .badge-warning {{
                background: #FEF3C7;
                color: #92400E;
            }}
            
            .badge-error {{
                background: #FEE2E2;
                color: #991B1B;
            }}
            
            .container {{
                max-width: 1600px;
                margin: 0 auto;
                padding: 2rem;
            }}
            
            .upload-section {{
                background: white;
                padding: 2rem;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                margin-bottom: 2rem;
            }}
            
            .upload-btn {{
                background: #667eea;
                color: white;
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: 8px;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.2s;
            }}
            
            .upload-btn:hover {{
                background: #5568d3;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            }}
            
            .results-table {{
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                overflow: hidden;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            
            th {{
                background: #f7fafc;
                padding: 1rem;
                text-align: left;
                font-weight: 600;
                color: #4a5568;
                border-bottom: 2px solid #e2e8f0;
            }}
            
            td {{
                padding: 1rem;
                border-bottom: 1px solid #e2e8f0;
            }}
            
            tr:hover {{
                background: #f7fafc;
            }}
            
            .badge {{
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 9999px;
                font-size: 0.875rem;
                font-weight: 600;
            }}
            
            .badge.success {{
                background: #c6f6d5;
                color: #22543d;
            }}
            
            .badge.warning {{
                background: #fed7d7;
                color: #742a2a;
            }}
            
            .badge.matched {{
                background: #bee3f8;
                color: #2c5282;
            }}
            
            .discrepancy-list {{
                font-size: 0.875rem;
                color: #e53e3e;
                margin-top: 0.5rem;
            }}
            
            .discrepancy-list li {{
                margin-left: 1.5rem;
            }}
            
            .no-data {{
                text-align: center;
                padding: 3rem;
                color: #718096;
            }}
            
            .image-preview {{
                width: 60px;
                height: 60px;
                object-fit: cover;
                border-radius: 6px;
                cursor: pointer;
                transition: transform 0.2s;
            }}
            
            .image-preview:hover {{
                transform: scale(1.1);
            }}
        </style>
    </head>
    <body>
        {get_sidebar_html("dashboard")}
        <div class="verifyap-main-content">
        <div class="header">
            <h1>✓ VerifyAP</h1>
            <p>Dashboard</p>
        </div>
        
        <div class="container">
            <!-- Process Flow -->
            <div class="process-flow">
                <div class="process-header">
                    <h2 class="process-title">Purchase Order Lifecycle</h2>
                    <p class="process-subtitle">Track orders from purchase to payment</p>
                </div>
                
                <div class="process-steps">
                    <div class="process-step">
                        <div class="step-icon complete">📝</div>
                        <div class="step-label">Ordered</div>
                        <div class="step-count">{len(po_manager.po_dict)}</div>
                        <div class="step-status">Open POs</div>
                    </div>
                    
                    <div class="process-arrow">→</div>
                    
                    <div class="process-step">
                        <div class="step-icon active">📦</div>
                        <div class="step-label">Received</div>
                        <div class="step-count">{len(processing_history)}</div>
                        <div class="step-status">Packing Slips</div>
                    </div>
                    
                    <div class="process-arrow">→</div>
                    
                    <div class="process-step">
                        <div class="step-icon pending">💰</div>
                        <div class="step-label">Invoiced</div>
                        <div class="step-count">0</div>
                        <div class="step-status">Awaiting Match</div>
                    </div>
                    
                    <div class="process-arrow">→</div>
                    
                    <div class="process-step">
                        <div class="step-icon complete">✓</div>
                        <div class="step-label">Matched</div>
                        <div class="step-count">0</div>
                        <div class="step-status">Ready to Pay</div>
                    </div>
                </div>
            </div>
            
            <!-- Stats Grid -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Transactions</div>
                    <div class="stat-value">{len(processing_history)}</div>
                    <div class="stat-change">Packing slips processed</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Discrepancies Found</div>
                    <div class="stat-value warning">{discrepancy_count}</div>
                    <div class="stat-change">Items need attention</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">POs in Database</div>
                    <div class="stat-value success">{len(po_manager.po_dict)}</div>
                    <div class="stat-change">Active purchase orders</div>
                </div>
                
                <div class="stat-card">
                    <div class="stat-label">Match Rate</div>
                    <div class="stat-value success">{100 - (discrepancy_count * 100 // max(len(processing_history), 1))}%</div>
                    <div class="stat-change">Successfully matched</div>
                </div>
            </div>
            
            <!-- Quick Actions -->
            <div class="actions-grid">
                <div class="action-card" onclick="document.getElementById('upload-section').scrollIntoView({{behavior: 'smooth'}})">
                    <div class="action-icon">📦</div>
                    <h3 class="action-title">Log a Delivery</h3>
                    <p class="action-desc">Upload packing slip photo to record goods received</p>
                </div>
                
                <div class="action-card" onclick="window.location.href='/invoices'">
                    <div class="action-icon">💰</div>
                    <h3 class="action-title">Process Invoice</h3>
                    <p class="action-desc">Upload vendor invoice for 3-way verification</p>
                </div>
            </div>
        
        <div class="stats" style="display:none;">
            <!-- Old stats hidden -->
        </div>
        
        <div class="container">
            <div class="card" id="upload-section">
                <div class="card-header">
                    <h2 class="card-title">Upload Packing Slip</h2>
                    <p class="card-subtitle">Take or upload a photo to verify against purchase orders</p>
                </div>
                <form id="uploadForm" enctype="multipart/form-data">
                    <div style="border: 2px dashed #E2E8F0; border-radius: 12px; padding: 48px; text-align: center; background: #F8FAFC; cursor: pointer; transition: all 0.2s;" onclick="document.getElementById('fileInput').click()" onmouseover="this.style.borderColor='#4F46E5'; this.style.background='#EEF2FF'" onmouseout="this.style.borderColor='#E2E8F0'; this.style.background='#F8FAFC'">
                        <div style="font-size: 48px; margin-bottom: 16px;">📦</div>
                        <p style="font-size: 16px; font-weight: 600; color: #0F172A; margin-bottom: 8px;">
                            Drop packing slip photo here
                        </p>
                        <p style="font-size: 14px; color: #64748B; margin-bottom: 16px;">
                            or click to browse • Supports JPG, PNG, HEIC
                        </p>
                        <input type="file" id="fileInput" accept="image/*" style="display: none;">
                        <button type="submit" class="upload-btn" style="background: #4F46E5; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.background='#4338CA'; this.style.transform='translateY(-1px)'" onmouseout="this.style.background='#4F46E5'; this.style.transform='translateY(0)'">
                            📸 Upload & Process
                        </button>
                    </div>
                </form>
                <div id="uploadStatus" style="margin-top: 16px;"></div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Recent Activity</h2>
                </div>
                <div style="overflow-x: auto; border-radius: 12px; border: 1px solid #E2E8F0;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr>
                            <th>Image</th>
                            <th>Timestamp</th>
                            <th>PO Number</th>
                            <th>Vendor</th>
                            <th>Status</th>
                            <th>Discrepancies</th>
                        </tr>
                    </thead>
                    <tbody id="resultsBody">
                        {generate_table_rows()}
                    </tbody>
                </table>
                </div>
            </div>
        </div>
        
        <script>
            document.getElementById('uploadForm').addEventListener('submit', async (e) => {{
                e.preventDefault();
                
                const fileInput = document.getElementById('fileInput');
                const statusDiv = document.getElementById('uploadStatus');
                
                if (!fileInput.files[0]) {{
                    statusDiv.innerHTML = '<p style="color: #e53e3e;">Please select a file</p>';
                    return;
                }}
                
                statusDiv.innerHTML = '<p style="color: #667eea;">Processing... ⏳</p>';
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                try {{
                    const response = await fetch('/api/upload-packing-slip', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        statusDiv.innerHTML = '<p style="color: #38a169;">✓ Processed successfully!</p>';
                        setTimeout(() => location.reload(), 1500);
                    }} else {{
                        statusDiv.innerHTML = '<p style="color: #e53e3e;">✗ Processing failed</p>';
                    }}
                }} catch (error) {{
                    statusDiv.innerHTML = '<p style="color: #e53e3e;">✗ Error: ' + error.message + '</p>';
                }}
            }});
        </script>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_table_rows() -> str:
    """Generate HTML table rows for processing history"""
    if not processing_history:
        return """
        <tr>
            <td colspan="6" style="text-align: center; padding: 64px 32px;">
                <div style="font-size: 64px; margin-bottom: 16px; opacity: 0.3;">📋</div>
                <div style="font-size: 18px; font-weight: 600; color: #0F172A; margin-bottom: 8px;">
                    No packing slips processed yet
                </div>
                <div style="font-size: 14px; color: #64748B;">
                    Upload one above to get started!
                </div>
            </td>
        </tr>
        """
    
    rows = []
    for record in reversed(processing_history):  # Show newest first
        vision_data = record.get("vision_data", {})
        match_result = record.get("match_result", {})
        
        po_number = vision_data.get("po_number", "N/A")
        vendor = vision_data.get("vendor_name", "N/A")
        
        # Determine status badge with modern styling
        if match_result.get("po_found"):
            if record.get("has_discrepancies"):
                status_badge = '<span class="badge badge-warning">⚠️ DISCREPANCY</span>'
            else:
                status_badge = '<span class="badge badge-success">✓ MATCHED</span>'
        else:
            status_badge = '<span class="badge badge-error">❌ NO MATCH</span>'
        
        # Generate discrepancy list
        discrepancies = match_result.get("discrepancies", [])
        discrepancy_html = ""
        if discrepancies:
            discrepancy_html = "<ul style='margin: 0; padding-left: 20px; font-size: 13px;'>"
            for disc in discrepancies[:3]:  # Show max 3
                discrepancy_html += f"<li>{disc}</li>"
            if len(discrepancies) > 3:
                discrepancy_html += f"<li>...and {len(discrepancies) - 3} more</li>"
            discrepancy_html += "</ul>"
        
        # Image preview
        filepath = record.get("filepath", "")
        image_html = f'<img src="/{filepath}" class="image-preview" alt="Packing slip">' if filepath else "📄"
        
        rows.append(f"""
        <tr>
            <td>{image_html}</td>
            <td>{record.get('timestamp', 'N/A')}</td>
            <td><strong>{po_number}</strong></td>
            <td>{vendor}</td>
            <td>{status_badge}</td>
            <td>{discrepancy_html if discrepancy_html else "—"}</td>
        </tr>
        """)
    
    
    return "\n".join(rows)


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    """Admin page for uploading PO CSV"""
    return get_admin_html()


@app.post("/api/upload-po-csv")
async def upload_po_csv(file: UploadFile = File(...)):
    """Upload and load PO CSV file"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(400, "File must be a CSV")
        
        # Save uploaded CSV
        csv_path = Path("data/open_pos.csv")
        contents = await file.read()
        
        with open(csv_path, "wb") as f:
            f.write(contents)
        
        # Reload PO data
        result = po_manager.load_from_csv(str(csv_path))
        
        return {
            "success": True,
            "message": f"✓ Loaded {result['po_count']} POs with {result['line_item_count']} line items from {result['vendor_count']} vendors",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/po-stats")
async def get_po_stats():
    """Get current PO database statistics"""
    vendor_set = set()
    line_item_count = 0
    
    for po in po_manager.po_dict.values():
        vendor_set.add(po.vendor_name)
        line_item_count += len(po.line_items)
    
    return {
        "po_count": len(po_manager.po_dict),
        "line_item_count": line_item_count,
        "vendor_count": len(vendor_set)
    }


@app.get("/invoices", response_class=HTMLResponse)
async def invoice_page():
    """Invoice upload and management page"""
    return get_invoice_html()


@app.post("/api/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):
    """Upload and process invoice for 3-way matching"""
    try:
        # Validate file type
        if not (file.content_type.startswith("image/") or file.content_type == "application/pdf"):
            raise HTTPException(400, "File must be an image or PDF")
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"invoice_{timestamp}_{file.filename}"
        filepath = Path("uploads") / filename
        
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        
        # Process with Claude Vision
        invoice_vision_data = await process_invoice_with_vision(content, file.content_type)
        
        # Parse into InvoiceData structure
        invoice_data = parse_invoice_from_vision(invoice_vision_data)
        
        # Find matching PO
        po_data = None
        if invoice_data.po_number:
            po = po_manager.po_dict.get(invoice_data.po_number)
            if po:
                po_data = {
                    "po_number": po.po_number,
                    "vendor": po.vendor_name,
                    "line_items": [
                        {
                            "description": item.item_description,
                            "quantity_ordered": item.quantity_ordered,
                            "unit_price": item.unit_price
                        }
                        for item in po.line_items
                    ]
                }
        
        # Find matching packing slip
        packing_slip_data = None
        for record in processing_history:
            if record.get("vision_data", {}).get("po_number") == invoice_data.po_number:
                packing_slip_data = record.get("vision_data")
                break
        
        # Perform 3-way match
        match_result = three_way_matcher.match_invoice(
            invoice_data,
            po_data=po_data,
            packing_slip_data=packing_slip_data
        )
        
        # Store result
        invoice_record = {
            "id": len(invoice_history) + 1,
            "timestamp": timestamp,
            "filename": filename,
            "filepath": str(filepath),
            "invoice_data": invoice_vision_data,
            "invoice_number": invoice_data.invoice_number,
            "po_number": invoice_data.po_number,
            "vendor": invoice_data.vendor_name,
            "total_amount": invoice_data.total_amount,
            "match_status": match_result["match_status"],
            "match_result": match_result
        }
        
        invoice_history.append(invoice_record)
        
        return {
            "success": True,
            "message": match_result["summary"],
            "invoice_number": invoice_data.invoice_number,
            "po_number": invoice_data.po_number,
            "match_status": match_result["match_status"],
            "discrepancies": match_result["discrepancies"],
            "warnings": match_result.get("warnings", []),
            "details": match_result["details"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/invoices")
async def get_invoices():
    """Get all uploaded invoices"""
    return JSONResponse(content=invoice_history)


async def process_invoice_with_vision(content: bytes, content_type: str) -> Dict:
    """Process invoice with Claude Vision API"""
    
    # Prepare image data
    if content_type == "application/pdf":
        # For PDF, we'll use document type
        media_type = "application/pdf"
        image_data = base64.standard_b64encode(content).decode("utf-8")
    else:
        # For images
        media_type = content_type
        image_data = base64.standard_b64encode(content).decode("utf-8")
    
    # Call Claude Vision API
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image" if content_type.startswith("image/") else "document",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": get_invoice_vision_prompt()
                    }
                ],
            }
        ],
    )
    
    # Extract JSON response
    response_text = message.content[0].text
    
    # Parse JSON from response
    try:
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
        
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        return {
            "error": "Failed to parse JSON",
            "raw_response": response_text,
            "parse_error": str(e)
        }


@app.get("/api/po-stats")
async def get_po_stats():
    """Get current PO database statistics"""
    vendor_set = set()
    line_item_count = 0
    
    for po in po_manager.po_dict.values():
        vendor_set.add(po.vendor_name)
        line_item_count += len(po.line_items)
    
    return {
        "po_count": len(po_manager.po_dict),
        "line_item_count": line_item_count,
        "vendor_count": len(vendor_set)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
