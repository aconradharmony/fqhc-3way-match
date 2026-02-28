"""
VerifyAP - PO Matching Engine
Purpose: Match packing slip data against purchase orders, detect discrepancies.
"""


def match_packing_slip(slip_data, purchase_orders):
    """
    Match a packing slip against stored purchase orders.
    
    Args:
        slip_data: Dict with po_number, vendor, items extracted from packing slip
        purchase_orders: Dict of PO number -> PO data
    
    Returns:
        Dict with status, discrepancies list, and match details
    """
    po_number = slip_data.get("po_number", "")
    discrepancies = []

    # Check if PO exists
    if not po_number or po_number not in purchase_orders:
        return {
            "status": "REVIEW",
            "has_discrepancy": True,
            "discrepancies": [
                {
                    "type": "PO Not Found",
                    "message": "Purchase order '" + str(po_number) + "' not found in database.",
                }
            ],
            "po_found": False,
        }

    po = purchase_orders[po_number]
    slip_items = slip_data.get("items", [])
    po_items = po.get("items", [])

    # Check vendor match
    slip_vendor = (slip_data.get("vendor") or "").lower().strip()
    po_vendor = (po.get("vendor") or "").lower().strip()
    if slip_vendor and po_vendor and slip_vendor != po_vendor:
        # Partial match check
        if slip_vendor not in po_vendor and po_vendor not in slip_vendor:
            discrepancies.append({
                "type": "Vendor Mismatch",
                "message": "Slip vendor '" + slip_data.get("vendor", "") + "' vs PO vendor '" + po.get("vendor", "") + "'",
            })

    # Check item quantities
    for slip_item in slip_items:
        slip_desc = (slip_item.get("description") or slip_item.get("item") or "").lower()
        slip_qty = slip_item.get("quantity", 0)
        try:
            slip_qty = float(slip_qty)
        except (ValueError, TypeError):
            slip_qty = 0

        matched = False
        for po_item in po_items:
            po_desc = (po_item.get("description") or "").lower()
            po_qty = po_item.get("quantity", 0)
            try:
                po_qty = float(po_qty)
            except (ValueError, TypeError):
                po_qty = 0

            # Fuzzy description match
            if po_desc and slip_desc and (po_desc in slip_desc or slip_desc in po_desc):
                matched = True
                if slip_qty != po_qty:
                    discrepancies.append({
                        "type": "Quantity Mismatch",
                        "message": "'" + slip_item.get("description", "") + "': received " + str(slip_qty) + ", ordered " + str(po_qty),
                    })
                break

        if not matched and slip_desc:
            discrepancies.append({
                "type": "Item Not on PO",
                "message": "'" + slip_item.get("description", "") + "' not found on PO " + po_number,
            })

    has_discrepancy = len(discrepancies) > 0
    status = "REVIEW" if has_discrepancy else "APPROVE"

    return {
        "status": status,
        "has_discrepancy": has_discrepancy,
        "discrepancies": discrepancies,
        "po_found": True,
        "po_number": po_number,
    }
