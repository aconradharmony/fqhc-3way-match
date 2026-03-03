"""
VerifyAP - Reusable Sidebar Navigation Component
Updated: Mar 2, 2026 — Added v2 drill-down pages, section divider
"""


def get_sidebar_styles():
    """Return CSS styles for the sidebar navigation."""
    return """
    <link rel="icon" type="image/svg+xml" href="/static/favicon.svg">
    <style>
        .verifyap-sidebar {
            position: fixed;
            left: 0;
            top: 0;
            bottom: 0;
            width: 260px;
            background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
            color: white;
            padding: 0;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.15);
        }

        .verifyap-sidebar-brand {
            padding: 28px 24px 24px 24px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }

        .verifyap-sidebar-brand-row {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .verifyap-sidebar-logo {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: 700;
            color: white;
            flex-shrink: 0;
        }

        .verifyap-sidebar-brand-text h2 {
            margin: 0;
            font-size: 18px;
            font-weight: 700;
            color: white;
            letter-spacing: -0.3px;
        }

        .verifyap-sidebar-brand-text p {
            margin: 2px 0 0 0;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.5);
            font-weight: 400;
        }

        .verifyap-sidebar-nav {
            padding: 16px 12px;
            flex: 1;
            overflow-y: auto;
        }

        .verifyap-sidebar-nav-label {
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            color: rgba(255, 255, 255, 0.35);
            padding: 0 12px;
            margin-bottom: 8px;
        }

        .verifyap-sidebar-nav-divider {
            height: 1px;
            background: rgba(255, 255, 255, 0.08);
            margin: 12px 12px;
        }

        .verifyap-sidebar-link {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 11px 16px;
            margin-bottom: 2px;
            border-radius: 10px;
            color: rgba(255, 255, 255, 0.65);
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .verifyap-sidebar-link:hover {
            background: rgba(255, 255, 255, 0.08);
            color: white;
        }

        .verifyap-sidebar-link.active {
            background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
            color: white;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(79, 70, 229, 0.4);
        }

        .verifyap-sidebar-link-icon {
            font-size: 18px;
            width: 24px;
            text-align: center;
            flex-shrink: 0;
        }

        .verifyap-sidebar-footer {
            padding: 16px 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            font-size: 11px;
            color: rgba(255, 255, 255, 0.3);
        }

        .verifyap-main-content {
            margin-left: 260px;
            min-height: 100vh;
            background: #F8FAFC;
        }
    </style>
    """


def get_sidebar_html(active_page="dashboard"):
    """
    Return HTML for the sidebar navigation.

    Args:
        active_page: One of 'dashboard', 'purchase_orders', 'deliveries',
                     'invoices', 'po_list', 'discrepancies',
                     'document_history'
    """

    # Upload / workflow section
    upload_items = [
        {"id": "purchase_orders", "label": "Upload POs", "icon": "\U0001F4CB", "href": "/admin"},
        {"id": "deliveries", "label": "Deliveries", "icon": "\U0001F4E6", "href": "/deliveries"},
        {"id": "invoices", "label": "Invoices", "icon": "\U0001F4B0", "href": "/invoices"},
    ]

    # Analysis / drill-down section
    analysis_items = [
        {"id": "dashboard", "label": "Dashboard", "icon": "\U0001F4CA", "href": "/dashboard-v2"},
        {"id": "po_list", "label": "Purchase Orders", "icon": "\U0001F4C4", "href": "/po-list"},
        {"id": "discrepancies", "label": "Discrepancies", "icon": "\u26A0\uFE0F", "href": "/discrepancy-list"},
        {"id": "document_history", "label": "Document History", "icon": "\U0001F552", "href": "/document-history"},
    ]

    def build_links(items):
        links = ""
        for item in items:
            active_class = " active" if item["id"] == active_page else ""
            links += (
                '<a class="verifyap-sidebar-link'
                + active_class
                + '" href="'
                + item["href"]
                + '">'
                + '<span class="verifyap-sidebar-link-icon">'
                + item["icon"]
                + "</span>"
                + "<span>"
                + item["label"]
                + "</span>"
                + "</a>\n"
            )
        return links

    html = (
        '<div class="verifyap-sidebar">'
        + '<div class="verifyap-sidebar-brand">'
        + '<div class="verifyap-sidebar-brand-row">'
        + '<div class="verifyap-sidebar-logo">'
        + "\u2713"
        + "</div>"
        + '<div class="verifyap-sidebar-brand-text">'
        + "<h2>VerifyAP</h2>"
        + "<p>3-Way Match Automation</p>"
        + "</div>"
        + "</div>"
        + "</div>"
        + '<nav class="verifyap-sidebar-nav">'
        + '<div class="verifyap-sidebar-nav-label">Analysis</div>'
        + build_links(analysis_items)
        + '<div class="verifyap-sidebar-nav-divider"></div>'
        + '<div class="verifyap-sidebar-nav-label">Upload</div>'
        + build_links(upload_items)
        + "</nav>"
        + '<div class="verifyap-sidebar-footer">'
        + "VerifyAP v2.0 &middot; Harmony Hello"
        + "</div>"
        + "</div>"
    )

    return html
