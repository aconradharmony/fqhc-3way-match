"""
VerifyAP - Packing Slip Vision Prompt
Purpose: Claude Vision prompt for extracting data from packing slip photos.
"""


def get_vision_prompt():
    """Return the prompt for packing slip OCR extraction."""

    return """You are an expert document processor for accounts payable. Analyze this packing slip / delivery receipt and extract ALL data into structured JSON.

Extract the following:

1. **po_number** — The purchase order number referenced on the packing slip
2. **vendor** — The vendor/supplier/shipper name
3. **date** — Date on the packing slip
4. **items** — Array of line items, each with:
   - **description** — Item description
   - **quantity** — Quantity received (as a number)
   - **item_number** — Item/SKU number if shown
5. **tracking_number** — Shipping tracking number if shown
6. **notes** — Any notes, damage indicators, or special remarks

Return ONLY valid JSON. No explanation or markdown.
If a field is not found, use null.

Example:
{
    "po_number": "PO-2024-001",
    "vendor": "Medical Supply Co",
    "date": "2024-01-20",
    "items": [
        {
            "description": "Exam Gloves, Nitrile, Medium",
            "quantity": 100,
            "item_number": "GLV-NIT-M"
        }
    ],
    "tracking_number": "1Z999AA10123456784",
    "notes": null
}"""
