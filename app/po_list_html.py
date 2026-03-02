"""
VerifyAP — Purchase Order List View

Filterable list of all POs with match status, vendor, amounts.
Rows click through to PO detail (which shows the full 3-way comparison).

Uses string concatenation (not f-strings) per project convention.
"""


def get_po_list_html():
    """Return full HTML for the PO list page."""

    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VerifyAP — Purchase Orders</title>
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'DM Sans', sans-serif; background: #F1F5F9; color: #1E293B; }

        .vap-main { margin-left: 260px; padding: 32px 40px; min-height: 100vh; }

        .page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
        .page-header h1 { font-size: 24px; font-weight: 700; }
        .page-header .breadcrumb { font-size: 13px; color: #64748B; margin-top: 4px; }
        .page-header .breadcrumb a { color: #4F46E5; text-decoration: none; }

        /* Filters */
        .filters-bar {
            display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; align-items: center;
        }
        .filter-chip {
            padding: 7px 16px; border-radius: 20px; border: 1px solid #E2E8F0;
            background: white; font-size: 13px; font-weight: 500; cursor: pointer;
            color: #64748B; transition: all 0.15s;
        }
        .filter-chip:hover { border-color: #4F46E5; color: #4F46E5; }
        .filter-chip.active { background: #4F46E5; color: white; border-color: #4F46E5; }

        .search-input {
            padding: 7px 14px; border-radius: 8px; border: 1px solid #E2E8F0;
            font-size: 13px; width: 240px; outline: none; font-family: inherit;
        }
        .search-input:focus { border-color: #4F46E5; box-shadow: 0 0 0 2px rgba(79,70,229,0.1); }

        /* Table */
        .data-table-wrap {
            background: white; border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden;
        }
        table { width: 100%; border-collapse: collapse; }
        thead { background: #F8FAFC; }
        th {
            text-align: left; padding: 12px 20px; font-size: 12px; font-weight: 600;
            color: #64748B; text-transform: uppercase; letter-spacing: 0.5px;
            border-bottom: 1px solid #E2E8F0;
        }
        td { padding: 14px 20px; font-size: 14px; border-bottom: 1px solid #F1F5F9; }
        tr:last-child td { border-bottom: none; }
        tr:hover { background: #FAFBFD; }
        tr.clickable-row { cursor: pointer; }

        .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; }
        .badge--approve { background: #D1FAE5; color: #065F46; }
        .badge--review { background: #FEF3C7; color: #92400E; }
        .badge--reject { background: #FEE2E2; color: #991B1B; }
        .badge--unmatched { background: #F1F5F9; color: #64748B; }

        .doc-indicators { display: flex; gap: 6px; }
        .doc-dot {
            width: 8px; height: 8px; border-radius: 50%; background: #E2E8F0;
            position: relative;
        }
        .doc-dot.filled { background: #10B981; }
        .doc-dot::after {
            content: attr(data-label); position: absolute; bottom: 14px; left: 50%;
            transform: translateX(-50%); font-size: 10px; color: #94A3B8;
            white-space: nowrap; display: none;
        }
        .doc-dot:hover::after { display: block; }

        .money { font-variant-numeric: tabular-nums; }
        .count-badge {
            display: inline-flex; align-items: center; justify-content: center;
            min-width: 24px; height: 20px; border-radius: 10px; font-size: 11px;
            font-weight: 600; padding: 0 6px;
        }
        .count-badge--warn { background: #FEF3C7; color: #92400E; }
        .count-badge--danger { background: #FEE2E2; color: #991B1B; }
        .count-badge--ok { background: #F1F5F9; color: #94A3B8; }

        .result-count { font-size: 13px; color: #94A3B8; margin-bottom: 12px; }

        .empty-state { text-align: center; padding: 60px 20px; color: #94A3B8; }
    </style>
</head>
<body>
    <!-- Sidebar injected by sidebar_component.py -->

    <div class="vap-main">
        <div class="page-header">
            <div>
                <div class="breadcrumb"><a href="/">Dashboard</a> &rsaquo; Purchase Orders</div>
                <h1>Purchase Orders</h1>
            </div>
        </div>

        <!-- Filters -->
        <div class="filters-bar">
            <button class="filter-chip active" data-filter="all" onclick="filterByStatus(this, '')">All</button>
            <button class="filter-chip" data-filter="unmatched" onclick="filterByStatus(this, 'unmatched')">Unmatched</button>
            <button class="filter-chip" data-filter="approve" onclick="filterByStatus(this, 'approve')">Approved</button>
            <button class="filter-chip" data-filter="review" onclick="filterByStatus(this, 'review')">Review</button>
            <button class="filter-chip" data-filter="reject" onclick="filterByStatus(this, 'reject')">Rejected</button>
            <div style="flex:1;"></div>
            <input type="text" class="search-input" placeholder="Search vendor..." id="vendor-search" oninput="filterByVendor(this.value)">
        </div>

        <div class="result-count" id="result-count"></div>

        <div class="data-table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>PO #</th>
                        <th>Vendor</th>
                        <th>Date</th>
                        <th>Amount</th>
                        <th>Documents</th>
                        <th>Match Status</th>
                        <th>Discrepancies</th>
                    </tr>
                </thead>
                <tbody id="po-tbody">
                    <tr><td colspan="7" class="empty-state">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        var allPOs = [];
        var currentFilter = '';
        var currentVendor = '';

        async function loadPOs() {
            try {
                var url = '/api/v2/purchase-orders';
                var params = [];
                if (currentFilter) params.push('match_status=' + currentFilter);
                if (currentVendor) params.push('vendor=' + encodeURIComponent(currentVendor));
                if (params.length > 0) url += '?' + params.join('&');

                var resp = await fetch(url);
                var data = await resp.json();
                allPOs = data.purchase_orders;
                document.getElementById('result-count').textContent = data.count + ' purchase order' + (data.count !== 1 ? 's' : '');
                renderTable(allPOs);
            } catch (e) {
                console.error('Failed to load POs:', e);
            }
        }

        function renderTable(pos) {
            var tbody = document.getElementById('po-tbody');
            if (pos.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><p>No purchase orders match your filters.</p></td></tr>';
                return;
            }
            var html = '';
            for (var i = 0; i < pos.length; i++) {
                var po = pos[i];
                var amt = po.total_amount ? '$' + Number(po.total_amount).toLocaleString('en-US', {minimumFractionDigits: 2}) : '--';
                var badgeClass = 'badge--' + (po.match_status || 'unmatched');
                var discCount = po.total_discrepancies || 0;
                var countClass = discCount > 2 ? 'count-badge--danger' : discCount > 0 ? 'count-badge--warn' : 'count-badge--ok';

                html += '<tr class="clickable-row" onclick="window.location.href=\\'/po-detail/' + po.id + '\\'">';
                html += '<td><strong>' + (po.po_number || '--') + '</strong></td>';
                html += '<td>' + (po.vendor_name || '--') + '</td>';
                html += '<td>' + (po.order_date || '--') + '</td>';
                html += '<td class="money">' + amt + '</td>';
                html += '<td><div class="doc-indicators">';
                html += '<div class="doc-dot filled" data-label="PO"></div>';
                html += '<div class="doc-dot' + (po.slip_count > 0 ? ' filled' : '') + '" data-label="Slip"></div>';
                html += '<div class="doc-dot' + (po.invoice_count > 0 ? ' filled' : '') + '" data-label="Invoice"></div>';
                html += '</div></td>';
                html += '<td><span class="badge ' + badgeClass + '">' + (po.match_status || 'unmatched').toUpperCase() + '</span></td>';
                html += '<td><span class="count-badge ' + countClass + '">' + discCount + '</span></td>';
                html += '</tr>';
            }
            tbody.innerHTML = html;
        }

        function filterByStatus(el, status) {
            var chips = document.querySelectorAll('.filter-chip');
            for (var c = 0; c < chips.length; c++) chips[c].classList.remove('active');
            el.classList.add('active');
            currentFilter = status;
            loadPOs();
        }

        function filterByVendor(val) {
            currentVendor = val;
            loadPOs();
        }

        // Check URL params for pre-filtering
        var urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('match_status')) {
            currentFilter = urlParams.get('match_status');
            var chips = document.querySelectorAll('.filter-chip');
            for (var c = 0; c < chips.length; c++) {
                chips[c].classList.remove('active');
                if (chips[c].dataset.filter === currentFilter) chips[c].classList.add('active');
            }
        }

        loadPOs();
    </script>
</body>
</html>"""
