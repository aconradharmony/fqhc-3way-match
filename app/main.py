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

app = FastAPI(title="FQHC 3-Way Match System")

# Initialize components
po_manager = POManager()
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Store processing results
processing_history: List[Dict] = []

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
        <title>FQHC 3-Way Match Dashboard</title>
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
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            .stat-card {{
                background: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }}
            
            .stat-label {{
                font-size: 0.875rem;
                color: #718096;
                margin-bottom: 0.5rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            
            .stat-value {{
                font-size: 2.5rem;
                font-weight: 700;
                color: #2d3748;
            }}
            
            .stat-value.warning {{
                color: #f56565;
            }}
            
            .container {{
                max-width: 1400px;
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
        <div class="header">
            <h1>🏥 FQHC 3-Way Match Dashboard</h1>
            <p>Purchase Order Verification System</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Slips Processed</div>
                <div class="stat-value">{len(processing_history)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Discrepancies Found</div>
                <div class="stat-value warning">{discrepancy_count}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">POs in Database</div>
                <div class="stat-value">{len(po_manager.po_dict)}</div>
            </div>
        </div>
        
        <div class="container">
            <div class="upload-section">
                <h2 style="margin-bottom: 1rem;">Upload Packing Slip</h2>
                <p style="color: #718096; margin-bottom: 1rem;">
                    Upload a photo of the packing slip to verify against open purchase orders.
                </p>
                <form id="uploadForm" enctype="multipart/form-data">
                    <input type="file" id="fileInput" accept="image/*" style="margin-bottom: 1rem;">
                    <button type="submit" class="upload-btn">📸 Upload & Process</button>
                </form>
                <div id="uploadStatus" style="margin-top: 1rem;"></div>
            </div>
            
            <div class="results-table">
                <table>
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
    </body>
    </html>
    """
    
    return html


def generate_table_rows() -> str:
    """Generate HTML table rows for processing history"""
    if not processing_history:
        return """
        <tr>
            <td colspan="6" class="no-data">
                No packing slips processed yet. Upload one to get started! 📦
            </td>
        </tr>
        """
    
    rows = []
    for record in reversed(processing_history):  # Show newest first
        vision_data = record.get("vision_data", {})
        match_result = record.get("match_result", {})
        
        po_number = vision_data.get("po_number", "N/A")
        vendor = vision_data.get("vendor_name", "N/A")
        
        # Determine status badge
        if match_result.get("po_found"):
            if record.get("has_discrepancies"):
                status_badge = '<span class="badge warning">⚠ Discrepancies</span>'
            else:
                status_badge = '<span class="badge success">✓ Match</span>'
        else:
            status_badge = '<span class="badge warning">✗ PO Not Found</span>'
        
        # Generate discrepancy list
        discrepancies = match_result.get("discrepancies", [])
        discrepancy_html = ""
        if discrepancies:
            discrepancy_html = "<ul class='discrepancy-list'>"
            for disc in discrepancies:
                discrepancy_html += f"<li>{disc}</li>"
            discrepancy_html += "</ul>"
        
        # Image preview
        filepath = record.get("filepath", "")
        image_html = f'<img src="/{filepath}" class="image-preview" alt="Packing slip">'
        
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
