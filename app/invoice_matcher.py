"""
VerifyAP - 3-Way Match Engine
Purpose: Compare Invoice vs PO vs Packing Slip for approval/review/rejection.
"""


def match_invoice(invoice_data, purchase_orders, packing_slips):
    """
    Perform 3-way match: Invoice vs Purchase Order vs Packing Slip.
    
    Returns:
        Dict with status (APPROVE/REVIEW/REJECT), discrepancies, and details.
    """
    po_number = invoice_data.get("po_number", "")
    discrepancies = []
    severity = "APPROVE"  # Start optimistic

    # --- Step 1: Find the PO ---
    if not po_number or po_number not in purchase_orders:
        return {
            "status": "REJECT",
            "has_discrepancy": True,
            "discrepancies": [
                {
                    "type": "PO Not Found",
                    "message": "Invoice references PO '" + str(po_number) + "' which is not in the system.",
                }
            ],
        }

    po = purchase_orders[po_number]

    # --- Step 2: Find matching packing slip ---
    matching_slip = None
    for slip in packing_slips:
        if slip.get("po_number") == po_number:
            matching_slip = slip
            break

    if not matching_slip:
        discrepancies.append({
            "type": "No Packing Slip",
            "message": "No delivery receipt found for PO " + po_number + ". Cannot verify receipt of goods.",
        })
        severity = "REVIEW"

    # --- Step 3: Compare invoice items to PO ---
    invoice_items = invoice_data.get("items", [])
    po_items = po.get("items", [])

    for inv_item in invoice_items:
        inv_desc = (inv_item.get("description") or "").lower()
        inv_qty = inv_item.get("quantity", 0)
        inv_price = inv_item.get("unit_price", 0)
        try:
            inv_qty = float(inv_qty)
        except (ValueError, TypeError):
            inv_qty = 0
        try:
            inv_price = float(inv_price)
        except (ValueError, TypeError):
            inv_price = 0

        po_matched = False
        for po_item in po_items:
            po_desc = (po_item.get("description") or "").lower()
            po_qty = po_item.get("quantity", 0)
            po_price = po_item.get("unit_price", 0)
            try:
                po_qty = float(po_qty)
            except (ValueError, TypeError):
                po_qty = 0
            try:
                po_price = float(po_price)
            except (ValueError, TypeError):
                po_price = 0

            if po_desc and inv_desc and (po_desc in inv_desc or inv_desc in po_desc):
                po_matched = True

                if inv_qty > po_qty:
                    discrepancies.append({
                        "type": "Over-Billed Quantity",
                        "message": "'" + inv_item.get("description", "") + "': invoiced " + str(inv_qty) + " but ordered " + str(po_qty),
                    })
                    severity = "REJECT"

                if inv_price > 0 and po_price > 0 and inv_price > po_price * 1.05:
                    discrepancies.append({
                        "type": "Price Variance",
                        "message": "'" + inv_item.get("description", "") + "': invoiced at $" + str(inv_price) + " vs PO price $" + str(po_price),
                    })
                    if severity != "REJECT":
                        severity = "REVIEW"
                break

        if not po_matched and inv_desc:
            discrepancies.append({
                "type": "Item Not on PO",
                "message": "'" + inv_item.get("description", "") + "' billed but not found on PO " + po_number,
            })
            severity = "REJECT"

    # --- Step 4: Compare invoice to packing slip (if available) ---
    if matching_slip:
        slip_items = matching_slip.get("items", [])
        for inv_item in invoice_items:
            inv_desc = (inv_item.get("description") or "").lower()
            inv_qty = inv_item.get("quantity", 0)
            try:
                inv_qty = float(inv_qty)
            except (ValueError, TypeError):
                inv_qty = 0

            slip_matched = False
            for slip_item in slip_items:
                slip_desc = (slip_item.get("description") or slip_item.get("item") or "").lower()
                slip_qty = slip_item.get("quantity", 0)
                try:
                    slip_qty = float(slip_qty)
                except (ValueError, TypeError):
                    slip_qty = 0

                if slip_desc and inv_desc and (slip_desc in inv_desc or inv_desc in slip_desc):
                    slip_matched = True
                    if inv_qty > slip_qty:
                        discrepancies.append({
                            "type": "Billed > Received",
                            "message": "'" + inv_item.get("description", "") + "': invoiced " + str(inv_qty) + " but only received " + str(slip_qty),
                        })
                        severity = "REJECT"
                    break

    has_discrepancy = len(discrepancies) > 0
    if not has_discrepancy:
        severity = "APPROVE"

    return {
        "status": severity,
        "has_discrepancy": has_discrepancy,
        "discrepancies": discrepancies,
        "po_number": po_number,
        "has_packing_slip": matching_slip is not None,
    }
