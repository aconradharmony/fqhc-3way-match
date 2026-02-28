"""
VerifyAP - Purchase Order Vision Prompt
Created: Feb 26, 2026
Purpose: Claude Vision prompt for extracting structured data from PO PDFs/images.
"""


def get_po_vision_prompt():
    """Return the prompt used to extract PO data from uploaded documents via Claude Vision."""

    return """You are an expert accounts payable document processor. Analyze this purchase order document and extract ALL data into structured JSON.

Extract the following fields:

1. **po_number** — The purchase order number (e.g., PO-12345, #12345)
2. **vendor** — The vendor/supplier name
3. **vendor_address** — Vendor address if visible
4. **date** — PO date (any format found)
5. **delivery_date** — Expected delivery date if shown
6. **ship_to** — Ship-to address if shown
7. **items** — Array of line items, each with:
   - **description** — Item description
   - **quantity** — Quantity ordered (as a number)
   - **unit_price** — Unit price (as a number, no currency symbol)
   - **total** — Line total if shown (as a number)
   - **item_number** — Item/SKU number if shown
8. **subtotal** — Subtotal if shown
9. **tax** — Tax amount if shown
10. **total** — Grand total if shown
11. **notes** — Any special instructions or notes

Return ONLY valid JSON. Do not include any explanation or markdown formatting.
If a field is not found in the document, use null for that field.
For items array, include every line item you can identify.

Example output format:
{
    "po_number": "PO-2024-001",
    "vendor": "Medical Supply Co",
    "vendor_address": "123 Main St, City, ST 12345",
    "date": "2024-01-15",
    "delivery_date": "2024-01-22",
    "ship_to": "FQHC Clinic, 456 Health Ave",
    "items": [
        {
            "description": "Exam Gloves, Nitrile, Medium",
            "quantity": 100,
            "unit_price": 0.12,
            "total": 12.00,
            "item_number": "GLV-NIT-M"
        }
    ],
    "subtotal": 12.00,
    "tax": 0.96,
    "total": 12.96,
    "notes": "Deliver to receiving dock B"
}"""
