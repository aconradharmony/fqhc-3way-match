# FQHC 3-Way Match System 🏥

Automated purchase order verification system for Federally Qualified Health Centers (FQHCs) using Netsuite and Claude AI Vision.

## Overview

This system automates the 3-way matching process between:
1. **Purchase Orders** (from Netsuite CSV export)
2. **Packing Slips** (photos from clinic staff)
3. **Receiving Verification** (quantity and quality checks)

### Key Features

- ✅ **Vision AI Processing**: Handles low-quality phone photos with shadows, blur, and glare
- ✅ **Handwritten Note Detection**: Identifies checkmarks, annotations, and receiving notes
- ✅ **Automatic PO Matching**: Fuzzy matching against Netsuite open POs
- ✅ **Discrepancy Alerts**: Flags quantity mismatches and missing items
- ✅ **Finance Dashboard**: Real-time view of all processed slips and issues
- ✅ **RESTful API**: Easy integration with existing systems

## System Architecture

```
┌─────────────────┐
│  Clinic Staff   │  Takes photo of packing slip
│   (Phone/SMS)   │  
└────────┬────────┘
         │
         │ POST /api/upload-packing-slip
         ▼
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│                                         │
│  ┌──────────────┐   ┌───────────────┐  │
│  │ Vision API   │   │  PO Matcher   │  │
│  │  (Claude)    │──▶│  (CSV Logic)  │  │
│  └──────────────┘   └───────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │    Processing History DB         │  │
│  │  (In-memory - production: SQL)   │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
         │
         │ GET /
         ▼
┌─────────────────────┐
│  Finance Dashboard  │  HTML Dashboard with:
│   (Web Browser)     │  - Match status
└─────────────────────┘  - Discrepancy alerts
                         - Photo previews
```

## Installation

### Prerequisites

- Python 3.9+
- Anthropic API Key (get from https://console.anthropic.com)
- Netsuite CSV export of Open Purchase Orders

### Setup Steps

1. **Clone/Download the project**
   ```bash
   cd fqhc-3way-match
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variable**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   # On Windows: set ANTHROPIC_API_KEY=your-api-key-here
   ```

5. **Add your Netsuite CSV**
   - Export Open POs from Netsuite
   - Save as `data/open_pos.csv`
   - Required columns: PO Number, Vendor Name, Vendor ID, PO Date, Expected Delivery, Status, Item ID, Item Description, Quantity Ordered, Unit Price, Line Total

6. **Create upload directory**
   ```bash
   mkdir -p uploads
   ```

## Running the Application

```bash
# From the project root directory
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open your browser to: **http://localhost:8000**

## API Endpoints

### POST `/api/upload-packing-slip`
Upload a packing slip photo for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Image file (JPEG, PNG, etc.)

**Response:**
```json
{
  "success": true,
  "result": {
    "id": 1,
    "timestamp": "20240215_143022",
    "filename": "packing_slip.jpg",
    "vision_data": {
      "po_number": "PO12345",
      "vendor_name": "McKesson Medical Supply",
      "line_items": [...]
    },
    "match_result": {
      "po_found": true,
      "discrepancies": [
        "Nitrile Gloves Large: Received 8 but PO ordered 10 (Difference: -2)"
      ],
      "has_discrepancies": true
    }
  }
}
```

### GET `/`
View the Finance Dashboard (HTML interface)

### GET `/api/history`
Get all processing history as JSON

### DELETE `/api/clear-history`
Clear all processing history

## CSV Format

Your Netsuite export should have these columns:

| Column | Description | Example |
|--------|-------------|---------|
| PO Number | Purchase order identifier | PO12345 |
| Vendor Name | Supplier name | McKesson Medical Supply |
| Vendor ID | Internal vendor ID | VEN-1001 |
| PO Date | Order date | 2024-01-15 |
| Expected Delivery | Expected delivery date | 2024-02-01 |
| Status | PO status | Open |
| Item ID | Internal item SKU | ITM-5001 |
| Item Description | Product description | Nitrile Gloves Large Box of 100 |
| Quantity Ordered | Ordered quantity | 10 |
| Unit Price | Price per unit | 15.99 |
| Line Total | Line item total | 159.90 |

**Note:** Netsuite exports have one row per line item, so a PO with 3 items will have 3 rows.

## Vision Prompt Engineering

The system uses a specialized prompt designed for healthcare clinic environments:

### Handles Common Issues:
- 📸 **Poor lighting** (shadows, dark corners)
- 🌫️ **Blur** (quick phone photos)
- ✨ **Glare** (from plastic slip covers)
- 📄 **Wrinkles/folds** (crumpled documents)
- ✍️ **Handwritten annotations** (checkmarks, notes, circles)
- 🖼️ **Partial visibility** (cropped photos)

### Detection Features:
- Extracts PO numbers (handles formats: PO12345, PO-12345, #12345)
- Identifies vendors (fuzzy matching handles Corp vs Corporation)
- Reads line items and quantities
- **Detects handwritten marks** (crucial for receiving verification)
- Provides confidence notes when uncertain

## Matching Logic

### PO Number Normalization
```python
# Handles variations:
"PO12345" → "12345"
"PO-12345" → "12345"
"#12345" → "12345"
" PO 12345 " → "12345"
```

### Vendor Fuzzy Matching
```python
# Matches despite differences:
"McKesson Corp" ≈ "McKesson Corporation"
"Cardinal Health Inc." ≈ "Cardinal Health"
```

### Item Description Matching
- Uses word overlap algorithm
- Ignores common stop words (the, a, an, of, etc.)
- 60% word match threshold
- Tolerates minor spelling variations

### Discrepancy Detection
1. **Quantity Mismatch**: Received ≠ Ordered
2. **Missing Items**: In PO but not received
3. **Extra Items**: Received but not in PO
4. **Vendor Mismatch**: Slip vendor ≠ PO vendor
5. **Handwritten Alerts**: Any manual annotations

## Production Deployment

### Environment Variables
```bash
ANTHROPIC_API_KEY=your-production-key
DATABASE_URL=postgresql://user:pass@host:5432/db  # For production DB
```

### Production Enhancements Needed:
1. **Database**: Replace in-memory storage with PostgreSQL/MySQL
2. **Authentication**: Add user authentication (OAuth, SAML for healthcare)
3. **File Storage**: Use S3/Azure Blob for uploaded images
4. **Logging**: Add structured logging (e.g., Loguru)
5. **Monitoring**: Add APM (DataDog, New Relic)
6. **Rate Limiting**: Protect endpoints from abuse
7. **HTTPS**: Use TLS certificates
8. **Backup**: Automated backups of processing history

### Docker Deployment
```dockerfile
# Example Dockerfile (create this for production)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Workflow Example

1. **Nurse receives shipment at clinic**
   - Takes photo of packing slip with phone
   - Texts/emails photo to system

2. **System processes automatically**
   - Vision API extracts PO#, vendor, items, quantities
   - Detects any handwritten checkmarks or notes
   - Matches against Netsuite open POs

3. **Finance team reviews dashboard**
   - Sees all received shipments
   - Red alerts for discrepancies
   - Can drill into specific issues

4. **Action on discrepancies**
   - Contact vendor about short shipments
   - Investigate extra items
   - Verify damaged goods (from handwritten notes)
   - Update Netsuite accordingly

## Troubleshooting

### Vision API returns partial data
- **Solution**: Check image quality, ensure PO number is visible
- **Retry**: Re-upload with better lighting/focus

### PO not found in database
- **Check**: Is PO in the CSV export?
- **Check**: CSV format matches expected columns
- **Check**: PO number format (try with/without "PO" prefix)

### Vendor mismatch false positive
- **Cause**: Fuzzy matching too strict
- **Solution**: Adjust `_fuzzy_vendor_match()` threshold in `po_matcher.py`

### No discrepancies showing when there should be
- **Check**: Quantities in CSV are correct data type (float)
- **Check**: Vision API extracted quantities correctly
- **Debug**: View `/api/history` to see raw match data

## Testing

### Sample Test Image
Create a mock packing slip image with:
- PO Number: PO12345
- Vendor: McKesson Medical Supply
- Items: 
  - Nitrile Gloves Large: 8 (write ✓ next to it)
  - Gauze Pads 4x4: 20

Upload via the dashboard and verify:
- ✅ PO found
- ✅ Vendor matched
- ✅ Discrepancy flagged (8 vs 10 gloves)
- ✅ Handwritten checkmark detected

## License & Support

This is a reference implementation for FQHC procurement automation.

For production deployment assistance, contact your healthcare IT team.

## Future Enhancements

- [ ] Email/SMS integration for automatic photo intake
- [ ] Mobile app for clinic staff
- [ ] OCR fallback for non-Claude processing
- [ ] Barcode scanning for item verification
- [ ] Integration with Netsuite API (direct PO updates)
- [ ] Multi-language support (Spanish for clinic staff)
- [ ] Signature capture for receiving verification
- [ ] Analytics dashboard (vendor performance, common discrepancies)

---

**Built with:**
- FastAPI - Modern Python web framework
- Anthropic Claude Vision - AI-powered document processing
- Netsuite - ERP/Procurement system
