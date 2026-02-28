"""
VerifyAP - Invoice Vision Prompt
Purpose: Claude Vision prompt for extracting data from vendor invoices.
"""


def get_invoice_vision_prompt():
    """Return the prompt for invoice OCR extraction."""

    return """You are an expert accounts payable document processor. Analyze this vendor invoice and extract ALL data into structured JSON.

Extract the following:

1. **invoice_number** — The invoice number
2. **po_number** — The purchase order number referenced on the invoice
3. **vendor** — The vendor/supplier name
4. **vendor_address** — Vendor address if visible
5. **invoice_date** — Invoice date
6. **due_date** — Payment due date if shown
7. **items** — Array of line items, each with:
   - **description** — Item description
   - **quantity** — Quantity billed (as a number)
   - **unit_price** — Unit price (as a number)
   - **total** — Line total (as a number)
8. **subtotal** — Subtotal amount
9. **tax** — Tax amount if shown
10. **shipping** — Shipping charges if shown
11. **total** — Grand total / amount due
12. **payment_terms** — Payment terms if shown (e.g., Net 30)
13. **notes** — Any special notes

Return ONLY valid JSON. No explanation or markdown.
If a field is not found, use null.

Example:
{
    "invoice_number": "INV-2024-0150",
    "po_number": "PO-2024-001",
    "vendor": "Medical Supply Co",
    "vendor_address": "123 Main St, City, ST 12345",
    "invoice_date": "2024-01-25",
    "due_date": "2024-02-24",
    "items": [
        {
            "description": "Exam Gloves, Nitrile, Medium",
            "quantity": 100,
            "unit_price": 0.12,
            "total": 12.00
        }
    ],
    "subtotal": 12.00,
    "tax": 0.96,
    "shipping": 5.00,
    "total": 17.96,
    "payment_terms": "Net 30",
    "notes": null
}"""
