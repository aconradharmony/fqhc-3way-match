# VerifyAP - Complete Project Documentation

## 📋 Project Overview

**Project Name:** VerifyAP  
**Purpose:** AI-powered 3-way match system for FQHCs  
**Status:** Production-ready, deployed  
**URL:** https://fqhc-3way-match.onrender.com  
**Alternative:** verify.harmonyhello.ai  

---

## 🏗️ Technical Architecture

### Stack
- **Backend:** FastAPI (Python 3.11)
- **AI/ML:** Anthropic Claude Sonnet 4 (Vision API)
- **Deployment:** Render.com (free tier)
- **Frontend:** Vanilla HTML/CSS/JavaScript
- **Font:** Inter (Google Fonts)
- **Version Control:** GitHub (aconradharmony/fqhc-3way-match)

### File Structure
```
fqhc-3way-match/
├── app/
│   ├── __init__.py
│   ├── main.py                      # Main FastAPI app, dashboard
│   ├── sidebar_component.py         # Reusable sidebar navigation
│   ├── admin_html.py                # PO admin page
│   ├── invoice_html.py              # Invoice processing page
│   ├── invoice_matcher.py           # 3-way matching logic
│   ├── invoice_vision_prompt.py     # Claude prompt for invoices
│   ├── po_matcher.py                # PO matching logic
│   ├── vision_prompt.py             # Claude prompt for packing slips
│   ├── organization.py              # Multi-tenant org settings (future)
│   ├── branding_html.py             # Branding customization page (future)
│   └── branding_utils.py            # Branding utilities (future)
├── data/                            # CSV storage (gitignored)
├── uploads/                         # Image uploads (gitignored)
├── static/                          # Static assets
├── requirements.txt                 # Python dependencies
├── runtime.txt                      # Python version (3.11.0)
├── Procfile                         # Render deployment config
└── render.yaml                      # Render service config
```

---

## 🎨 UI/UX Design

### Color Palette
- **Primary:** Indigo-600 (#4F46E5)
- **Secondary:** Slate-900 (#0F172A)
- **Success:** Emerald-500 (#10B981)
- **Warning:** Amber-500 (#F59E0B)
- **Error:** Rose-500 (#EF4444)
- **Background:** Slate-50 (#F8FAFC)

### Design System
- **Sidebar:** 260px fixed left, dark slate background
- **Typography:** Inter font family
- **Cards:** 12px border-radius, 1px border, subtle shadows
- **Buttons:** 8px border-radius, hover effects, transform animations
- **Stats:** Hover lift effect, color-coded values

### Pages
1. **Dashboard (/)** - Process flow, stats, upload packing slips
2. **Admin (/admin)** - Upload PO CSV, data health stats
3. **Invoices (/invoices)** - Upload invoices, 3-way matching

---

## 🤖 AI Integration

### Claude Vision API
- **Model:** claude-sonnet-4-20250514
- **Use Cases:**
  - Packing slip OCR (extract PO#, vendor, items, quantities)
  - Invoice OCR (extract invoice#, PO#, line items, amounts)
- **Cost:** ~$0.015 per image (~$0.60/month for 200 images)

### Prompts
- **Packing Slips:** `/app/vision_prompt.py` - Extracts structured JSON
- **Invoices:** `/app/invoice_vision_prompt.py` - Extracts invoice data

---

## 📊 Core Features

### Current (Production)
✅ **PO Management**
- Upload NetSuite CSV
- Parse and store POs in memory
- Display data health stats

✅ **Packing Slip Processing**
- Photo upload (drag-and-drop)
- Claude Vision extraction
- Match against POs
- Discrepancy detection

✅ **Invoice Processing**
- PDF/photo upload
- Claude Vision extraction
- 3-way match (PO + Packing Slip + Invoice)
- Status: APPROVE / REVIEW / REJECT

✅ **Modern UI**
- Sidebar navigation
- Process flow visualization
- Stat cards with hover effects
- Professional tables with badges

### Planned (Not Yet Built)
❌ PostgreSQL database (data currently in-memory)
❌ User authentication
❌ Email notifications
❌ Reporting/analytics dashboard
❌ Batch operations
❌ Multi-tenant support

---

## 🔧 Key Technical Details

### Environment Variables (Render)
```
ANTHROPIC_API_KEY=sk-ant-api03-WhAssJH1...
PYTHON_VERSION=3.11.0
```

### Dependencies (requirements.txt)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
anthropic==0.39.0
httpx==0.27.0
python-multipart==0.0.9
```

### Critical Code Patterns

**String Concatenation (NOT f-strings for HTML):**
```python
# CORRECT (avoids syntax errors with CSS hex colors)
html = """<style>color: #667eea;</style>""" + sidebar_html

# WRONG (causes Python syntax errors)
html = f"""<style>color: #667eea;</style>"""
```

**Directory Creation:**
```python
os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)
os.makedirs("data", exist_ok=True)
```

---

## 🚀 Deployment

### GitHub → Render Auto-Deploy
1. Push to GitHub `main` branch
2. Render automatically detects changes
3. Builds: `pip install -r requirements.txt`
4. Starts: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Live in 5-10 minutes

### Common Deployment Issues
- **Syntax errors:** Use string concatenation, not f-strings for HTML
- **Missing directories:** Auto-created in `app/main.py` startup
- **Python version:** Must be 3.11.0 (set in runtime.txt and env var)
- **Package compatibility:** anthropic==0.39.0 required for Python 3.11

---

## 💰 Business Model (Future)

### Target Market
- 1,400+ FQHCs in the US
- Each processes 100-500 invoices/month
- Current solution: Manual (costly, error-prone)

### Pricing Tiers
- **Basic:** $199/month (up to 300 transactions)
- **Professional:** $299/month (up to 1,000 transactions)
- **Enterprise:** Custom pricing

### Value Proposition
- Save 20-40 hours/month of manual work
- Prevent overpayment errors (2-5% typical error rate)
- HIPAA-compliant, healthcare-specific
- ROI in first month

---

## 📈 Roadmap

### Phase 1: MVP Validation (Completed ✅)
- ✅ Build core matching system
- ✅ Deploy to cloud
- ✅ Modern UI
- ✅ All 3 pages functional

### Phase 2: Production Hardening (Next)
- 🔄 Test with real NetSuite data
- 🔄 Add PostgreSQL database
- 🔄 Email notifications
- 🔄 Error handling improvements

### Phase 3: SaaS Features (Future)
- ⏳ User authentication
- ⏳ Multi-tenant support
- ⏳ Stripe billing
- ⏳ Reporting/analytics

### Phase 4: Scale (Future)
- ⏳ First 10 paying customers
- ⏳ API integrations (NetSuite, QuickBooks)
- ⏳ Mobile app
- ⏳ White-label branding per customer

---

## 🐛 Known Issues & Limitations

### Current Limitations
- **No data persistence:** Data lost on server restart (in-memory only)
- **Single-tenant:** One organization only
- **No authentication:** Anyone with URL can access
- **No email alerts:** Manual checking required
- **Limited error handling:** Errors not always user-friendly

### Future Improvements Needed
- PostgreSQL for persistence
- User login system
- Role-based access control
- Email notification system
- Better error messages
- Audit logs

---

## 🔑 Important Context for Future Sessions

### What Works Well
- Claude Vision API for OCR (very accurate)
- FastAPI for rapid development
- Render for easy deployment
- String concatenation for HTML generation

### What to Avoid
- ❌ f-strings for HTML with CSS (causes syntax errors)
- ❌ pypdf library (use alternatives)
- ❌ Pillow (not needed, causes build issues)
- ❌ Python 3.14 (use 3.11.0 specifically)

### Key Files to Reference
- `app/main.py` - Main dashboard logic
- `app/sidebar_component.py` - Reusable navigation
- `app/po_matcher.py` - PO matching algorithm
- `app/invoice_matcher.py` - 3-way match logic

---

## 📞 External Resources

- **GitHub Repo:** https://github.com/aconradharmony/fqhc-3way-match
- **Live Site:** https://fqhc-3way-match.onrender.com
- **Render Dashboard:** https://dashboard.render.com
- **Anthropic API Docs:** https://docs.anthropic.com

---

## 💡 Tips for Working with Claude

1. **Reference this doc** in future chats: "See PROJECT_DOCS.md for context"
2. **Upload key files** when starting new conversations
3. **Be specific** about which page/feature you're working on
4. **Mention deployment** if changes need to go live
5. **Test locally first** before pushing to GitHub/Render

---

**Last Updated:** February 24, 2026  
**Status:** Production-ready, deployed  
**Next Milestone:** Test with real data
