"""
Vision Prompt Engineering Module
Specialized prompt for processing low-quality packing slip photos from clinic environments
"""


def get_vision_prompt() -> str:
    """
    Returns the optimized prompt for Claude Vision API to handle:
    - Low-quality photos (shadows, blur, glare)
    - Handwritten annotations
    - Various packing slip formats
    - Partial visibility
    """
    
    return """You are processing a packing slip photo taken in a busy healthcare clinic environment. These photos are often taken quickly by nurses or clinic staff using their phones, so they may have quality issues like shadows, blur, glare, wrinkles, or partial visibility.

Your task is to extract purchase order information from this image with maximum accuracy despite these challenges.

**EXTRACTION REQUIREMENTS:**

Extract the following information and return it as valid JSON:

1. **PO Number**: The purchase order number (look for "PO#", "PO Number", "Purchase Order", or similar labels). May include letters, numbers, or hyphens. If unclear, provide your best interpretation.

2. **Vendor Name**: The company/vendor sending the shipment (often at the top of the slip, in the "from" section, or in a logo/letterhead).

3. **Line Items**: Extract ALL items listed with their quantities. For each item, extract:
   - `description`: Item name/description (be generous with partial reads)
   - `quantity_received`: The quantity number (may be handwritten or printed)
   - `has_handwritten_notes`: true if there are ANY handwritten marks, checkmarks, circles, or annotations on or near this line item
   - `handwritten_notes`: If handwritten marks exist, describe them (e.g., "checkmark", "circled", "underlined", "note: partial shipment", "damaged")

**HANDLING QUALITY ISSUES:**

- **Shadows/Dark Areas**: Use context clues from visible portions. If only part of a word is visible, make an educated guess based on typical medical supply terminology.

- **Blur**: Focus on the clearest parts first. Numbers are often more distinguishable than text.

- **Glare/Reflections**: Look around glare spots. Information is often repeated in multiple places on packing slips.

- **Wrinkles/Folds**: Text may be distorted but still partially readable. Piece together visible segments.

- **Handwriting**: Clinic staff often write checkmarks (✓), circle quantities, or add notes like "partial", "damaged", "OK", "short 2". Be very attentive to ANY handwritten marks as these indicate important receiving notes.

- **Partial Visibility**: If the image is cropped or angled, extract what you can see. Don't skip line items just because they're partially visible.

**CONFIDENCE HANDLING:**

If you cannot determine a field with confidence:
- For PO Number or Vendor: Return your best guess with a note in a `confidence_notes` field
- For line items: Include partial information rather than omitting the item entirely
- For quantities: If unclear, return the most likely number and note "quantity_uncertain": true

**OUTPUT FORMAT:**

Return ONLY valid JSON in this exact structure:

```json
{
  "po_number": "PO12345",
  "vendor_name": "McKesson Medical Supply",
  "line_items": [
    {
      "description": "Nitrile Gloves, Large, Box of 100",
      "quantity_received": 5,
      "has_handwritten_notes": true,
      "handwritten_notes": "checkmark and circled quantity"
    },
    {
      "description": "Gauze Pads 4x4",
      "quantity_received": 10,
      "has_handwritten_notes": false,
      "handwritten_notes": null
    }
  ],
  "image_quality_issues": ["shadow in bottom left corner", "slight blur"],
  "confidence_notes": "PO number partially obscured but appears to be PO12345"
}
```

**CRITICAL REMINDERS:**

1. Extract ALL line items visible in the image, even if partially obscured
2. Pay special attention to handwritten marks - these are crucial for receiving verification
3. Be generous with interpretation - a partially visible item is better than a missing item
4. Return valid JSON only - no markdown formatting, no explanations outside the JSON
5. If multiple PO numbers appear, extract the PRIMARY one (usually largest or most prominent)

Now, analyze the packing slip image and extract the information following these guidelines."""


def get_reprocess_prompt(original_result: dict, user_feedback: str) -> str:
    """
    Generate a prompt for reprocessing with user feedback
    Useful if the initial extraction missed something
    """
    
    return f"""The initial extraction returned:

{original_result}

However, the user has provided this feedback:

"{user_feedback}"

Please re-analyze the packing slip image with this feedback in mind and return an updated JSON extraction. Pay special attention to the areas or items mentioned in the feedback.

Return ONLY valid JSON in the same format as before."""


def get_validation_prompt(extracted_data: dict, po_data: dict) -> str:
    """
    Generate a prompt for validation against known PO data
    Can help Claude identify likely errors in its extraction
    """
    
    return f"""You previously extracted this data from a packing slip:

{extracted_data}

This data is being matched against Purchase Order {po_data.get('po_number')} for vendor "{po_data.get('vendor_name')}".

The PO contains these line items:
{po_data.get('line_items')}

Please review your extraction and identify any likely errors or misreads. Consider:
1. Does the vendor name approximately match?
2. Do the item descriptions align with what would be on this PO?
3. Are there any quantity discrepancies that seem like OCR errors (e.g., 1 vs 7, 0 vs O)?

Return a JSON object with:
- `validation_warnings`: List of potential issues you notice
- `suggested_corrections`: Any corrections you recommend
- `confidence_score`: 0-100 score for overall extraction accuracy
"""
