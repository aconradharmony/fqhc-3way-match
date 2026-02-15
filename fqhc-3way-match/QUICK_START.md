# Quick Start Guide - FQHC 3-Way Match System

## Setup (5 minutes)

### 1. Install Dependencies
```bash
cd fqhc-3way-match
pip install -r requirements.txt
```

### 2. Set API Key
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
# Windows: set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Add Your CSV
Replace `data/open_pos.csv` with your Netsuite export, or use the sample data provided.

### 4. Run Tests (Optional but Recommended)
```bash
python test_matcher.py
```

Expected output: `🎉 ALL TESTS PASSED!`

### 5. Start the Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Open Browser
Navigate to: **http://localhost:8000**

## First Upload Test

### Using Sample Data:
The system comes pre-loaded with PO12345 (McKesson Medical Supply) containing:
- Nitrile Gloves Large Box of 100 (Qty: 10)
- Gauze Pads 4x4 Sterile 100ct (Qty: 20)
- Alcohol Prep Pads 200ct (Qty: 15)

### Test Scenarios:

**Perfect Match Test:**
Create a simple text file or image with:
```
PO Number: PO12345
Vendor: McKesson Medical Supply

Items Received:
- Nitrile Gloves Large Box of 100: 10 ✓
- Gauze Pads 4x4 Sterile 100ct: 20 ✓
- Alcohol Prep Pads 200ct: 15 ✓
```

Upload → Should show ✓ Match with no discrepancies

**Discrepancy Test:**
Create image with:
```
PO Number: PO12345
Vendor: McKesson Medical Supply

Items Received:
- Nitrile Gloves Large Box of 100: 8 ✓ (note: 2 damaged)
- Gauze Pads 4x4 Sterile 100ct: 20 ✓
```

Upload → Should flag:
- Quantity discrepancy (8 vs 10)
- Handwritten note detected
- Missing item (Alcohol Prep Pads)

## API Testing with cURL

```bash
# Upload packing slip
curl -X POST "http://localhost:8000/api/upload-packing-slip" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/packing_slip.jpg"

# Get history
curl http://localhost:8000/api/history

# Clear history
curl -X DELETE http://localhost:8000/api/clear-history
```

## Understanding the Dashboard

### Status Badges:
- 🟢 **✓ Match** - Everything matches perfectly
- 🔴 **⚠ Discrepancies** - Issues found (quantities, missing items)
- 🔴 **✗ PO Not Found** - PO number not in database

### Discrepancy Types:
1. **Quantity Mismatch** - "Received 8 but PO ordered 10"
2. **Missing Items** - "Missing from shipment: [item]"
3. **Extra Items** - "Item not in PO: [item]"
4. **Vendor Mismatch** - "Vendor mismatch: Slip shows X but PO is for Y"
5. **Handwritten Notes** - "Handwritten note found - [description]"

## Troubleshooting

### "No PO data loaded"
- Check `data/open_pos.csv` exists
- Verify CSV has correct columns
- Restart server to reload CSV

### "API key error"
- Ensure ANTHROPIC_API_KEY is set
- Verify key starts with `sk-ant-`
- Check key hasn't expired

### "Vision processing failed"
- Check image file is valid (JPG, PNG)
- Ensure image is < 10MB
- Try with better quality photo

### "PO not found"
- Check PO number format in CSV
- Try with/without "PO" prefix
- Verify CSV loaded correctly (check startup logs)

## Next Steps

1. **Export your real Netsuite data** - Replace sample CSV
2. **Test with real packing slips** - Start with clear photos
3. **Train clinic staff** - Show them how to take good photos
4. **Monitor discrepancies** - Review dashboard daily
5. **Integrate with workflow** - Consider email/SMS automation

## Production Checklist

Before deploying to production:

- [ ] Use environment variables for API key (not hardcoded)
- [ ] Set up HTTPS/TLS
- [ ] Add user authentication
- [ ] Configure database (PostgreSQL/MySQL)
- [ ] Set up automated backups
- [ ] Enable logging and monitoring
- [ ] Load test with expected volume
- [ ] Create runbook for ops team
- [ ] Train finance team on dashboard
- [ ] Establish SLA for processing time

## Support

For issues:
1. Check logs: Server console shows detailed errors
2. Review test results: `python test_matcher.py`
3. Verify CSV format matches sample
4. Ensure vision API quota not exceeded

## Sample Data Reference

The included sample CSV has 9 POs from 6 vendors with 20 total line items worth $6,860.10. Perfect for testing all scenarios.
