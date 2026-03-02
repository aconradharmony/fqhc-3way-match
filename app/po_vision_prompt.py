"""
VerifyAP - Purchase Order Vision Prompt
Purpose: Claude Vision prompt to extract structured PO data from PDFs, photos, and scanned documents.
"""


def get_po_vision_prompt():
    """Return the prompt used to extract purchase order data from documents via Claude Vision."""

    return """You are an expert accounts payable document processor. Analyze this purchase order document and extract ALL purchase order data into structured JSON.

IMPORTANT RULES:
- Extract EVERY purchase order found in the document. A single document may contain one or multiple POs.
- Be thorough with line items — capture every item row you can find.
- For quantities and prices, extract the numeric values only (no currency symbols or commas in numbers).
- If a field is not clearly visible or not present, use an empty string "" for text fields or 0 for numeric fields.
- PO numbers may appear as "PO#", "PO Number", "Purchase Order", "Order #", or similar labels.
- Vendor may appear as "Vendor", "Supplier", "Ship From", "Sold By", or similar.

Return ONLY valid JSON (no markdown, no explanation, no extra text).

If the document contains a SINGLE purchase order, return:
{
    "po_number": "PO-12345",
    "vendor": "Vendor Name",
    "date": "2026-01-15",
    "ship_to": "Facility Name or Address",
    "total": 1234.56,
    "items": [
        {
            "description": "Item description",
            "quantity": 10,
            "unit_price": 25.50,
            "total": 255.00,
            "item_number": "SKU-001",
            "unit": "EA"
        }
    ]
}

If the document contains MULTIPLE purchase orders, return a JSON array:
[
    {
        "po_number": "PO-12345",
        "vendor": "Vendor Name",
        "date": "2026-01-15",
        "ship_to": "",
        "total": 0,
        "items": [
            {
                "description": "Item description",
                "quantity": 10,
                "unit_price": 25.50,
                "total": 255.00,
                "item_number": "",
                "unit": "EA"
            }
        ]
    }
]

FIELD NOTES:
- "item_number": SKU, catalog number, part number, or item code if present
- "unit": Unit of measure (EA, BX, CS, PK, etc.) if present
- "total" at item level: quantity * unit_price (calculate if not shown)
- "total" at PO level: sum of all line item totals, or the document total if shown
- "date": Order date, PO date, or issue date in YYYY-MM-DD format if possible

Extract the data now from the provided document."""
