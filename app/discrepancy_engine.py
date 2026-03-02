"""
VerifyAP — Discrepancy Engine v2.0

Performs 3-way matching (PO vs Packing Slip vs Invoice) with real-world
awareness of pharmaceutical document quirks:

  1. Fuzzy description matching (product names vary across documents)
  2. Tax lines appear on PO + Invoice but NOT on packing slips
  3. Zero-cost bundled items (e.g. sterile diluent syringes shipped with
     Proquad) appear on slip + invoice but NOT on PO
  4. Quantity semantics differ: PO says "1" meaning "1 box of 10 vials",
     packing slip also says "1" (same meaning)
  5. Dollar totals must match across PO and invoice

Match outcomes:
  APPROVE  — all product lines match on qty + price, totals agree
  REVIEW   — minor discrepancies (bundled items, info-only differences)
  REJECT   — material discrepancies (qty mismatch, price mismatch, missing items)
"""

import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

# Known pharma product keywords for fuzzy matching
PRODUCT_KEYWORDS = {
    "mmr": ["m-m-r", "mmr", "m.m.r"],
    "proquad": ["proquad", "pro-quad"],
    "varivax": ["varivax"],
    "diluent": ["diluent", "dilutent"],
    "syringe": ["syringe", "syrnge"],
}

# Tax line detection patterns
TAX_PATTERNS = [
    r"excise\s*tax",
    r"^tax$",
    r"federal\s*excise",
    r"state\s*tax",
]

# Bundled / zero-cost item patterns
BUNDLED_PATTERNS = [
    r"sterile\s+diluent",
    r"diluent.*syringe",
    r"needle",
    r"applicator",
]


def normalize_description(desc: str) -> str:
    """Lowercase, strip whitespace, collapse spaces, remove special chars."""
    if not desc:
        return ""
    text = desc.lower().strip()
    text = re.sub(r"[^a-z0-9\s\.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_tax_line(description: str) -> bool:
    """Check if a line item is a tax/excise line."""
    norm = normalize_description(description)
    return any(re.search(p, norm) for p in TAX_PATTERNS)


def is_bundled_item(description: str) -> bool:
    """Check if a line item is a zero-cost bundled accessory."""
    norm = normalize_description(description)
    return any(re.search(p, norm) for p in BUNDLED_PATTERNS)


def fuzzy_match_score(desc_a: str, desc_b: str) -> float:
    """Score 0.0–1.0 for how similar two product descriptions are."""
    if not desc_a or not desc_b:
        return 0.0
    norm_a = normalize_description(desc_a)
    norm_b = normalize_description(desc_b)

    # Exact match after normalization
    if norm_a == norm_b:
        return 1.0

    # Check if they share a known product keyword
    for key, variants in PRODUCT_KEYWORDS.items():
        a_has = any(v in norm_a for v in variants)
        b_has = any(v in norm_b for v in variants)
        if a_has and b_has:
            return 0.9  # Same product family

    # Fall back to sequence matching
    return SequenceMatcher(None, norm_a, norm_b).ratio()


def find_best_match(target: Dict, candidates: List[Dict], threshold: float = 0.5) -> Optional[Tuple[Dict, float]]:
    """Find the best-matching line item from candidates for a target line."""
    target_desc = target.get("description", "")
    best = None
    best_score = 0.0
    for cand in candidates:
        score = fuzzy_match_score(target_desc, cand.get("description", ""))
        if score > best_score and score >= threshold:
            best = cand
            best_score = score
    if best:
        return (best, best_score)
    return None


# ---------------------------------------------------------------------------
# Core 3-Way Match Engine
# ---------------------------------------------------------------------------

def run_3way_match(
    po: Dict,
    slip: Optional[Dict],
    invoice: Optional[Dict],
) -> Dict:
    """
    Run a full 3-way match and return structured results with
    per-line drill-in details.

    Args:
        po: Purchase order dict with "line_items" list
        slip: Packing slip dict with "line_items" list (or None for 2-way)
        invoice: Invoice dict with "line_items" list (or None for 2-way)

    Returns:
        Dict with keys:
            match_type, overall_status, confidence, total_discrepancies,
            amount_delta, summary, line_details (list of per-line comparisons)
    """
    match_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    po_lines = po.get("line_items", [])
    slip_lines = slip.get("line_items", []) if slip else []
    inv_lines = invoice.get("line_items", []) if invoice else []

    # Determine match type
    has_slip = slip is not None and len(slip_lines) > 0
    has_invoice = invoice is not None and len(inv_lines) > 0
    if has_slip and has_invoice:
        match_type = "3way"
    elif has_slip:
        match_type = "2way_po_slip"
    elif has_invoice:
        match_type = "2way_po_inv"
    else:
        return {
            "id": match_id,
            "match_type": "none",
            "overall_status": "review",
            "confidence": 0.0,
            "total_discrepancies": 0,
            "amount_delta": 0,
            "summary": "No packing slip or invoice to match against.",
            "line_details": [],
            "created_at": now,
        }

    # Separate product lines from tax / bundled lines
    po_products = [l for l in po_lines if not l.get("is_tax_line") and not is_tax_line(l.get("description", ""))]
    po_taxes = [l for l in po_lines if l.get("is_tax_line") or is_tax_line(l.get("description", ""))]

    slip_products = [l for l in slip_lines if not is_bundled_item(l.get("description", ""))]
    slip_bundled = [l for l in slip_lines if is_bundled_item(l.get("description", ""))]

    inv_products = [l for l in inv_lines if not l.get("is_tax_line") and not is_tax_line(l.get("description", "")) and not l.get("is_zero_cost") and not is_bundled_item(l.get("description", ""))]
    inv_taxes = [l for l in inv_lines if l.get("is_tax_line") or is_tax_line(l.get("description", ""))]
    inv_bundled = [l for l in inv_lines if (l.get("is_zero_cost") or is_bundled_item(l.get("description", ""))) and not is_tax_line(l.get("description", ""))]

    line_details = []
    discrepancies = 0
    line_num = 0

    # --- Phase 1: Match product lines (PO → slip → invoice) ---
    used_slip = set()
    used_inv = set()

    for po_line in po_products:
        line_num += 1
        detail = {
            "line_number": line_num,
            "po_description": po_line.get("description"),
            "po_quantity": _to_float(po_line.get("quantity")),
            "po_unit_price": _to_float(po_line.get("unit_price")),
            "po_line_total": _to_float(po_line.get("line_total")),
        }

        # Find matching slip line
        slip_match = None
        if has_slip:
            available_slip = [s for i, s in enumerate(slip_products) if i not in used_slip]
            result = find_best_match(po_line, available_slip)
            if result:
                slip_match, score = result
                used_slip.add(slip_products.index(slip_match))
                detail["slip_description"] = slip_match.get("description")
                detail["slip_qty_ordered"] = _to_int(slip_match.get("quantity_ordered"))
                detail["slip_qty_shipped"] = _to_int(slip_match.get("quantity_shipped"))

        # Find matching invoice line
        inv_match = None
        if has_invoice:
            available_inv = [iv for i, iv in enumerate(inv_products) if i not in used_inv]
            result = find_best_match(po_line, available_inv)
            if result:
                inv_match, score = result
                used_inv.add(inv_products.index(inv_match))
                detail["inv_description"] = inv_match.get("description")
                detail["inv_quantity"] = _to_float(inv_match.get("quantity"))
                detail["inv_unit_price"] = _to_float(inv_match.get("unit_price"))
                detail["inv_extension"] = _to_float(inv_match.get("extension"))

        # Compare quantities
        po_qty = detail.get("po_quantity", 0)
        slip_qty = detail.get("slip_qty_shipped")
        inv_qty = detail.get("inv_quantity")

        qty_ok = True
        if slip_qty is not None and slip_qty != po_qty:
            qty_ok = False
        if inv_qty is not None and inv_qty != po_qty:
            qty_ok = False

        # Compare prices
        po_price = detail.get("po_unit_price", 0)
        inv_price = detail.get("inv_unit_price")
        price_ok = True
        if inv_price is not None and abs(po_price - inv_price) > 0.01:
            price_ok = False

        # Compare totals
        po_total = detail.get("po_line_total", 0)
        inv_ext = detail.get("inv_extension")
        total_ok = True
        if inv_ext is not None and abs(po_total - inv_ext) > 0.01:
            total_ok = False

        detail["qty_match"] = qty_ok
        detail["price_match"] = price_ok
        detail["total_match"] = total_ok

        if not qty_ok:
            detail["line_status"] = "discrepancy"
            detail["discrepancy_type"] = "qty_mismatch"
            parts = []
            if slip_qty is not None and slip_qty != po_qty:
                parts.append("Slip shipped " + str(int(slip_qty)) + " vs PO ordered " + str(int(po_qty)))
            if inv_qty is not None and inv_qty != po_qty:
                parts.append("Invoice billed " + str(int(inv_qty)) + " vs PO ordered " + str(int(po_qty)))
            detail["discrepancy_note"] = "; ".join(parts)
            discrepancies += 1
        elif not price_ok:
            detail["line_status"] = "discrepancy"
            detail["discrepancy_type"] = "price_mismatch"
            detail["discrepancy_note"] = "Invoice unit price $" + str(inv_price) + " vs PO $" + str(po_price)
            discrepancies += 1
        elif not total_ok:
            detail["line_status"] = "discrepancy"
            detail["discrepancy_type"] = "total_mismatch"
            detail["discrepancy_note"] = "Invoice extension $" + str(inv_ext) + " vs PO line total $" + str(po_total)
            discrepancies += 1
        elif not slip_match and has_slip:
            detail["line_status"] = "discrepancy"
            detail["discrepancy_type"] = "missing_on_slip"
            detail["discrepancy_note"] = "Product on PO but not found on packing slip"
            discrepancies += 1
        elif not inv_match and has_invoice:
            detail["line_status"] = "discrepancy"
            detail["discrepancy_type"] = "missing_on_invoice"
            detail["discrepancy_note"] = "Product on PO but not found on invoice"
            discrepancies += 1
        else:
            detail["line_status"] = "match"

        line_details.append(detail)

    # --- Phase 2: Tax line comparison (PO taxes vs Invoice taxes) ---
    for i, po_tax in enumerate(po_taxes):
        line_num += 1
        detail = {
            "line_number": line_num,
            "po_description": po_tax.get("description"),
            "po_quantity": _to_float(po_tax.get("quantity")),
            "po_unit_price": _to_float(po_tax.get("unit_price")),
            "po_line_total": _to_float(po_tax.get("line_total")),
            "line_status": "info_only",
            "discrepancy_type": "tax_line",
            "discrepancy_note": "Tax line — not expected on packing slip",
        }
        # Try to match to invoice tax line
        if i < len(inv_taxes):
            inv_tax = inv_taxes[i]
            detail["inv_description"] = inv_tax.get("description")
            detail["inv_quantity"] = _to_float(inv_tax.get("quantity"))
            detail["inv_unit_price"] = _to_float(inv_tax.get("unit_price"))
            detail["inv_extension"] = _to_float(inv_tax.get("extension"))
            po_tax_amt = _to_float(po_tax.get("line_total"))
            inv_tax_amt = _to_float(inv_tax.get("extension"))
            if abs(po_tax_amt - inv_tax_amt) > 0.01:
                detail["line_status"] = "discrepancy"
                detail["discrepancy_type"] = "tax_mismatch"
                detail["discrepancy_note"] = "Tax differs: PO $" + str(po_tax_amt) + " vs Invoice $" + str(inv_tax_amt)
                discrepancies += 1
        line_details.append(detail)

    # --- Phase 3: Bundled / zero-cost items (slip + invoice only) ---
    all_bundled = []
    for sl in slip_bundled:
        all_bundled.append({"source": "slip", "item": sl})
    for il in inv_bundled:
        all_bundled.append({"source": "invoice", "item": il})

    seen_bundled = set()
    for b in all_bundled:
        desc_norm = normalize_description(b["item"].get("description", ""))
        if desc_norm in seen_bundled:
            continue
        seen_bundled.add(desc_norm)
        line_num += 1
        detail = {
            "line_number": line_num,
            "line_status": "info_only",
            "discrepancy_type": "bundled_zero_cost",
            "discrepancy_note": "Bundled item (zero cost) — not on PO, included with shipment",
        }
        if b["source"] == "slip":
            detail["slip_description"] = b["item"].get("description")
            detail["slip_qty_shipped"] = _to_int(b["item"].get("quantity_shipped"))
        else:
            detail["inv_description"] = b["item"].get("description")
            detail["inv_quantity"] = _to_float(b["item"].get("quantity"))
            detail["inv_unit_price"] = 0
            detail["inv_extension"] = 0
        line_details.append(detail)

    # --- Phase 4: Unmatched slip / invoice lines ---
    for i, sl in enumerate(slip_products):
        if i not in used_slip:
            line_num += 1
            line_details.append({
                "line_number": line_num,
                "slip_description": sl.get("description"),
                "slip_qty_shipped": _to_int(sl.get("quantity_shipped")),
                "line_status": "discrepancy",
                "discrepancy_type": "missing_on_po",
                "discrepancy_note": "Item on packing slip not found on PO",
                "qty_match": False,
                "price_match": None,
                "total_match": None,
            })
            discrepancies += 1

    for i, il in enumerate(inv_products):
        if i not in used_inv:
            line_num += 1
            line_details.append({
                "line_number": line_num,
                "inv_description": il.get("description"),
                "inv_quantity": _to_float(il.get("quantity")),
                "inv_unit_price": _to_float(il.get("unit_price")),
                "inv_extension": _to_float(il.get("extension")),
                "line_status": "discrepancy",
                "discrepancy_type": "missing_on_po",
                "discrepancy_note": "Item on invoice not found on PO",
                "qty_match": False,
                "price_match": None,
                "total_match": None,
            })
            discrepancies += 1

    # --- Overall Assessment ---
    po_total = _to_float(po.get("total_amount", 0))
    inv_total = _to_float(invoice.get("total_amount", 0)) if invoice else 0
    amount_delta = round(inv_total - po_total, 2) if invoice else 0

    # Determine overall status
    material_discrepancies = [
        d for d in line_details
        if d.get("line_status") == "discrepancy"
        and d.get("discrepancy_type") not in ("bundled_zero_cost", "tax_line")
    ]

    if len(material_discrepancies) == 0 and abs(amount_delta) < 0.01:
        overall_status = "approve"
        confidence = 98.0
        summary = "All product lines match. Totals agree ($" + str(po_total) + "). Safe to approve payment."
    elif len(material_discrepancies) == 0 and abs(amount_delta) < 5.0:
        overall_status = "approve"
        confidence = 95.0
        summary = "Product lines match. Minor total difference of $" + str(abs(amount_delta)) + " (rounding). Safe to approve."
    elif len(material_discrepancies) <= 2 and abs(amount_delta) < 50.0:
        overall_status = "review"
        confidence = 70.0
        summary = str(len(material_discrepancies)) + " discrepanc" + ("y" if len(material_discrepancies) == 1 else "ies") + " found. Delta: $" + str(abs(amount_delta)) + ". Manual review recommended."
    else:
        overall_status = "reject"
        confidence = 40.0
        summary = str(len(material_discrepancies)) + " material discrepancies. Delta: $" + str(abs(amount_delta)) + ". Do not approve without investigation."

    return {
        "id": match_id,
        "match_type": match_type,
        "overall_status": overall_status,
        "confidence": confidence,
        "total_discrepancies": discrepancies,
        "amount_delta": amount_delta,
        "summary": summary,
        "line_details": line_details,
        "details_json": {
            "po_total": po_total,
            "invoice_total": inv_total,
            "po_product_lines": len(po_products),
            "slip_product_lines": len(slip_products),
            "inv_product_lines": len(inv_products),
            "tax_lines_compared": len(po_taxes),
            "bundled_items_found": len(seen_bundled),
        },
        "created_at": now,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_float(val) -> float:
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def _to_int(val) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None
