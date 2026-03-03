"""
VerifyAP — Document History View

Visual timeline of all document events. When a user selects a PO,
shows the full lifecycle: upload → match → verify → archive.
"""

from .sidebar_component import get_sidebar_html, get_sidebar_styles


def get_document_history_html():
    sidebar_html = get_sidebar_html("document_history")
    sidebar_styles = get_sidebar_styles()

    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VerifyAP — Document History</title>
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

        /* Layout: list + detail panel */
        .history-layout { display: grid; grid-template-columns: 380px 1fr; gap: 24px; }

        /* Left panel: event list */
        .event-list {
            background: white; border: 1px solid #E2E8F0; border-radius: 12px;
            max-height: calc(100vh - 160px); overflow-y: auto;
        }
        .event-list-header {
            padding: 16px 20px; border-bottom: 1px solid #E2E8F0;
            font-size: 14px; font-weight: 600; color: #0F172A;
            position: sticky; top: 0; background: white; z-index: 1;
        }
        .event-item {
            padding: 14px 20px; border-bottom: 1px solid #F1F5F9; cursor: pointer;
            transition: background 0.1s;
        }
        .event-item:hover { background: #F8FAFC; }
        .event-item.active { background: #EEF2FF; border-left: 3px solid #4F46E5; }
        .event-item:last-child { border-bottom: none; }

        .event-icon {
            display: inline-flex; align-items: center; justify-content: center;
            width: 28px; height: 28px; border-radius: 6px; margin-right: 10px;
            font-size: 13px; flex-shrink: 0; vertical-align: middle;
        }
        .event-icon--po { background: #EEF2FF; color: #4F46E5; }
        .event-icon--slip { background: #E0F2FE; color: #0369A1; }
        .event-icon--invoice { background: #EDE9FE; color: #6D28D9; }
        .event-icon--match { background: #D1FAE5; color: #065F46; }
        .event-icon--verify { background: #FEF3C7; color: #92400E; }
        .event-icon--archive { background: #F1F5F9; color: #64748B; }

        .event-title { font-size: 14px; font-weight: 500; color: #0F172A; }
        .event-meta { font-size: 12px; color: #94A3B8; margin-top: 2px; }

        /* Right panel: timeline detail */
        .timeline-panel {
            background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 28px;
        }
        .timeline-panel h2 {
            font-size: 18px; font-weight: 600; color: #0F172A; margin-bottom: 4px;
        }
        .timeline-panel .po-meta {
            font-size: 14px; color: #64748B; margin-bottom: 24px;
        }

        /* Vertical timeline */
        .timeline {
            position: relative; padding-left: 32px;
        }
        .timeline::before {
            content: ''; position: absolute; left: 11px; top: 0; bottom: 0;
            width: 2px; background: #E2E8F0;
        }
        .timeline-event {
            position: relative; margin-bottom: 24px; padding-bottom: 0;
        }
        .timeline-event:last-child { margin-bottom: 0; }
        .timeline-dot {
            position: absolute; left: -32px; top: 2px;
            width: 22px; height: 22px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-size: 10px; border: 2px solid white;
        }
        .tl-dot--po { background: #4F46E5; color: white; }
        .tl-dot--slip { background: #0EA5E9; color: white; }
        .tl-dot--invoice { background: #8B5CF6; color: white; }
        .tl-dot--match { background: #10B981; color: white; }
        .tl-dot--verify { background: #F59E0B; color: white; }
        .tl-dot--archive { background: #94A3B8; color: white; }

        .tl-time { font-size: 12px; color: #94A3B8; margin-bottom: 4px; }
        .tl-title { font-size: 14px; font-weight: 600; color: #0F172A; }
        .tl-desc { font-size: 13px; color: #64748B; margin-top: 2px; }
        .tl-file-link {
            display: inline-flex; align-items: center; gap: 4px;
            font-size: 12px; color: #4F46E5; margin-top: 6px; text-decoration: none;
        }

        .empty-state { text-align: center; padding: 60px 20px; color: #94A3B8; }

        /* Batch archive section */
        .archive-section {
            margin-top: 28px; padding-top: 20px; border-top: 1px solid #E2E8F0;
        }
        .archive-section h3 { font-size: 14px; font-weight: 600; margin-bottom: 12px; }
        .btn {
            padding: 8px 18px; border-radius: 8px; font-size: 13px; font-weight: 600;
            cursor: pointer; border: none; font-family: inherit;
        }
        .btn-danger { background: #FEE2E2; color: #991B1B; }
        .btn-danger:hover { background: #FECACA; }
    </style>
</head>
<body>
""" + sidebar_html + """
    <div class="vap-main">
        <div class="page-header">
            <div class="breadcrumb"><a href="/">Dashboard</a> &rsaquo; Document History</div>
            <h1>Document History</h1>
        </div>

        <div class="history-layout">
            <!-- Left: Event list -->
            <div class="event-list">
                <div class="event-list-header">Recent Events</div>
                <div id="event-list-body">
                    <div class="empty-state">Loading...</div>
                </div>
            </div>

            <!-- Right: Timeline detail -->
            <div class="timeline-panel" id="timeline-panel">
                <div class="empty-state">
                    <p>Select a PO from the list to view its document timeline.</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        var eventIcons = {
            po_uploaded: {cls: 'event-icon--po', label: 'PO'},
            slip_uploaded: {cls: 'event-icon--slip', label: 'PS'},
            invoice_uploaded: {cls: 'event-icon--invoice', label: 'INV'},
            match_2way: {cls: 'event-icon--match', label: '2W'},
            match_3way: {cls: 'event-icon--match', label: '3W'},
            verified: {cls: 'event-icon--verify', label: 'VER'},
            archived: {cls: 'event-icon--archive', label: 'ARC'},
        };

        var tlDotClasses = {
            po_uploaded: 'tl-dot--po',
            slip_uploaded: 'tl-dot--slip',
            invoice_uploaded: 'tl-dot--invoice',
            match_2way: 'tl-dot--match',
            match_3way: 'tl-dot--match',
            verified: 'tl-dot--verify',
            archived: 'tl-dot--archive',
        };

        var eventLabels = {
            po_uploaded: 'Purchase Order Uploaded',
            slip_uploaded: 'Packing Slip Uploaded',
            invoice_uploaded: 'Invoice Uploaded',
            match_2way: '2-Way Match Performed',
            match_3way: '3-Way Match Performed',
            verified: 'PO Verified',
            archived: 'Documents Archived',
        };

        async function loadEvents() {
            try {
                var resp = await fetch('/api/v2/document-history?limit=100');
                var data = await resp.json();
                var container = document.getElementById('event-list-body');

                if (data.events.length === 0) {
                    container.innerHTML = '<div class="empty-state"><p>No document events yet.</p></div>';
                    return;
                }

                // Group by PO
                var poGroups = {};
                for (var i = 0; i < data.events.length; i++) {
                    var ev = data.events[i];
                    var key = ev.po_id || ev.po_number || 'unknown';
                    if (!poGroups[key]) poGroups[key] = [];
                    poGroups[key].push(ev);
                }

                var html = '';
                for (var i = 0; i < data.events.length; i++) {
                    var ev = data.events[i];
                    var iconInfo = eventIcons[ev.event_type] || {cls: 'event-icon--po', label: '?'};
                    var label = eventLabels[ev.event_type] || ev.event_type;
                    var time = ev.created_at ? new Date(ev.created_at).toLocaleString() : '';
                    var poLabel = ev.po_number ? 'PO ' + ev.po_number : '';

                    html += '<div class="event-item" onclick="loadTimeline(\\'' + (ev.po_id || '') + '\\')" data-po="' + (ev.po_id || '') + '">';
                    html += '<span class="event-icon ' + iconInfo.cls + '">' + iconInfo.label + '</span>';
                    html += '<span class="event-title">' + label + '</span>';
                    html += '<div class="event-meta">' + poLabel + ' &middot; ' + time + '</div>';
                    html += '</div>';
                }
                container.innerHTML = html;
            } catch (e) {
                console.error('Failed to load events:', e);
            }
        }

        async function loadTimeline(poId) {
            if (!poId) return;

            // Highlight active item
            var items = document.querySelectorAll('.event-item');
            for (var i = 0; i < items.length; i++) {
                items[i].classList.toggle('active', items[i].dataset.po === poId);
            }

            try {
                var resp = await fetch('/api/v2/document-history/' + poId);
                var data = await resp.json();
                var panel = document.getElementById('timeline-panel');

                var html = '<h2>PO ' + (data.po_number || '--') + '</h2>';
                html += '<div class="po-meta">' + (data.vendor_name || '') + ' &middot; Status: ' + (data.current_status || '--').toUpperCase() + '</div>';

                if (data.timeline.length === 0) {
                    html += '<div class="empty-state"><p>No events recorded for this PO.</p></div>';
                    panel.innerHTML = html;
                    return;
                }

                html += '<div class="timeline">';
                for (var i = 0; i < data.timeline.length; i++) {
                    var ev = data.timeline[i];
                    var dotClass = tlDotClasses[ev.event_type] || 'tl-dot--po';
                    var label = eventLabels[ev.event_type] || ev.event_type;
                    var time = ev.created_at ? new Date(ev.created_at).toLocaleString() : '';
                    var dotLabel = (eventIcons[ev.event_type] || {label:'?'}).label;

                    html += '<div class="timeline-event">';
                    html += '<div class="timeline-dot ' + dotClass + '">' + dotLabel + '</div>';
                    html += '<div class="tl-time">' + time + '</div>';
                    html += '<div class="tl-title">' + label + '</div>';
                    if (ev.entity_type) {
                        html += '<div class="tl-desc">' + ev.entity_type + ' &middot; ' + (ev.event_source || 'user') + '</div>';
                    }
                    html += '</div>';
                }
                html += '</div>';

                // Archive section
                html += '<div class="archive-section">';
                html += '<h3>Lifecycle Actions</h3>';
                if (data.current_status === 'verified') {
                    html += '<button class="btn btn-danger" onclick="archivePO(\\'' + poId + '\\')">Archive This PO</button>';
                } else if (data.current_status === 'active' || data.current_status === 'fully_matched') {
                    html += '<button class="btn" style="background:#D1FAE5;color:#065F46;" onclick="verifyPO(\\'' + poId + '\\')">Mark as Verified</button>';
                } else {
                    html += '<span style="color:#94A3B8;font-size:13px;">Status: ' + data.current_status + '</span>';
                }
                html += '</div>';

                panel.innerHTML = html;
            } catch (e) {
                console.error('Failed to load timeline:', e);
            }
        }

        async function verifyPO(poId) {
            var resp = await fetch('/api/v2/verify/' + poId, {method:'POST'});
            var data = await resp.json();
            alert(data.message);
            loadTimeline(poId);
            loadEvents();
        }

        async function archivePO(poId) {
            if (!confirm('Archive this PO and all linked documents?')) return;
            var resp = await fetch('/api/v2/archive/batch', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify([poId])
            });
            var data = await resp.json();
            alert(data.message);
            loadTimeline(poId);
            loadEvents();
        }

        loadEvents();
    </script>
</body>
</html>"""

    sidebar_html = get_sidebar_html("document_history")
    sidebar_styles = get_sidebar_styles()

