# Vision Prompt Strategy for Low-Quality Clinic Photos

## Overview

The FQHC 3-Way Match system processes packing slip photos taken in real-world clinic environments. These photos are typically taken quickly by busy nursing staff using smartphones, resulting in various quality challenges. This document explains the prompt engineering strategy designed to handle these scenarios.

## Common Photo Quality Issues in Healthcare Settings

### 1. **Lighting Problems**
- **Shadow casting**: Overhead fluorescent lights create dark areas
- **Backlighting**: Photos taken near windows
- **Uneven illumination**: Mixed natural/artificial light
- **Glare hotspots**: Reflections from glossy paper

**Prompt Strategy:**
```
"Use context clues from visible portions. If only part of a word is visible, 
make an educated guess based on typical medical supply terminology."
```

### 2. **Camera Limitations**
- **Motion blur**: Staff taking quick photos while multitasking
- **Focus issues**: Auto-focus failing on crumpled paper
- **Low resolution**: Older phones or compressed MMS images
- **Distortion**: Wide-angle lenses on phones

**Prompt Strategy:**
```
"Focus on the clearest parts first. Numbers are often more distinguishable 
than text. Look around blare spots - information is often repeated in 
multiple places on packing slips."
```

### 3. **Document Condition**
- **Wrinkles/folds**: From shipping or handling
- **Tears**: Damaged during unpacking
- **Stains**: Coffee, handling marks
- **Transparency**: Thin paper showing through from reverse side

**Prompt Strategy:**
```
"Text may be distorted but still partially readable. Piece together 
visible segments."
```

### 4. **Composition Issues**
- **Partial visibility**: Document cropped by photo frame
- **Angle/perspective**: Not taken straight-on
- **Obstructions**: Fingers, other papers visible
- **Background clutter**: Busy clinic environment

**Prompt Strategy:**
```
"If the image is cropped or angled, extract what you can see. Don't skip 
line items just because they're partially visible."
```

## The Vision Prompt Architecture

### 1. Context Setting (Healthcare-Specific)

```
"You are processing a packing slip photo taken in a busy healthcare clinic 
environment. These photos are often taken quickly by nurses or clinic staff 
using their phones, so they may have quality issues..."
```

**Why this works:**
- Sets realistic expectations for photo quality
- Primes the model to be forgiving of imperfections
- Establishes the use case (medical supplies, not general retail)
- Creates empathy for the user (busy healthcare worker)

### 2. Extraction Requirements (Structured Output)

```json
{
  "po_number": "PO12345",
  "vendor_name": "McKesson Medical Supply",
  "line_items": [...],
  "image_quality_issues": [...],
  "confidence_notes": "..."
}
```

**Why this works:**
- JSON format ensures parseable output
- Explicit fields reduce ambiguity
- Quality notes help debugging
- Confidence field allows graceful degradation

### 3. Domain-Specific Guidance

```
"Typical medical supply terminology: Nitrile, Gauze, Sterile, Prep Pads, 
Syringes, Gloves..."
```

**Why this works:**
- Helps with OCR error correction
- "Nitnle" → "Nitrile" (common OCR mistake)
- Provides context for partial reads
- "Gau__ P_ds" → "Gauze Pads"

### 4. Handwritten Detection (Critical Feature)

```
"Be very attentive to ANY handwritten marks as these indicate important 
receiving notes. Clinic staff often write checkmarks (✓), circle quantities, 
or add notes like 'partial', 'damaged', 'OK', 'short 2'."
```

**Why this is critical:**
- Handwritten notes indicate manual verification
- Checkmarks = item was inspected
- Circles = attention needed
- Notes like "damaged" are crucial for finance

**Detection approach:**
- Visual: Look for pen/pencil marks distinct from printed text
- Color: Often blue/black pen vs printed black
- Position: Usually near quantities or item descriptions
- Style: Irregular, non-machine-generated marks

### 5. Confidence Handling (Graceful Degradation)

```
If you cannot determine a field with confidence:
- For PO Number or Vendor: Return your best guess with a note
- For line items: Include partial information rather than omitting
- For quantities: If unclear, return the most likely number and note uncertainty
```

**Why this works:**
- Better to flag uncertainty than fail silently
- Partial data > no data
- Finance team can investigate flagged items
- Prevents complete failures on challenging photos

## Prompt Testing Scenarios

### Scenario 1: Heavy Shadow
**Challenge:** Bottom half of slip in shadow, quantities barely visible
**Prompt Guidance:** "Use context clues from visible portions"
**Expected Behavior:**
- Read PO number and vendor from top (usually clearest)
- For shadowed quantities, use repetition (qty often appears multiple places)
- Flag uncertainty in confidence notes

### Scenario 2: Severe Blur
**Challenge:** Entire image out of focus
**Prompt Guidance:** "Focus on the clearest parts first. Numbers are often more distinguishable than text"
**Expected Behavior:**
- Start with numbers (they have distinct shapes)
- Use positional cues (PO# usually top right)
- Match blurry text to known medical supply terms

### Scenario 3: Wrinkled Paper
**Challenge:** Text distorted by folds
**Prompt Guidance:** "Text may be distorted but still partially readable. Piece together visible segments"
**Expected Behavior:**
- Read text on either side of fold
- Reconstruct middle from context
- "Nit__le Gl__es" + position + context → "Nitrile Gloves"

### Scenario 4: Partial Visibility
**Challenge:** Photo only shows top 60% of slip
**Prompt Guidance:** "Extract what you can see. Don't skip line items just because they're partially visible"
**Expected Behavior:**
- Extract all visible items
- Note in confidence field: "Bottom of slip not visible"
- Still process what's available

### Scenario 5: Handwritten Annotations
**Challenge:** Nurse circled quantity and wrote "short 2"
**Prompt Guidance:** "Be very attentive to ANY handwritten marks"
**Expected Behavior:**
```json
{
  "description": "Gauze Pads 4x4",
  "quantity_received": 8,
  "has_handwritten_notes": true,
  "handwritten_notes": "Quantity circled, note says 'short 2'"
}
```

## PO Number Format Variations

The prompt handles multiple formats:

| Format | Example | Normalization |
|--------|---------|---------------|
| Standard | PO12345 | 12345 |
| With hyphen | PO-12345 | 12345 |
| With hash | #12345 | 12345 |
| Spaces | PO 12345 | 12345 |
| Lowercase | po12345 | 12345 |
| No prefix | 12345 | 12345 |

**Extraction guidance in prompt:**
```
"Look for 'PO#', 'PO Number', 'Purchase Order', or similar labels. 
May include letters, numbers, or hyphens. If unclear, provide your 
best interpretation."
```

## Vendor Name Fuzzy Matching

After extraction, the system performs fuzzy matching to handle:

### Common Variations:
- "McKesson Corp" vs "McKesson Corporation"
- "Cardinal Health Inc." vs "Cardinal Health"
- "Owens & Minor" vs "Owens and Minor"

### Normalization Rules:
1. Remove common suffixes: Inc, Corp, LLC, Ltd, Co.
2. Convert to lowercase
3. Check substring matching
4. Use word overlap algorithm

**Prompt doesn't need to handle this** - it's done in Python matching logic.

## Quality Metrics for Vision Processing

### Success Criteria:
1. **PO Number Extraction**: 95%+ accuracy target
2. **Vendor Extraction**: 90%+ accuracy (fuzzy matching helps)
3. **Line Items**: 85%+ complete extraction
4. **Quantities**: 95%+ accuracy (critical for matching)
5. **Handwritten Detection**: 80%+ recall (better to over-flag than miss)

### Failure Modes:
1. **Complete failure**: Image too degraded → Return error
2. **Partial failure**: Some fields unclear → Return with confidence notes
3. **Hallucination**: Model invents data → Use confidence thresholds

## Prompt Maintenance

### Version Control:
Track prompt changes in `vision_prompt.py`:

```python
PROMPT_VERSION = "2.0"
PROMPT_CHANGELOG = """
v2.0 - 2024-02-15
- Added handwritten detection emphasis
- Enhanced shadow handling guidance
- Added medical supply terminology context

v1.0 - 2024-01-15
- Initial prompt for general packing slip processing
"""
```

### A/B Testing Strategy:
1. Run parallel prompts on same images
2. Compare extraction accuracy
3. Measure handwritten detection recall
4. Track processing time
5. Iterate based on real clinic photos

## Production Optimization

### Cost Considerations:
- Claude Vision API charges per image
- Estimated cost: ~$0.015 per packing slip
- At 100 slips/day: ~$1.50/day = $45/month
- ROI: Saves 2-3 hours/day of manual data entry

### Performance Tuning:
```python
# In production, cache common patterns
COMMON_VENDORS = {
    "mck": "McKesson Medical Supply",
    "card": "Cardinal Health",
    "med": "Medline Industries"
}

# Use cache to speed up vendor normalization
```

### Error Recovery:
1. **First attempt**: Full vision prompt
2. **If fails**: Retry with simplified prompt
3. **If still fails**: Flag for manual review
4. **Store original image** for later reprocessing

## Real-World Example

### Input Image:
- Partially shadowed
- Slight blur on bottom
- Nurse's handwritten checkmark on line 1
- Coffee stain in corner

### Vision API Response:
```json
{
  "po_number": "PO12345",
  "vendor_name": "McKesson Medical Supply",
  "line_items": [
    {
      "description": "Nitrile Gloves Large Box of 100",
      "quantity_received": 10,
      "has_handwritten_notes": true,
      "handwritten_notes": "checkmark next to quantity"
    },
    {
      "description": "Gauze Pads 4x4 Sterile",
      "quantity_received": 20,
      "has_handwritten_notes": false,
      "handwritten_notes": null
    },
    {
      "description": "Alcohol Prep",
      "quantity_received": 15,
      "has_handwritten_notes": false,
      "handwritten_notes": null
    }
  ],
  "image_quality_issues": [
    "shadow in bottom left corner",
    "slight blur on bottom third",
    "stain visible but doesn't obscure text"
  ],
  "confidence_notes": "Line 3 description may be truncated - appears to be 'Alcohol Prep Pads' based on context"
}
```

### Matching Result:
```json
{
  "po_found": true,
  "vendor_match": true,
  "discrepancies": [],
  "matched_items": 3,
  "has_discrepancies": false
}
```

## Future Enhancements

1. **Multi-language support**: Spanish for clinic staff
2. **Barcode detection**: Extract product UPC/SKU
3. **Signature verification**: Confirm receiver signature present
4. **Damage detection**: Visual assessment of product condition
5. **Auto-rotation**: Correct upside-down images
6. **Multi-page handling**: Process multi-page slips

## Conclusion

The vision prompt is engineered specifically for the challenging environment of healthcare facilities. By acknowledging quality issues upfront and providing clear guidance for handling them, we achieve reliable extraction even from imperfect images.

The key insight: **Graceful degradation is better than binary success/failure**. Partial data with confidence notes enables the finance team to make informed decisions, while perfect extraction remains the goal.
