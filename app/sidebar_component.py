"""
Modern sidebar component for VerifyAP
Can be imported into any page
"""

def get_sidebar_styles():
    """CSS styles for the sidebar"""
    return """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        /* SIDEBAR */
        .verifyap-sidebar {
            position: fixed;
            left: 0;
            top: 0;
            bottom: 0;
            width: 260px;
            background: #0F172A;
            display: flex;
            flex-direction: column;
            z-index: 1000;
        }
        
        .verifyap-sidebar-header {
            padding: 24px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .verifyap-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }
        
        .verifyap-logo-icon {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            font-weight: 700;
            color: white;
        }
        
        .verifyap-logo-text {
            font-size: 20px;
            font-weight: 700;
            color: white;
        }
        
        .verifyap-tagline {
            font-size: 12px;
            color: #94A3B8;
            padding-left: 48px;
        }
        
        .verifyap-nav {
            flex: 1;
            padding: 24px 12px;
            overflow-y: auto;
        }
        
        .verifyap-nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px 16px;
            border-radius: 8px;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 4px;
            transition: all 0.2s;
            cursor: pointer;
        }
        
        .verifyap-nav-item.active {
            background: #4F46E5;
            color: white;
        }
        
        .verifyap-nav-item:not(.active) {
            color: #94A3B8;
        }
        
        .verifyap-nav-item:not(.active):hover {
            background: rgba(255, 255, 255, 0.05);
            color: white;
        }
        
        .verifyap-nav-icon {
            font-size: 18px;
            width: 20px;
            text-align: center;
        }
        
        .verifyap-sidebar-footer {
            padding: 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .verifyap-user-profile {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 8px;
            border-radius: 8px;
        }
        
        .verifyap-user-avatar {
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }
        
        .verifyap-user-name {
            font-size: 13px;
            font-weight: 600;
            color: white;
        }
        
        .verifyap-user-role {
            font-size: 11px;
            color: #94A3B8;
        }
        
        /* MAIN CONTENT ADJUSTMENT */
        .verifyap-main-content {
            margin-left: 260px;
            min-height: 100vh;
        }
        
        /* Mobile responsive */
        @media (max-width: 768px) {
            .verifyap-sidebar {
                transform: translateX(-100%);
                transition: transform 0.3s;
            }
            
            .verifyap-sidebar.mobile-open {
                transform: translateX(0);
            }
            
            .verifyap-main-content {
                margin-left: 0;
            }
        }
    </style>
    """


def get_sidebar_html(current_page="dashboard"):
    """
    Generate sidebar HTML
    
    Args:
        current_page: One of 'dashboard', 'admin', 'invoices'
    """
    
    nav_items = [
        {"id": "dashboard", "icon": "📊", "label": "Dashboard", "url": "/"},
        {"id": "admin", "icon": "📝", "label": "Purchase Orders", "url": "/admin"},
        {"id": "invoices", "icon": "💰", "label": "Accounts Payable", "url": "/invoices"},
    ]
    
    nav_html = ""
    for item in nav_items:
        active_class = "active" if item["id"] == current_page else ""
        nav_html += f"""
        <a href="{item['url']}" class="verifyap-nav-item {active_class}">
            <span class="verifyap-nav-icon">{item['icon']}</span>
            <span>{item['label']}</span>
        </a>
        """
    
    return f"""
    <div class="verifyap-sidebar">
        <div class="verifyap-sidebar-header">
            <div class="verifyap-logo">
                <div class="verifyap-logo-icon">✓</div>
                <div class="verifyap-logo-text">VerifyAP</div>
            </div>
            <div class="verifyap-tagline">3-Way Match Automation</div>
        </div>
        
        <nav class="verifyap-nav">
            {nav_html}
        </nav>
        
        <div class="verifyap-sidebar-footer">
            <div class="verifyap-user-profile">
                <div class="verifyap-user-avatar">👤</div>
                <div style="flex: 1;">
                    <div class="verifyap-user-name">Admin User</div>
                    <div class="verifyap-user-role">Administrator</div>
                </div>
            </div>
        </div>
    </div>
    """


def wrap_with_sidebar(page_content, current_page="dashboard"):
    """
    Wrap any page content with the sidebar
    
    Args:
        page_content: The main page HTML content
        current_page: Which page is active
    
    Returns:
        Complete HTML with sidebar
    """
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VerifyAP</title>
        {get_sidebar_styles()}
    </head>
    <body>
        {get_sidebar_html(current_page)}
        <div class="verifyap-main-content">
            {page_content}
        </div>
    </body>
    </html>
    """
