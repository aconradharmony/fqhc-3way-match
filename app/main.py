"""
VerifyAP - Main FastAPI Application & Dashboard
Updated: Feb 26, 2026 — Dashboard is now analytics-only (lifecycle + stats).
Packing slip upload moved to /deliveries. PO upload generalized on /admin.
"""

import os
import json
import base64
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# --- App Setup ---
app = FastAPI(title="VerifyAP", description="AI-Powered 3-Way Match for Accounts Payable")

# Auto-create directories (Render filesystem starts empty)
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("data", exist_ok=True)

# --- In-Memory Storage ---
purchase_orders = {}
packing_slips = []
invoices = []
match_results = []


# --- Import Page Modules ---
from .admin_html import get_admin_html, handle_csv_upload, handle_po_pdf_upload
from .invoice_html import get_invoice_html
from .deliveries_html import get_deliveries_html
from .sidebar_component import get_sidebar_html, get_sidebar_styles
from .po_matcher import match_packing_slip
from .invoice_matcher import match_invoice


# --- Dashboard HTML ---
def get_dashboard_html():
    """Generate the dashboard page — analytics command center."""

    sidebar_html = get_sidebar_html("dashboard")
    sidebar_styles = get_sidebar_styles()

    # Calculate stats from in-memory data
    total_transactions = len(packing_slips)
    total_pos = len(purchase_orders)
    discrepancies = sum(1 for s in packing_slips if s.get("has_discrepancy", False))
    matched_count = total_transactions - discrepancies if total_transactions > 0 else 0
    match_rate = round((matched_count / total_transactions) * 100) if total_transactions > 0 else 100

    # Lifecycle counts
    open_pos = total_pos
    received_count = len(packing_slips)
    invoiced_count = len(invoices)
    matched_final = len([r for r in match_results if r.get("status") == "APPROVE"])

    html = (
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VerifyAP - Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    """
        + sidebar_styles
        + """
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, sans-serif; background: #F8FAFC; color: #1E293B; }

        .dashboard-header {
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #9333EA 100%);
            padding: 36px 40px 32px 40px;
            color: white;
        }
        .dashboard-header h1 {
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .dashboard-header p {
            margin-top: 4px;
            font-size: 14px;
            color: rgba(255, 255, 255, 0.75);
            font-weight: 400;
        }

        .dashboard-body { padding: 32px 40px; }

        /* --- Purchase Order Lifecycle --- */
        .lifecycle-card {
            background: white;
            border-radius: 16px;
            border: 1px solid #E2E8F0;
            padding: 32px;
            margin-bottom: 28px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .lifecycle-card h2 {
            font-size: 18px;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 4px;
        }
        .lifecycle-card .subtitle {
            font-size: 13px;
            color: #64748B;
            margin-bottom: 28px;
        }
        .lifecycle-steps {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0;
        }
        .lifecycle-step {
            display: flex;
            flex-direction: column;
            align-items: center;
            flex: 1;
        }
        .lifecycle-icon-wrap {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            margin-bottom: 10px;
        }
        .lifecycle-icon-wrap.step-ordered { background: #EEF2FF; border: 2.5px solid #A5B4FC; }
        .lifecycle-icon-wrap.step-received { background: #FEF9C3; border: 2.5px solid #FDE047; }
        .lifecycle-icon-wrap.step-invoiced { background: #FFF7ED; border: 2.5px solid #FDBA74; }
        .lifecycle-icon-wrap.step-matched { background: #ECFDF5; border: 2.5px solid #6EE7B7; }

        .lifecycle-step-label {
            font-size: 13px;
            font-weight: 600;
            color: #334155;
            margin-bottom: 4px;
        }
        .lifecycle-step-value {
            font-size: 24px;
            font-weight: 800;
            color: #0F172A;
        }
        .lifecycle-step-sub {
            font-size: 11px;
            color: #94A3B8;
            margin-top: 2px;
        }
        .lifecycle-arrow {
            font-size: 22px;
            color: #CBD5E1;
            flex-shrink: 0;
            margin: 0 4px;
            padding-bottom: 40px;
        }

        /* --- Stat Cards --- */
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }
        .stat-card {
            background: white;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            padding: 24px;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }
        .stat-card-label {
            font-size: 12px;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .stat-card-value {
            font-size: 32px;
            font-weight: 800;
            color: #0F172A;
            line-height: 1;
        }
        .stat-card-value.green { color: #10B981; }
        .stat-card-value.amber { color: #F59E0B; }
        .stat-card-value.rose { color: #EF4444; }
        .stat-card-sub {
            font-size: 12px;
            color: #94A3B8;
            margin-top: 6px;
        }
        .stat-card.highlight {
            background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
            border-color: #A7F3D0;
        }

        @media (max-width: 900px) {
            .stat-grid { grid-template-columns: repeat(2, 1fr); }
            .lifecycle-steps { flex-wrap: wrap; gap: 16px; }
            .lifecycle-arrow { display: none; }
        }
    </style>
</head>
<body>
    """
        + sidebar_html
        + """
    <div class="verifyap-main-content">
        <div class="dashboard-header">
            <h1>&#10003; VerifyAP</h1>
            <p>Dashboard</p>
        </div>

        <div class="dashboard-body">
            <!-- Purchase Order Lifecycle -->
            <div class="lifecycle-card">
                <h2>Purchase Order Lifecycle</h2>
                <p class="subtitle">Track orders from purchase to payment</p>
                <div class="lifecycle-steps">
                    <div class="lifecycle-step">
                        <div class="lifecycle-icon-wrap step-ordered">&#128203;</div>
                        <div class="lifecycle-step-label">Ordered</div>
                        <div class="lifecycle-step-value">"""
        + str(open_pos)
        + """</div>
                        <div class="lifecycle-step-sub">Open POs</div>
                    </div>
                    <div class="lifecycle-arrow">&rarr;</div>
                    <div class="lifecycle-step">
                        <div class="lifecycle-icon-wrap step-received">&#128230;</div>
                        <div class="lifecycle-step-label">Received</div>
                        <div class="lifecycle-step-value">"""
        + str(received_count)
        + """</div>
                        <div class="lifecycle-step-sub">Packing Slips</div>
                    </div>
                    <div class="lifecycle-arrow">&rarr;</div>
                    <div class="lifecycle-step">
                        <div class="lifecycle-icon-wrap step-invoiced">&#128176;</div>
                        <div class="lifecycle-step-label">Invoiced</div>
                        <div class="lifecycle-step-value">"""
        + str(invoiced_count)
        + """</div>
                        <div class="lifecycle-step-sub">Awaiting Match</div>
                    </div>
                    <div class="lifecycle-arrow">&rarr;</div>
                    <div class="lifecycle-step">
                        <div class="lifecycle-icon-wrap step-matched">&#10003;</div>
                        <div class="lifecycle-step-label">Matched</div>
                        <div class="lifecycle-step-value">"""
        + str(matched_final)
        + """</div>
                        <div class="lifecycle-step-sub">Ready to Pay</div>
                    </div>
                </div>
            </div>

            <!-- Stat Cards -->
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-card-label">Total Transactions</div>
                    <div class="stat-card-value">"""
        + str(total_transactions)
        + """</div>
                    <div class="stat-card-sub">Packing slips processed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">Discrepancies Found</div>
                    <div class="stat-card-value amber">"""
        + str(discrepancies)
        + """</div>
                    <div class="stat-card-sub">Items need attention</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-label">POs in Database</div>
                    <div class="stat-card-value">"""
        + str(total_pos)
        + """</div>
                    <div class="stat-card-sub">Active purchase orders</div>
                </div>
                <div class="stat-card highlight">
                    <div class="stat-card-label">Match Rate</div>
                    <div class="stat-card-value green">"""
        + str(match_rate)
        + """%</div>
                    <div class="stat-card-sub">Successfully matched</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
    )

    return html


# =====================
# ROUTES
# =====================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return get_dashboard_html()


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    return get_admin_html(purchase_orders)


@app.get("/deliveries", response_class=HTMLResponse)
async def deliveries_page():
    return get_deliveries_html()


@app.get("/invoices", response_class=HTMLResponse)
async def invoices_page():
    return get_invoice_html()


# =====================
# API ENDPOINTS
# =====================

@app.get("/api/po-stats")
async def po_stats():
    """Return PO statistics for the admin page."""
    total_pos = len(purchase_orders)
    total_items = sum(len(po.get("items", [])) for po in purchase_orders.values())
    vendors = set()
    for po in purchase_orders.values():
        vendor = po.get("vendor", "")
        if vendor:
            vendors.add(vendor)
    return {
        "active_pos": total_pos,
        "line_items": total_items,
        "active_vendors": len(vendors),
    }


@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Handle CSV upload for purchase orders."""
    contents = await file.read()
    result = handle_csv_upload(contents, purchase_orders)
    return JSONResponse(content=result)


@app.post("/api/upload-po-pdf")
async def upload_po_pdf(file: UploadFile = File(...)):
    """Handle PDF upload for purchase orders (Claude Vision OCR)."""
    contents = await file.read()
    filename = file.filename or "po_upload.pdf"
    result = await handle_po_pdf_upload(contents, filename, purchase_orders)
    return JSONResponse(content=result)


@app.post("/api/upload-packing-slip")
async def upload_packing_slip(file: UploadFile = File(...)):
    """Handle packing slip upload — OCR via Claude Vision + PO matching."""
    import anthropic
    from .vision_prompt import get_vision_prompt

    contents = await file.read()
    filename = file.filename or "packing_slip.jpg"

    # Determine media type
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "jpg"
    media_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "heic": "image/heic",
        "pdf": "application/pdf",
    }
    media_type = media_map.get(ext, "image/jpeg")

    # Save file
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    # Encode to base64
    b64_data = base64.b64encode(contents).decode("utf-8")

    # Call Claude Vision
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

        # Build content block based on file type
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
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        source_block,
                        {"type": "text", "text": get_vision_prompt()},
                    ],
                }
            ],
        )

        response_text = message.content[0].text

        # Extract JSON (handle markdown fencing)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        slip_data = json.loads(json_str)

        # Match against POs
        match_result = match_packing_slip(slip_data, purchase_orders)
        slip_data["match_result"] = match_result
        slip_data["has_discrepancy"] = match_result.get("has_discrepancy", False)

        packing_slips.append(slip_data)

        return {"success": True, "data": slip_data, "match": match_result}

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):
    """Handle invoice upload — OCR via Claude Vision + 3-way matching."""
    import anthropic
    from .invoice_vision_prompt import get_invoice_vision_prompt

    contents = await file.read()
    filename = file.filename or "invoice.pdf"

    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "jpg"
    media_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "pdf": "application/pdf",
    }
    media_type = media_map.get(ext, "image/jpeg")

    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    b64_data = base64.b64encode(contents).decode("utf-8")

    try:
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
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        source_block,
                        {"type": "text", "text": get_invoice_vision_prompt()},
                    ],
                }
            ],
        )

        response_text = message.content[0].text

        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        invoice_data = json.loads(json_str)

        # 3-way match
        result = match_invoice(invoice_data, purchase_orders, packing_slips)
        invoice_data["match_result"] = result
        invoices.append(invoice_data)
        match_results.append(result)

        return {"success": True, "data": invoice_data, "match": result}

    except Exception as e:
        return {"success": False, "error": str(e)}
