"""
VerifyAP — API Routes for Dashboard Drill-Downs, Document History & Lifecycle

All endpoints return JSON. Frontend pages consume these via fetch().

Endpoints:
  GET  /api/v2/purchase-orders          — Filtered PO list (with match status)
  GET  /api/v2/purchase-orders/{po_id}  — Single PO with full details + lines
  GET  /api/v2/discrepancies            — All matches with discrepancies
  GET  /api/v2/match/{match_id}         — Full match detail with per-line drill-in
  GET  /api/v2/document-history         — All document events (timeline)
  GET  /api/v2/document-history/{po_id} — Timeline for a specific PO
  GET  /api/v2/dashboard-stats          — Aggregated stats for dashboard cards
  POST /api/v2/verify/{po_id}           — Mark a PO as verified
  POST /api/v2/archive/batch            — Batch archive verified POs
  GET  /api/v2/archive/candidates       — POs eligible for archiving
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from .database import get_db

router = APIRouter(prefix="/api/v2", tags=["VerifyAP v2"])


# ---------------------------------------------------------------------------
# Dashboard Stats
# ---------------------------------------------------------------------------

@router.get("/dashboard-stats")
def dashboard_stats():
    """Aggregated counts for the clickable dashboard cards."""
    db = get_db()
    pos = db.list_pos()

    total_pos = len(pos)
    active_pos = len([p for p in pos if p.get("status") == "active"])
    matched_pos = len([p for p in pos if p.get("match_status") in ("approve", "review", "reject")])
    unmatched_pos = len([p for p in pos if p.get("match_status") == "unmatched"])

    discrepancies = db.list_discrepancies()
    total_discrepancies = len(discrepancies)
    review_count = len([d for d in discrepancies if d.get("overall_status") == "review"])
    reject_count = len([d for d in discrepancies if d.get("overall_status") == "reject"])

    approved_total = sum(
        float(p.get("total_amount", 0) or 0) for p in pos if p.get("match_status") == "approve"
    )

    verified_pos = len([p for p in pos if p.get("status") == "verified"])
    archived_pos = len([p for p in pos if p.get("status") == "archived"])

    return {
        "purchase_orders": {
            "total": total_pos,
            "active": active_pos,
            "matched": matched_pos,
            "unmatched": unmatched_pos,
        },
        "discrepancies": {
            "total": total_discrepancies,
            "review": review_count,
            "reject": reject_count,
        },
        "financials": {
            "approved_total": round(approved_total, 2),
        },
        "lifecycle": {
            "verified": verified_pos,
            "archived": archived_pos,
        },
    }


# ---------------------------------------------------------------------------
# Purchase Orders
# ---------------------------------------------------------------------------

@router.get("/purchase-orders")
def list_purchase_orders(
    status: Optional[str] = Query(None, description="Filter by status: active|matched|verified|archived"),
    match_status: Optional[str] = Query(None, description="Filter by match: approve|review|reject|unmatched"),
    vendor: Optional[str] = Query(None, description="Filter by vendor name (partial match)"),
):
    """List POs with match status summary. Powers the PO list view."""
    db = get_db()
    pos = db.list_pos(status=status)

    if match_status:
        pos = [p for p in pos if p.get("match_status") == match_status]

    if vendor:
        vendor_lower = vendor.lower()
        pos = [p for p in pos if vendor_lower in (p.get("vendor_name") or "").lower()]

    # Shape output for the frontend table
    return {
        "count": len(pos),
        "purchase_orders": [
            {
                "id": p["id"],
                "po_number": p.get("po_number"),
                "vendor_name": p.get("vendor_name"),
                "order_date": p.get("order_date"),
                "total_amount": p.get("total_amount"),
                "status": p.get("status"),
                "match_status": p.get("match_status", "unmatched"),
                "total_discrepancies": p.get("total_discrepancies", 0),
                "amount_delta": p.get("amount_delta", 0),
                "product_line_count": p.get("product_line_count", 0),
                "slip_count": p.get("slip_count", 0),
                "invoice_count": p.get("invoice_count", 0),
                "source_type": p.get("source_type"),
                "uploaded_at": p.get("uploaded_at"),
            }
            for p in pos
        ],
    }


@router.get("/purchase-orders/{po_id}")
def get_purchase_order(po_id: str):
    """Full PO detail with line items, linked slips, invoices, and matches."""
    db = get_db()
    po = db.get_po(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    slips = db.get_slips_for_po(po_id)
    matches = db.get_matches_for_po(po_id)

    # Get linked invoices
    invoices = []
    for m in matches:
        inv_id = m.get("invoice_id")
        if inv_id:
            inv = db.get_invoice(inv_id)
            if inv:
                invoices.append(inv)

    timeline = db.get_timeline_for_po(po_id)

    return {
        "purchase_order": po,
        "packing_slips": slips,
        "invoices": invoices,
        "matches": matches,
        "timeline": timeline,
    }


# ---------------------------------------------------------------------------
# Discrepancies
# ---------------------------------------------------------------------------

@router.get("/discrepancies")
def list_discrepancies(
    severity: Optional[str] = Query(None, description="Filter: review|reject"),
    vendor: Optional[str] = Query(None),
):
    """All matches that have discrepancies. Powers the Discrepancies list view."""
    db = get_db()
    discs = db.list_discrepancies()

    if severity:
        discs = [d for d in discs if d.get("overall_status") == severity]

    if vendor:
        vendor_lower = vendor.lower()
        discs = [d for d in discs if vendor_lower in (d.get("vendor_name") or "").lower()]

    return {
        "count": len(discs),
        "discrepancies": [
            {
                "match_id": d["id"],
                "po_number": d.get("po_number"),
                "vendor_name": d.get("vendor_name"),
                "po_total": d.get("po_total"),
                "invoice_number": d.get("invoice_number"),
                "invoice_total": d.get("invoice_total"),
                "amount_delta": d.get("amount_delta"),
                "overall_status": d.get("overall_status"),
                "total_discrepancies": d.get("total_discrepancies"),
                "match_type": d.get("match_type"),
                "summary": d.get("summary"),
                "matched_at": d.get("created_at"),
                "discrepancy_lines": [
                    {
                        "line_number": dl.get("line_number"),
                        "discrepancy_type": dl.get("discrepancy_type"),
                        "discrepancy_note": dl.get("discrepancy_note"),
                        "po_description": dl.get("po_description"),
                        "po_quantity": dl.get("po_quantity"),
                        "slip_qty_shipped": dl.get("slip_qty_shipped"),
                        "inv_quantity": dl.get("inv_quantity"),
                        "po_unit_price": dl.get("po_unit_price"),
                        "inv_unit_price": dl.get("inv_unit_price"),
                    }
                    for dl in d.get("discrepancy_lines", [])
                ],
            }
            for d in discs
        ],
    }


# ---------------------------------------------------------------------------
# Match Detail (Drill-In)
# ---------------------------------------------------------------------------

@router.get("/match/{match_id}")
def get_match_detail(match_id: str):
    """Full match detail with every line comparison. This is the drill-in view."""
    db = get_db()
    match = db.get_match(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Match result not found")

    # Enrich with PO / slip / invoice metadata
    po = db.get_po(match.get("po_id", ""))
    slip = db.get_slip(match.get("slip_id", "")) if match.get("slip_id") else None
    inv = db.get_invoice(match.get("invoice_id", "")) if match.get("invoice_id") else None

    return {
        "match": match,
        "purchase_order": {
            "po_number": po.get("po_number") if po else None,
            "vendor_name": po.get("vendor_name") if po else None,
            "total_amount": po.get("total_amount") if po else None,
            "source_filename": po.get("source_filename") if po else None,
        },
        "packing_slip": {
            "slip_number": slip.get("slip_number") if slip else None,
            "delivery_number": slip.get("delivery_number") if slip else None,
            "total_units": slip.get("total_units") if slip else None,
            "source_filename": slip.get("source_filename") if slip else None,
        } if slip else None,
        "invoice": {
            "invoice_number": inv.get("invoice_number") if inv else None,
            "total_amount": inv.get("total_amount") if inv else None,
            "payment_terms": inv.get("payment_terms") if inv else None,
            "source_filename": inv.get("source_filename") if inv else None,
        } if inv else None,
    }


# ---------------------------------------------------------------------------
# Document History / Timeline
# ---------------------------------------------------------------------------

@router.get("/document-history")
def list_document_history(
    limit: int = Query(50, ge=1, le=200),
):
    """Global document event timeline."""
    db = get_db()
    events = db.get_all_events()
    return {
        "count": len(events[:limit]),
        "events": events[:limit],
    }


@router.get("/document-history/{po_id}")
def get_po_timeline(po_id: str):
    """Timeline for a specific PO — shows when each document was uploaded and matched."""
    db = get_db()
    po = db.get_po(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    timeline = db.get_timeline_for_po(po_id)

    return {
        "po_number": po.get("po_number"),
        "vendor_name": po.get("vendor_name"),
        "current_status": po.get("status"),
        "timeline": timeline,
    }


# ---------------------------------------------------------------------------
# Lifecycle Management
# ---------------------------------------------------------------------------

@router.post("/verify/{po_id}")
def verify_po(po_id: str):
    """Mark a PO as verified (AP sync confirmed). Starts the archive clock."""
    db = get_db()
    po = db.get_po(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")

    db.update_status("po", po_id, "verified")
    return {
        "status": "verified",
        "po_number": po.get("po_number"),
        "message": "PO marked as verified. Archive eligibility starts in 30 days.",
    }


@router.get("/archive/candidates")
def get_archive_candidates(
    days: int = Query(30, description="Days after verification before archive eligibility"),
):
    """List POs that are eligible for archiving."""
    db = get_db()
    candidates = db.get_archive_candidates(days=days)
    return {
        "count": len(candidates),
        "candidates": [
            {
                "id": c["id"],
                "po_number": c.get("po_number"),
                "vendor_name": c.get("vendor_name"),
                "total_amount": c.get("total_amount"),
                "verified_at": c.get("verified_at"),
            }
            for c in candidates
        ],
    }


@router.post("/archive/batch")
def batch_archive(po_ids: List[str]):
    """Archive multiple verified POs at once."""
    db = get_db()
    archived = db.batch_archive(po_ids)
    return {
        "archived_count": archived,
        "message": str(archived) + " purchase order(s) archived.",
    }
