"""
VerifyAP — Dashboard v2 (Drill-Down Edition)

Replaces the static dashboard. Cards are now clickable links that route to
filtered list views. Stats load from /api/v2/dashboard-stats.

Uses string concatenation (not f-strings) per project convention.
"""

from .sidebar_component import get_sidebar_html, get_sidebar_styles


def get_dashboard_v2_html():
    """Return the full HTML for the drill-down dashboard."""

    sidebar_html = get_sidebar_html("dashboard")
    sidebar_styles = get_sidebar_styles()


    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VerifyAP — Dashboard</title>
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    """ + sidebar_styles + """
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'DM Sans', -apple-system, sans-serif;
            background: #F1F5F9;
            color: #1E293B;
            min-height: 100vh;
        }

        /* --- Layout (sidebar assumed at 260px) --- */
        .vap-main {
            margin-left: 260px;
            padding: 32px 40px;
            min-height: 100vh;
        }

        .vap-header {
            margin-bottom: 32px;
        }
        .vap-header h1 {
            font-size: 28px;
            font-weight: 700;
            color: #0F172A;
        }
        .vap-header p {
            color: #64748B;
            margin-top: 4px;
            font-size: 14px;
        }

        /* --- Stat Cards Grid --- */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 36px;
        }

        .stat-card {
            background: white;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 24px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-decoration: none;
            color: inherit;
            display: block;
            position: relative;
            overflow: hidden;
        }
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
        }
        .stat-card:hover {
            border-color: #CBD5E1;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        }
        .stat-card .card-label {
            font-size: 13px;
            font-weight: 500;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .stat-card .card-value {
            font-size: 36px;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 8px;
        }
        .stat-card .card-detail {
            font-size: 13px;
            color: #94A3B8;
        }
        .stat-card .card-arrow {
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 20px;
            color: #CBD5E1;
            transition: all 0.2s;
        }
        .stat-card:hover .card-arrow {
            color: #4F46E5;
            transform: translateY(-50%) translateX(3px);
        }

        /* Card accent colors */
        .stat-card--po::before { background: #4F46E5; }
        .stat-card--po .card-value { color: #4F46E5; }

        .stat-card--disc::before { background: #F59E0B; }
        .stat-card--disc .card-value { color: #F59E0B; }

        .stat-card--approved::before { background: #10B981; }
        .stat-card--approved .card-value { color: #10B981; }

        .stat-card--lifecycle::before { background: #6366F1; }
        .stat-card--lifecycle .card-value { color: #6366F1; }

        /* --- Recent Activity Table --- */
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .section-header h2 {
            font-size: 18px;
            font-weight: 600;
            color: #0F172A;
        }
        .section-header a {
            font-size: 13px;
            color: #4F46E5;
            text-decoration: none;
            font-weight: 500;
        }
        .section-header a:hover {
            text-decoration: underline;
        }

        .data-table-wrap {
            background: white;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 32px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }
        thead {
            background: #F8FAFC;
        }
        th {
            text-align: left;
            padding: 12px 20px;
            font-size: 12px;
            font-weight: 600;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #E2E8F0;
        }
        td {
            padding: 14px 20px;
            font-size: 14px;
            border-bottom: 1px solid #F1F5F9;
        }
        tr:last-child td {
            border-bottom: none;
        }
        tr:hover {
            background: #FAFBFD;
        }
        tr.clickable-row {
            cursor: pointer;
        }

        /* Badges */
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .badge--approve { background: #D1FAE5; color: #065F46; }
        .badge--review  { background: #FEF3C7; color: #92400E; }
        .badge--reject  { background: #FEE2E2; color: #991B1B; }
        .badge--unmatched { background: #F1F5F9; color: #64748B; }

        .money { font-variant-numeric: tabular-nums; }
        .money--negative { color: #EF4444; }

        /* Empty state */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #94A3B8;
        }
        .empty-state svg {
            width: 48px;
            height: 48px;
            margin-bottom: 16px;
            opacity: 0.4;
        }
        .empty-state p {
            font-size: 15px;
        }

        /* Loading skeleton */
        .skeleton {
            background: linear-gradient(90deg, #F1F5F9 25%, #E2E8F0 50%, #F1F5F9 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 6px;
            height: 20px;
        }
        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        /* Process Flow */
        .process-flow {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0;
            margin-bottom: 36px;
            background: white;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            overflow: hidden;
        }
        .flow-step {
            padding: 20px 24px;
            text-align: center;
            position: relative;
            border-right: 1px solid #E2E8F0;
        }
        .flow-step:last-child { border-right: none; }
        .flow-step .step-num {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #EEF2FF;
            color: #4F46E5;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .flow-step h4 {
            font-size: 13px;
            font-weight: 600;
            color: #0F172A;
            margin-bottom: 4px;
        }
        .flow-step p {
            font-size: 12px;
            color: #94A3B8;
        }

        @media (max-width: 1200px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    """ + sidebar_html + """

    <div class="vap-main">
        <div class="vap-header">
            <h1>AP Dashboard</h1>
            <p>3-way match overview &mdash; click any card to drill in</p>
        </div>

        <!-- Process Flow -->
        <div class="process-flow">
            <div class="flow-step">
                <div class="step-num">1</div>
                <h4>Upload PO</h4>
                <p>CSV, PDF, or image</p>
            </div>
            <div class="flow-step">
                <div class="step-num">2</div>
                <h4>Scan Packing Slip</h4>
                <p>Photo of delivery receipt</p>
            </div>
            <div class="flow-step">
                <div class="step-num">3</div>
                <h4>Upload Invoice</h4>
                <p>PDF or scanned invoice</p>
            </div>
            <div class="flow-step">
                <div class="step-num">4</div>
                <h4>3-Way Match</h4>
                <p>Auto-compare all three</p>
            </div>
        </div>

        <!-- Stat Cards -->
        <div class="stats-grid">
            <a href="/po-list" class="stat-card stat-card--po" id="card-po">
                <div class="card-label">Purchase Orders</div>
                <div class="card-value" id="stat-po-total">--</div>
                <div class="card-detail" id="stat-po-detail">Loading...</div>
                <div class="card-arrow">&rarr;</div>
            </a>
            <a href="/discrepancy-list" class="stat-card stat-card--disc" id="card-disc">
                <div class="card-label">Discrepancies</div>
                <div class="card-value" id="stat-disc-total">--</div>
                <div class="card-detail" id="stat-disc-detail">Loading...</div>
                <div class="card-arrow">&rarr;</div>
            </a>
            <a href="/po-list?match_status=approve" class="stat-card stat-card--approved" id="card-approved">
                <div class="card-label">Approved Value</div>
                <div class="card-value" id="stat-approved-total">--</div>
                <div class="card-detail" id="stat-approved-detail">Loading...</div>
                <div class="card-arrow">&rarr;</div>
            </a>
            <a href="/document-history" class="stat-card stat-card--lifecycle" id="card-lifecycle">
                <div class="card-label">Document History</div>
                <div class="card-value" id="stat-lifecycle-total">--</div>
                <div class="card-detail" id="stat-lifecycle-detail">Loading...</div>
                <div class="card-arrow">&rarr;</div>
            </a>
        </div>

        <!-- Recent POs Table -->
        <div class="section-header">
            <h2>Recent Purchase Orders</h2>
            <a href="/po-list">View all &rarr;</a>
        </div>
        <div class="data-table-wrap">
            <table id="recent-po-table">
                <thead>
                    <tr>
                        <th>PO #</th>
                        <th>Vendor</th>
                        <th>Date</th>
                        <th>Amount</th>
                        <th>Match Status</th>
                        <th>Discrepancies</th>
                    </tr>
                </thead>
                <tbody id="recent-po-body">
                    <tr><td colspan="6"><div class="skeleton" style="width:100%;height:18px;margin:4px 0;"></div></td></tr>
                    <tr><td colspan="6"><div class="skeleton" style="width:80%;height:18px;margin:4px 0;"></div></td></tr>
                    <tr><td colspan="6"><div class="skeleton" style="width:90%;height:18px;margin:4px 0;"></div></td></tr>
                </tbody>
            </table>
        </div>

        <!-- Recent Discrepancies -->
        <div class="section-header">
            <h2>Recent Discrepancies</h2>
            <a href="/discrepancy-list">View all &rarr;</a>
        </div>
        <div class="data-table-wrap">
            <table id="recent-disc-table">
                <thead>
                    <tr>
                        <th>PO #</th>
                        <th>Vendor</th>
                        <th>Status</th>
                        <th>Issues</th>
                        <th>Amount Delta</th>
                        <th>Summary</th>
                    </tr>
                </thead>
                <tbody id="recent-disc-body">
                    <tr><td colspan="6"><div class="skeleton" style="width:100%;height:18px;margin:4px 0;"></div></td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // --- Load Dashboard Stats ---
        async function loadStats() {
            try {
                const resp = await fetch('/api/v2/dashboard-stats');
                const data = await resp.json();

                // PO card
                document.getElementById('stat-po-total').textContent = data.purchase_orders.total;
                document.getElementById('stat-po-detail').textContent =
                    data.purchase_orders.active + ' active, ' +
                    data.purchase_orders.unmatched + ' unmatched';

                // Discrepancy card
                document.getElementById('stat-disc-total').textContent = data.discrepancies.total;
                document.getElementById('stat-disc-detail').textContent =
                    data.discrepancies.review + ' review, ' +
                    data.discrepancies.reject + ' reject';

                // Approved value
                var amt = data.financials.approved_total;
                document.getElementById('stat-approved-total').textContent = '$' + amt.toLocaleString('en-US', {minimumFractionDigits: 2});
                document.getElementById('stat-approved-detail').textContent = 'Ready for payment';

                // Lifecycle
                document.getElementById('stat-lifecycle-total').textContent =
                    data.lifecycle.verified + data.lifecycle.archived;
                document.getElementById('stat-lifecycle-detail').textContent =
                    data.lifecycle.verified + ' verified, ' +
                    data.lifecycle.archived + ' archived';
            } catch (e) {
                console.error('Failed to load stats:', e);
            }
        }

        // --- Load Recent POs ---
        async function loadRecentPOs() {
            try {
                const resp = await fetch('/api/v2/purchase-orders');
                const data = await resp.json();
                var tbody = document.getElementById('recent-po-body');
                var pos = data.purchase_orders.slice(0, 5);

                if (pos.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="empty-state"><p>No purchase orders yet. Upload one on the Admin page.</p></td></tr>';
                    return;
                }

                var html = '';
                for (var i = 0; i < pos.length; i++) {
                    var po = pos[i];
                    var badgeClass = 'badge--' + (po.match_status || 'unmatched');
                    var amt = po.total_amount ? '$' + Number(po.total_amount).toLocaleString('en-US', {minimumFractionDigits: 2}) : '--';
                    html += '<tr class="clickable-row" onclick="window.location.href=\\'/po-detail/' + po.id + '\\'">';
                    html += '<td><strong>' + (po.po_number || '--') + '</strong></td>';
                    html += '<td>' + (po.vendor_name || '--') + '</td>';
                    html += '<td>' + (po.order_date || '--') + '</td>';
                    html += '<td class="money">' + amt + '</td>';
                    html += '<td><span class="badge ' + badgeClass + '">' + (po.match_status || 'unmatched').toUpperCase() + '</span></td>';
                    html += '<td>' + (po.total_discrepancies || 0) + '</td>';
                    html += '</tr>';
                }
                tbody.innerHTML = html;
            } catch (e) {
                console.error('Failed to load POs:', e);
            }
        }

        // --- Load Recent Discrepancies ---
        async function loadRecentDiscrepancies() {
            try {
                const resp = await fetch('/api/v2/discrepancies');
                const data = await resp.json();
                var tbody = document.getElementById('recent-disc-body');
                var discs = data.discrepancies.slice(0, 5);

                if (discs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="empty-state"><p>No discrepancies found. All clear!</p></td></tr>';
                    return;
                }

                var html = '';
                for (var i = 0; i < discs.length; i++) {
                    var d = discs[i];
                    var badgeClass = 'badge--' + d.overall_status;
                    var delta = d.amount_delta ? '$' + Math.abs(d.amount_delta).toFixed(2) : '$0.00';
                    var deltaClass = d.amount_delta !== 0 ? 'money money--negative' : 'money';
                    html += '<tr class="clickable-row" onclick="window.location.href=\\'/match-detail/' + d.match_id + '\\'">';
                    html += '<td><strong>' + (d.po_number || '--') + '</strong></td>';
                    html += '<td>' + (d.vendor_name || '--') + '</td>';
                    html += '<td><span class="badge ' + badgeClass + '">' + d.overall_status.toUpperCase() + '</span></td>';
                    html += '<td>' + d.total_discrepancies + '</td>';
                    html += '<td class="' + deltaClass + '">' + delta + '</td>';
                    html += '<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + (d.summary || '') + '</td>';
                    html += '</tr>';
                }
                tbody.innerHTML = html;
            } catch (e) {
                console.error('Failed to load discrepancies:', e);
            }
        }

        // --- Init ---
        loadStats();
        loadRecentPOs();
        loadRecentDiscrepancies();
    </script>
</body>
</html>"""
