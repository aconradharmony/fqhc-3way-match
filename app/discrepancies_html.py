"""
VerifyAP — Discrepancy List View

Shows all matches that flagged discrepancies. Filterable by severity.
Rows click through to the full match detail / line comparison view.
"""


def get_discrepancy_list_html():

    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VerifyAP — Discrepancies</title>
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'DM Sans', sans-serif; background: #F1F5F9; color: #1E293B; }
        .vap-main { margin-left: 260px; padding: 32px 40px; min-height: 100vh; }

        .page-header { margin-bottom: 24px; }
        .page-header h1 { font-size: 24px; font-weight: 700; }
        .breadcrumb { font-size: 13px; color: #64748B; margin-bottom: 4px; }
        .breadcrumb a { color: #4F46E5; text-decoration: none; }

        .filters-bar { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
        .filter-chip {
            padding: 7px 16px; border-radius: 20px; border: 1px solid #E2E8F0;
            background: white; font-size: 13px; font-weight: 500; cursor: pointer; color: #64748B;
        }
        .filter-chip:hover { border-color: #F59E0B; color: #92400E; }
        .filter-chip.active { background: #F59E0B; color: white; border-color: #F59E0B; }

        .data-table-wrap { background: white; border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden; }
        table { width: 100%; border-collapse: collapse; }
        thead { background: #F8FAFC; }
        th { text-align: left; padding: 12px 20px; font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #E2E8F0; }
        td { padding: 14px 20px; font-size: 14px; border-bottom: 1px solid #F1F5F9; }
        tr:last-child td { border-bottom: none; }
        tr:hover { background: #FAFBFD; }
        tr.clickable-row { cursor: pointer; }

        .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
        .badge--review { background: #FEF3C7; color: #92400E; }
        .badge--reject { background: #FEE2E2; color: #991B1B; }
        .badge--approve { background: #D1FAE5; color: #065F46; }

        .disc-type-tag {
            display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px;
            font-weight: 500; background: #FEF3C7; color: #92400E; margin: 2px;
        }
        .disc-type-tag--price { background: #FEE2E2; color: #991B1B; }
        .disc-type-tag--qty { background: #DBEAFE; color: #1E40AF; }
        .disc-type-tag--missing { background: #F3E8FF; color: #6B21A8; }

        .money { font-variant-numeric: tabular-nums; }
        .delta-negative { color: #EF4444; font-weight: 600; }
        .delta-zero { color: #10B981; }
        .result-count { font-size: 13px; color: #94A3B8; margin-bottom: 12px; }
        .empty-state { text-align: center; padding: 60px 20px; color: #94A3B8; }
    </style>
</head>
<body>
    <div class="vap-main">
        <div class="page-header">
            <div class="breadcrumb"><a href="/">Dashboard</a> &rsaquo; Discrepancies</div>
            <h1>Discrepancies</h1>
        </div>

        <div class="filters-bar">
            <button class="filter-chip active" onclick="filterSeverity(this, '')">All</button>
            <button class="filter-chip" onclick="filterSeverity(this, 'review')">Review</button>
            <button class="filter-chip" onclick="filterSeverity(this, 'reject')">Rejected</button>
        </div>

        <div class="result-count" id="result-count"></div>

        <div class="data-table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>PO #</th>
                        <th>Vendor</th>
                        <th>Invoice #</th>
                        <th>Status</th>
                        <th>Issues</th>
                        <th>Amount Delta</th>
                        <th>Discrepancy Types</th>
                    </tr>
                </thead>
                <tbody id="disc-tbody">
                    <tr><td colspan="7" class="empty-state">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        var currentSeverity = '';

        async function loadDiscrepancies() {
            try {
                var url = '/api/v2/discrepancies';
                if (currentSeverity) url += '?severity=' + currentSeverity;
                var resp = await fetch(url);
                var data = await resp.json();
                document.getElementById('result-count').textContent = data.count + ' discrepanc' + (data.count !== 1 ? 'ies' : 'y');
                renderTable(data.discrepancies);
            } catch (e) {
                console.error('Failed to load:', e);
            }
        }

        function renderTable(discs) {
            var tbody = document.getElementById('disc-tbody');
            if (discs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><p>No discrepancies found. All clear!</p></td></tr>';
                return;
            }
            var html = '';
            for (var i = 0; i < discs.length; i++) {
                var d = discs[i];
                var badgeClass = 'badge--' + d.overall_status;
                var delta = Math.abs(d.amount_delta || 0).toFixed(2);
                var deltaClass = d.amount_delta !== 0 ? 'delta-negative' : 'delta-zero';

                // Collect unique discrepancy types
                var types = {};
                var lines = d.discrepancy_lines || [];
                for (var j = 0; j < lines.length; j++) {
                    var t = lines[j].discrepancy_type || 'unknown';
                    types[t] = (types[t] || 0) + 1;
                }
                var typeTags = '';
                for (var key in types) {
                    var tagClass = 'disc-type-tag';
                    if (key.indexOf('price') >= 0) tagClass += ' disc-type-tag--price';
                    else if (key.indexOf('qty') >= 0) tagClass += ' disc-type-tag--qty';
                    else if (key.indexOf('missing') >= 0) tagClass += ' disc-type-tag--missing';
                    typeTags += '<span class="' + tagClass + '">' + key.replace(/_/g, ' ') + ' (' + types[key] + ')</span>';
                }

                html += '<tr class="clickable-row" onclick="window.location.href=\\'/match-detail/' + d.match_id + '\\'">';
                html += '<td><strong>' + (d.po_number || '--') + '</strong></td>';
                html += '<td>' + (d.vendor_name || '--') + '</td>';
                html += '<td>' + (d.invoice_number || '--') + '</td>';
                html += '<td><span class="badge ' + badgeClass + '">' + d.overall_status.toUpperCase() + '</span></td>';
                html += '<td>' + d.total_discrepancies + '</td>';
                html += '<td class="money ' + deltaClass + '">$' + delta + '</td>';
                html += '<td>' + typeTags + '</td>';
                html += '</tr>';
            }
            tbody.innerHTML = html;
        }

        function filterSeverity(el, val) {
            var chips = document.querySelectorAll('.filter-chip');
            for (var c = 0; c < chips.length; c++) chips[c].classList.remove('active');
            el.classList.add('active');
            currentSeverity = val;
            loadDiscrepancies();
        }

        loadDiscrepancies();
    </script>
</body>
</html>"""
