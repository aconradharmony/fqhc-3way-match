def get_branding_html(org_settings):
    """Generate branding customization admin page"""
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Branding Settings - VerifyAP</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #2d3748;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .container {{
            max-width: 1000px;
            margin: 2rem auto;
            padding: 0 1rem;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        h2 {{
            color: #2d3748;
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
        }}
        .form-group {{
            margin-bottom: 1.5rem;
        }}
        label {{
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #4a5568;
        }}
        input[type="text"],
        input[type="url"] {{
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            font-size: 1rem;
        }}
        input[type="color"] {{
            width: 100px;
            height: 50px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
        }}
        .color-preview {{
            display: inline-block;
            margin-left: 1rem;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            color: white;
            font-weight: 600;
        }}
        .logo-upload {{
            border: 2px dashed #cbd5e0;
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            background: #f7fafc;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .logo-upload:hover {{
            border-color: #667eea;
            background: #edf2f7;
        }}
        .logo-preview {{
            max-width: 200px;
            max-height: 100px;
            margin-top: 1rem;
            border-radius: 6px;
        }}
        .btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            border-radius: 6px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .btn:hover {{
            background: #5a67d8;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        .btn-secondary {{
            background: #48bb78;
        }}
        .btn-secondary:hover {{
            background: #38a169;
        }}
        .preview-section {{
            background: #f7fafc;
            border-radius: 8px;
            padding: 2rem;
            margin-top: 2rem;
        }}
        .preview-header {{
            padding: 2rem;
            border-radius: 8px;
            color: white;
            margin-bottom: 1rem;
        }}
        .message {{
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 1rem;
            display: none;
        }}
        .message.success {{
            background: #c6f6d5;
            color: #22543d;
            border-left: 4px solid #48bb78;
        }}
        .help-text {{
            font-size: 0.875rem;
            color: #718096;
            margin-top: 0.25rem;
        }}
        .back-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 Branding Settings</h1>
        <p>Customize your VerifyAP portal appearance</p>
    </div>

    <div class="container">
        <div class="message success" id="message"></div>

        <div class="card">
            <h2>Organization Information</h2>
            
            <div class="form-group">
                <label for="org-name">Organization Name</label>
                <input type="text" id="org-name" value="{org_settings.name}" placeholder="Harmony Health Center">
                <p class="help-text">This appears in your portal header</p>
            </div>

            <div class="form-group">
                <label for="portal-name">Custom Portal Name (Optional)</label>
                <input type="text" id="portal-name" value="{org_settings.portal_name or ''}" placeholder="Harmony Invoice Portal">
                <p class="help-text">Leave blank to use your organization name</p>
            </div>

            <div class="form-group">
                <label for="tagline">Tagline (Optional)</label>
                <input type="text" id="tagline" value="{org_settings.tagline or ''}" placeholder="Powered by VerifyAP">
                <p class="help-text">Appears below your name</p>
            </div>
        </div>

        <div class="card">
            <h2>Logo</h2>
            
            <div class="logo-upload" id="logo-upload-area">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" style="margin: 0 auto; color: #a0aec0;">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                    <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
                <p style="margin-top: 1rem; color: #4a5568;">Click to upload logo</p>
                <p style="margin-top: 0.5rem; color: #a0aec0; font-size: 0.9rem;">PNG, JPG, SVG • Max 2MB • Recommended: 200x80px</p>
                <input type="file" id="logo-input" accept="image/*" style="display: none;">
            </div>

            {f'<img src="{org_settings.logo_url}" class="logo-preview" id="logo-preview">' if org_settings.logo_url else '<div id="logo-preview"></div>'}
        </div>

        <div class="card">
            <h2>Colors</h2>
            
            <div class="form-group">
                <label for="primary-color">Primary Color</label>
                <input type="color" id="primary-color" value="{org_settings.primary_color}">
                <span class="color-preview" id="primary-preview" style="background: {org_settings.primary_color};">
                    {org_settings.primary_color}
                </span>
                <p class="help-text">Main brand color (buttons, headers)</p>
            </div>

            <div class="form-group">
                <label for="secondary-color">Secondary Color</label>
                <input type="color" id="secondary-color" value="{org_settings.secondary_color}">
                <span class="color-preview" id="secondary-preview" style="background: {org_settings.secondary_color};">
                    {org_settings.secondary_color}
                </span>
                <p class="help-text">Used for gradients and accents</p>
            </div>
        </div>

        <div class="card">
            <h2>Preview</h2>
            <div class="preview-section">
                <div class="preview-header" id="preview-header">
                    <img src="" id="preview-logo" style="display: none; max-height: 40px; margin-bottom: 0.5rem;">
                    <h1 id="preview-name">{org_settings.get_display_name()}</h1>
                    <p id="preview-tagline">{org_settings.get_tagline()}</p>
                </div>
                <p style="color: #718096;">This is how your portal header will look</p>
            </div>
        </div>

        <div class="card">
            <button class="btn" id="save-btn">Save Changes</button>
            <a href="/admin" class="back-link" style="margin-left: 1rem;">← Back to Admin</a>
        </div>
    </div>

    <script>
        const logoUploadArea = document.getElementById('logo-upload-area');
        const logoInput = document.getElementById('logo-input');
        const logoPreview = document.getElementById('logo-preview');
        const primaryColor = document.getElementById('primary-color');
        const secondaryColor = document.getElementById('secondary-color');
        const primaryPreview = document.getElementById('primary-preview');
        const secondaryPreview = document.getElementById('secondary-preview');
        const previewHeader = document.getElementById('preview-header');
        const previewLogo = document.getElementById('preview-logo');
        const previewName = document.getElementById('preview-name');
        const previewTagline = document.getElementById('preview-tagline');
        const message = document.getElementById('message');
        
        let currentLogoFile = null;

        // Logo upload
        logoUploadArea.addEventListener('click', () => logoInput.click());
        
        logoInput.addEventListener('change', (e) => {{
            const file = e.target.files[0];
            if (file) {{
                currentLogoFile = file;
                const reader = new FileReader();
                reader.onload = (e) => {{
                    const imgUrl = e.target.result;
                    logoPreview.innerHTML = `<img src="${{imgUrl}}" class="logo-preview">`;
                    previewLogo.src = imgUrl;
                    previewLogo.style.display = 'block';
                }};
                reader.readAsDataURL(file);
            }}
        }});

        // Color pickers
        primaryColor.addEventListener('input', (e) => {{
            const color = e.target.value;
            primaryPreview.style.background = color;
            primaryPreview.textContent = color;
            updatePreviewGradient();
        }});

        secondaryColor.addEventListener('input', (e) => {{
            const color = e.target.value;
            secondaryPreview.style.background = color;
            secondaryPreview.textContent = color;
            updatePreviewGradient();
        }});

        function updatePreviewGradient() {{
            const primary = primaryColor.value;
            const secondary = secondaryColor.value;
            previewHeader.style.background = `linear-gradient(135deg, ${{primary}} 0%, ${{secondary}} 100%)`;
        }}

        // Live preview updates
        document.getElementById('org-name').addEventListener('input', (e) => {{
            const portalName = document.getElementById('portal-name').value;
            previewName.textContent = portalName || e.target.value;
        }});

        document.getElementById('portal-name').addEventListener('input', (e) => {{
            const orgName = document.getElementById('org-name').value;
            previewName.textContent = e.target.value || orgName;
        }});

        document.getElementById('tagline').addEventListener('input', (e) => {{
            previewTagline.textContent = e.target.value || 'Powered by VerifyAP';
        }});

        // Save
        document.getElementById('save-btn').addEventListener('click', async () => {{
            const formData = new FormData();
            
            formData.append('name', document.getElementById('org-name').value);
            formData.append('portal_name', document.getElementById('portal-name').value);
            formData.append('tagline', document.getElementById('tagline').value);
            formData.append('primary_color', primaryColor.value);
            formData.append('secondary_color', secondaryColor.value);
            
            if (currentLogoFile) {{
                formData.append('logo', currentLogoFile);
            }}

            try {{
                const response = await fetch('/api/branding/save', {{
                    method: 'POST',
                    body: formData
                }});

                if (response.ok) {{
                    message.textContent = '✓ Branding settings saved successfully!';
                    message.className = 'message success';
                    message.style.display = 'block';
                    
                    // Reload page after 2 seconds to show new branding
                    setTimeout(() => window.location.reload(), 2000);
                }} else {{
                    throw new Error('Failed to save');
                }}
            }} catch (error) {{
                alert('Error saving settings: ' + error.message);
            }}
        }});

        // Initialize preview
        updatePreviewGradient();
    </script>
</body>
</html>
    """
