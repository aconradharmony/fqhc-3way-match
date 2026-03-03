"""
VerifyAP — Match Detail (Drill-In View)

Shows the full per-line comparison across PO, Packing Slip, and Invoice.
Each row shows the same product across all 3 documents with color-coded
delta indicators. This is the core "drill in" experience.

Example from PO#16817:
  Line 1: M-M-R II — PO Qty 1 / Slip Shipped 1 / Invoice Qty 1 — MATCH
  Line 4: Sterile Diluent — Not on PO / Slip Shipped 1 / Invoice Qty 1 at $0 — INFO (bundled)
"""

from .sidebar_component import get_sidebar_html, get_sidebar_styles


def get_match_detail_html():
    sidebar_html = get_sidebar_html("discrepancies")
    sidebar_styles = get_sidebar_styles()

    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VerifyAP — Match Detail</title>
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    """ + sidebar_styles + """
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'DM Sans', sans-serif; background: #F1F5F9; color: #1E293B; }
        .vap-main { margin-left: 260px; padding: 32px 40px; min-height: 100vh; }

        .page-header { margin-bottom: 28px; }
        .breadcrumb { font-size: 13px; color: #64748B; margin-bottom: 4px; }
        .breadcrumb a { color: #4F46E5; text-decoration: none; }
        .page-header h1 { font-size: 24px; font-weight: 700; }
        .page-header .subtitle { color: #64748B; font-size: 14px; margin-top: 4px; }

        /* Summary banner */
        .match-banner {
            display: flex; align-items: center; gap: 24px;
            padding: 20px 28px; border-radius: 12px; margin-bottom: 28px;
            border: 1px solid;
        }
        .match-banner--approve { background: #F0FDF4; border-color: #BBF7D0; }
        .match-banner--review { background: #FFFBEB; border-color: #FDE68A; }
        .match-banner--reject { background: #FEF2F2; border-color: #FECACA; }

        .banner-icon {
            width: 48px; height: 48px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 24px; flex-shrink: 0;
        }
        .match-banner--approve .banner-icon { background: #D1FAE5; }
        .match-banner--review .banner-icon { background: #FEF3C7; }
        .match-banner--reject .banner-icon { background: #FEE2E2; }

        .banner-text h3 { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
        .banner-text p { font-size: 14px; color: #475569; }

        .banner-stats {
            margin-left: auto; display: flex; gap: 32px; text-align: center;
        }
        .banner-stat-value { font-size: 22px; font-weight: 700; }
        .banner-stat-label { font-size: 11px; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; }

        /* Document cards row */
        .doc-cards {
            display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 28px;
        }
        .doc-card {
            background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 18px;
        }
        .doc-card h4 {
            font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase;
            letter-spacing: 0.5px; margin-bottom: 10px;
        }
        .doc-card .doc-value { font-size: 15px; font-weight: 600; color: #0F172A; margin-bottom: 4px; }
        .doc-card .doc-meta { font-size: 13px; color: #94A3B8; }
        .doc-card .doc-file {
            margin-top: 10px; font-size: 12px; color: #4F46E5;
            text-decoration: none; display: inline-flex; align-items: center; gap: 4px;
        }

        /* Line comparison table */
        .comp-section-header {
            font-size: 16px; font-weight: 600; color: #0F172A; margin-bottom: 14px;
            padding-bottom: 8px; border-bottom: 2px solid #E2E8F0;
        }

        .comp-table-wrap {
            background: white; border: 1px solid #E2E8F0; border-radius: 12px;
            overflow-x: auto; margin-bottom: 28px;
        }
        .comp-table { width: 100%; border-collapse: collapse; min-width: 900px; }
        .comp-table thead { background: #F8FAFC; }
        .comp-table th {
            text-align: left; padding: 10px 14px; font-size: 11px; font-weight: 600;
            color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;
            border-bottom: 1px solid #E2E8F0; white-space: nowrap;
        }
        .comp-table td {
            padding: 12px 14px; font-size: 13px; border-bottom: 1px solid #F1F5F9;
            vertical-align: top;
        }
        .comp-table tr:last-child td { border-bottom: none; }

        /* Column group headers */
        .col-group-po { border-left: 3px solid #4F46E5; }
        .col-group-slip { border-left: 3px solid #0EA5E9; }
        .col-group-inv { border-left: 3px solid #8B5CF6; }

        .th-group {
            text-align: center; font-size: 11px; font-weight: 700;
            padding: 6px 14px; border-bottom: 1px solid #E2E8F0;
        }
        .th-group--po { background: #EEF2FF; color: #4338CA; }
        .th-group--slip { background: #E0F2FE; color: #0369A1; }
        .th-group--inv { background: #EDE9FE; color: #6D28D9; }

        /* Row status highlighting */
        .row-match td { }
        .row-discrepancy td { background: #FFF7ED; }
        .row-info td { background: #F8FAFC; }

        .line-status-dot {
            display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px;
        }
        .dot-match { background: #10B981; }
        .dot-discrepancy { background: #F59E0B; }
        .dot-info { background: #94A3B8; }

        .delta-cell { font-weight: 600; }
        .delta-cell--mismatch { color: #EF4444; background: #FEF2F2; border-radius: 4px; padding: 2px 6px; }
        .delta-cell--match { color: #10B981; }

        .disc-note {
            display: block; font-size: 12px; color: #92400E; margin-top: 4px;
            padding: 4px 8px; background: #FEF3C7; border-radius: 4px;
            border-left: 3px solid #F59E0B;
        }

        .no-data { color: #CBD5E1; font-style: italic; }

        /* Verify button */
        .action-bar {
            display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px;
        }
        .btn {
            padding: 10px 24px; border-radius: 8px; font-size: 14px; font-weight: 600;
            cursor: pointer; border: none; font-family: inherit; transition: all 0.15s;
        }
        .btn-primary { background: #4F46E5; color: white; }
        .btn-primary:hover { background: #4338CA; }
        .btn-outline { background: white; color: #64748B; border: 1px solid #E2E8F0; }
        .btn-outline:hover { border-color: #94A3B8; }
    </style>
</head>
<body>
""" + sidebar_html + """
    <div class="vap-main">
        <div class="page-header">
            <div class="breadcrumb">
                <a href="/">Dashboard</a> &rsaquo;
                <a href="/discrepancy-list">Discrepancies</a> &rsaquo;
                Match Detail
            </div>
            <h1 id="page-title">Match Detail</h1>
            <div class="subtitle" id="page-subtitle">Loading...</div>
        </div>

        <!-- Status Banner -->
        <div class="match-banner match-banner--review" id="match-banner">
            <div class="banner-icon" id="banner-icon">&#8230;</div>
            <div class="banner-text">
                <h3 id="banner-title">Loading...</h3>
                <p id="banner-summary"></p>
            </div>
            <div class="banner-stats">
                <div>
                    <div class="banner-stat-value" id="stat-discrepancies">--</div>
                    <div class="banner-stat-label">Discrepancies</div>
                </div>
                <div>
                    <div class="banner-stat-value" id="stat-delta">--</div>
                    <div class="banner-stat-label">Amount Delta</div>
                </div>
                <div>
                    <div class="banner-stat-value" id="stat-confidence">--</div>
                    <div class="banner-stat-label">Confidence</div>
                </div>
            </div>
        </div>

        <!-- Document Cards -->
        <div class="doc-cards" id="doc-cards"></div>

        <!-- Per-Line Comparison Table -->
        <div class="comp-section-header">Line-by-Line Comparison</div>
        <div class="comp-table-wrap">
            <table class="comp-table">
                <thead>
                    <tr>
                        <th rowspan="2" style="width:30px;">#</th>
                        <th rowspan="2" style="width:40px;">Status</th>
                        <th colspan="3" class="th-group th-group--po">Purchase Order</th>
                        <th colspan="2" class="th-group th-group--slip">Packing Slip</th>
                        <th colspan="3" class="th-group th-group--inv">Invoice</th>
                        <th rowspan="2">Notes</th>
                    </tr>
                    <tr>
                        <th class="col-group-po">Description</th>
                        <th>Qty</th>
                        <th>Unit Price</th>
                        <th class="col-group-slip">Description</th>
                        <th>Shipped</th>
                        <th class="col-group-inv">Description</th>
                        <th>Qty</th>
                        <th>Unit Price</th>
                    </tr>
                </thead>
                <tbody id="comp-tbody">
                    <tr><td colspan="11" style="text-align:center;padding:40px;color:#94A3B8;">Loading...</td></tr>
                </tbody>
            </table>
        </div>

        <!-- Actions -->
        <div class="action-bar" id="action-bar" style="display:none;">
            <button class="btn btn-outline" onclick="window.history.back()">Back</button>
            <button class="btn btn-primary" id="btn-verify" onclick="verifyPO()">Mark as Verified</button>
        </div>
    </div>

    <script>
        var matchId = window.location.pathname.split('/').pop();
        var poId = null;

        async function loadMatchDetail() {
            try {
                var resp = await fetch('/api/v2/match/' + matchId);
                var data = await resp.json();
                var match = data.match;
                var po = data.purchase_order;
                var slip = data.packing_slip;
                var inv = data.invoice;
                poId = match.po_id;

                // Title
                document.getElementById('page-title').textContent = 'Match: PO ' + (po.po_number || '--');
                document.getElementById('page-subtitle').textContent = (po.vendor_name || '') + ' — ' + match.match_type.replace('_', ' ').toUpperCase();

                // Banner
                var banner = document.getElementById('match-banner');
                banner.className = 'match-banner match-banner--' + match.overall_status;
                var icons = {approve: '&#10003;', review: '&#9888;', reject: '&#10007;'};
                document.getElementById('banner-icon').innerHTML = icons[match.overall_status] || '?';
                document.getElementById('banner-title').textContent = match.overall_status.toUpperCase();
                document.getElementById('banner-summary').textContent = match.summary || '';
                document.getElementById('stat-discrepancies').textContent = match.total_discrepancies;
                document.getElementById('stat-delta').textContent = '$' + Math.abs(match.amount_delta || 0).toFixed(2);
                document.getElementById('stat-confidence').textContent = (match.confidence || 0).toFixed(0) + '%';

                // Document cards
                var cardsHtml = '';
                cardsHtml += '<div class="doc-card"><h4>Purchase Order</h4>';
                cardsHtml += '<div class="doc-value">PO ' + (po.po_number || '--') + '</div>';
                cardsHtml += '<div class="doc-meta">' + (po.vendor_name || '') + '</div>';
                cardsHtml += '<div class="doc-meta">Total: $' + Number(po.total_amount || 0).toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>';
                if (po.source_filename) cardsHtml += '<a class="doc-file" href="#">&#128196; ' + po.source_filename + '</a>';
                cardsHtml += '</div>';

                if (slip) {
                    cardsHtml += '<div class="doc-card"><h4>Packing Slip</h4>';
                    cardsHtml += '<div class="doc-value">' + (slip.slip_number || '--') + '</div>';
                    cardsHtml += '<div class="doc-meta">Delivery: ' + (slip.delivery_number || '--') + '</div>';
                    cardsHtml += '<div class="doc-meta">Units: ' + (slip.total_units || '--') + '</div>';
                    if (slip.source_filename) cardsHtml += '<a class="doc-file" href="#">&#128196; ' + slip.source_filename + '</a>';
                    cardsHtml += '</div>';
                } else {
                    cardsHtml += '<div class="doc-card" style="opacity:0.5;"><h4>Packing Slip</h4><div class="doc-meta">Not uploaded</div></div>';
                }

                if (inv) {
                    cardsHtml += '<div class="doc-card"><h4>Invoice</h4>';
                    cardsHtml += '<div class="doc-value">#' + (inv.invoice_number || '--') + '</div>';
                    cardsHtml += '<div class="doc-meta">Total: $' + Number(inv.total_amount || 0).toLocaleString('en-US', {minimumFractionDigits: 2}) + '</div>';
                    cardsHtml += '<div class="doc-meta">' + (inv.payment_terms || '') + '</div>';
                    if (inv.source_filename) cardsHtml += '<a class="doc-file" href="#">&#128196; ' + inv.source_filename + '</a>';
                    cardsHtml += '</div>';
                } else {
                    cardsHtml += '<div class="doc-card" style="opacity:0.5;"><h4>Invoice</h4><div class="doc-meta">Not uploaded</div></div>';
                }
                document.getElementById('doc-cards').innerHTML = cardsHtml;

                // Line comparison table
                var lines = match.line_details || [];
                var tbody = document.getElementById('comp-tbody');
                if (lines.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="11" style="text-align:center;padding:40px;">No line details available.</td></tr>';
                    return;
                }

                var html = '';
                for (var i = 0; i < lines.length; i++) {
                    var l = lines[i];
                    var rowClass = 'row-' + l.line_status;
                    var dotClass = 'dot-' + l.line_status;

                    html += '<tr class="' + rowClass + '">';
                    html += '<td>' + l.line_number + '</td>';
                    html += '<td><span class="line-status-dot ' + dotClass + '"></span>' + l.line_status + '</td>';

                    // PO columns
                    html += '<td class="col-group-po">' + (l.po_description || '<span class="no-data">--</span>') + '</td>';
                    html += '<td>' + formatQty(l.po_quantity) + '</td>';
                    html += '<td>' + formatMoney(l.po_unit_price) + '</td>';

                    // Slip columns
                    html += '<td class="col-group-slip">' + (l.slip_description || '<span class="no-data">--</span>') + '</td>';
                    var slipShipped = l.slip_qty_shipped !== null && l.slip_qty_shipped !== undefined ? l.slip_qty_shipped : null;
                    if (slipShipped !== null && l.po_quantity !== null && slipShipped != l.po_quantity) {
                        html += '<td><span class="delta-cell delta-cell--mismatch">' + slipShipped + '</span></td>';
                    } else {
                        html += '<td>' + (slipShipped !== null ? slipShipped : '<span class="no-data">--</span>') + '</td>';
                    }

                    // Invoice columns
                    html += '<td class="col-group-inv">' + (l.inv_description || '<span class="no-data">--</span>') + '</td>';
                    if (l.inv_quantity !== null && l.inv_quantity !== undefined && l.po_quantity !== null && l.inv_quantity != l.po_quantity) {
                        html += '<td><span class="delta-cell delta-cell--mismatch">' + l.inv_quantity + '</span></td>';
                    } else {
                        html += '<td>' + formatQty(l.inv_quantity) + '</td>';
                    }
                    if (l.inv_unit_price !== null && l.inv_unit_price !== undefined && l.po_unit_price !== null && Math.abs(l.inv_unit_price - l.po_unit_price) > 0.01) {
                        html += '<td><span class="delta-cell delta-cell--mismatch">$' + Number(l.inv_unit_price).toFixed(2) + '</span></td>';
                    } else {
                        html += '<td>' + formatMoney(l.inv_unit_price) + '</td>';
                    }

                    // Notes
                    html += '<td>';
                    if (l.discrepancy_note) {
                        html += '<span class="disc-note">' + l.discrepancy_note + '</span>';
                    }
                    html += '</td>';

                    html += '</tr>';
                }
                tbody.innerHTML = html;

                // Show action bar
                if (match.overall_status === 'approve') {
                    document.getElementById('action-bar').style.display = 'flex';
                }
            } catch (e) {
                console.error('Failed to load match detail:', e);
            }
        }

        function formatQty(val) {
            if (val === null || val === undefined) return '<span class="no-data">--</span>';
            return Number(val).toString();
        }
        function formatMoney(val) {
            if (val === null || val === undefined) return '<span class="no-data">--</span>';
            return '$' + Number(val).toFixed(2);
        }

        async function verifyPO() {
            if (!poId) return;
            try {
                var resp = await fetch('/api/v2/verify/' + poId, {method: 'POST'});
                var data = await resp.json();
                alert('PO verified: ' + data.message);
                window.location.href = '/po-list';
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }

        loadMatchDetail();
    </script>
</body>
</html>"""

    sidebar_html = get_sidebar_html("discrepancies")
    sidebar_styles = get_sidebar_styles()

