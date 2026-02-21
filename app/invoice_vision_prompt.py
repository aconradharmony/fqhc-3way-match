"""
Vision prompt for extracting invoice data
"""

def get_invoice_vision_prompt():
    """Returns the prompt for Claude to extract invoice data"""
    return """You are analyzing an invoice image. Extract ALL information in JSON format.

CRITICAL: Return ONLY valid JSON, no markdown, no explanation, no preamble.

Extract:
{
  "invoice_number": "exact invoice number from document",
  "po_number": "PO number if referenced (look for 'PO#', 'Purchase Order', etc.)",
  "vendor": "company name issuing the invoice",
  "invoice_date": "date in YYYY-MM-DD format if visible",
  "due_date": "payment due date if shown",
  "bill_to": "customer/facility name being billed",
  "line_items": [
    {
      "description": "item description",
      "quantity": numeric quantity,
      "unit_price": numeric price per unit,
      "line_total": numeric line total
    }
  ],
  "subtotal": numeric subtotal before tax/shipping,
  "tax_amount": numeric tax amount (0 if not shown),
  "shipping_amount": numeric shipping/freight (0 if not shown),
  "total_amount": numeric final total amount due,
  "payment_terms": "net 30, net 60, etc.",
  "notes": ["any special notes, discounts, or important details"]
}

EXTRACTION RULES:
1. For line_items: Extract EVERY line item visible
2. Include item codes/SKUs in description if present
3. Calculate line_total as quantity × unit_price if not explicitly shown
4. If subtotal not shown, calculate as sum of all line_totals
5. Ensure total_amount matches the invoice total (subtotal + tax + shipping)
6. Look carefully for PO numbers - they may be in header, footer, or line items
7. All numeric values must be numbers, not strings
8. Return null for fields not found (don't guess)

VALIDATION:
- Verify: subtotal + tax + shipping = total_amount (within rounding)
- Verify: sum of all line_totals = subtotal (within rounding)

Return ONLY the JSON object."""
