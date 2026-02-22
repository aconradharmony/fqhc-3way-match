"""
Dynamic header generator for white-label branding
"""

def generate_branded_header(org_settings, current_page="dashboard"):
    """
    Generate header HTML with organization branding
    
    Args:
        org_settings: OrganizationSettings object
        current_page: 'dashboard', 'invoices', 'admin', etc.
    
    Returns:
        HTML string for header
    """
    
    # Determine navigation links based on current page
    nav_links = []
    
    if current_page != "dashboard":
        nav_links.append('<a href="/" class="nav-link">📊 Dashboard</a>')
    
    if current_page != "invoices":
        nav_links.append('<a href="/invoices" class="nav-link">💰 Invoices</a>')
    
    if current_page != "admin":
        nav_links.append('<a href="/admin" class="nav-link">⚙️ Admin</a>')
    
    # Only show branding link if not default org
    if org_settings.id != "default":
        nav_links.append('<a href="/branding" class="nav-link">🎨 Branding</a>')
    
    nav_html = ' '.join(nav_links)
    
    # Logo HTML
    logo_html = ""
    if org_settings.logo_url:
        logo_html = f'<img src="{org_settings.logo_url}" alt="{org_settings.name}" class="org-logo">'
    
    # Powered by badge (if enabled)
    powered_by_html = ""
    if org_settings.show_powered_by:
        powered_by_html = '<p class="powered-by">Powered by <strong>VerifyAP</strong></p>'
    
    return f"""
    <div class="header" style="background: linear-gradient(135deg, {org_settings.primary_color} 0%, {org_settings.secondary_color} 100%);">
        <div class="header-nav">
            {nav_html}
        </div>
        <div class="header-content">
            {logo_html}
            <h1>{org_settings.get_display_name()}</h1>
            <p class="tagline">{org_settings.get_tagline()}</p>
            {powered_by_html}
        </div>
    </div>
    """


def generate_branded_styles(org_settings):
    """
    Generate CSS styles based on organization branding
    
    Returns:
        CSS string
    """
    return f"""
    <style>
        .header {{
            background: linear-gradient(135deg, {org_settings.primary_color} 0%, {org_settings.secondary_color} 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: relative;
        }}
        
        .header-nav {{
            position: absolute;
            top: 1rem;
            right: 2rem;
            display: flex;
            gap: 1rem;
        }}
        
        .nav-link {{
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s;
            font-size: 0.9rem;
        }}
        
        .nav-link:hover {{
            background: rgba(255,255,255,0.3);
            transform: translateY(-2px);
        }}
        
        .header-content {{
            text-align: center;
            max-width: 800px;
            margin: 0 auto;
        }}
        
        .org-logo {{
            max-height: 60px;
            max-width: 300px;
            margin-bottom: 1rem;
            object-fit: contain;
        }}
        
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .tagline {{
            opacity: 0.9;
            font-size: 1rem;
        }}
        
        .powered-by {{
            opacity: 0.7;
            font-size: 0.85rem;
            margin-top: 0.5rem;
        }}
        
        .powered-by strong {{
            font-weight: 600;
        }}
        
        /* Buttons use primary color */
        .btn {{
            background: {org_settings.primary_color};
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .btn:hover {{
            filter: brightness(0.9);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }}
        
        /* Links use primary color */
        a.text-link {{
            color: {org_settings.primary_color};
        }}
        
        /* Status badges */
        .status-badge.approved {{
            background: #c6f6d5;
            color: #22543d;
        }}
        
        .status-badge.review {{
            background: #feebc8;
            color: #744210;
        }}
        
        .status-badge.reject {{
            background: #fed7d7;
            color: #742a2a;
        }}
    </style>
    """
