"""
Organization settings for white-label branding
Each FQHC can customize their portal appearance
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OrganizationSettings:
    """Organization branding and settings"""
    id: str
    name: str  # e.g., "Harmony Health Center"
    logo_url: Optional[str] = None  # URL to uploaded logo
    primary_color: str = "#667eea"  # Default purple
    secondary_color: str = "#764ba2"  # Default purple gradient
    portal_name: Optional[str] = None  # e.g., "Harmony Invoice Portal" (if they want custom name)
    tagline: Optional[str] = None  # Custom tagline
    show_powered_by: bool = True  # Show "Powered by VerifyAP"
    custom_domain: Optional[str] = None  # e.g., "invoices.harmonyhello.ai"
    
    # Subscription info
    subscription_tier: str = "professional"  # basic, professional, enterprise
    max_monthly_transactions: int = 1000
    
    # Feature flags
    enable_invoices: bool = True
    enable_packing_slips: bool = True
    enable_analytics: bool = True
    
    def get_display_name(self) -> str:
        """Get the name to display in header"""
        return self.portal_name or self.name
    
    def get_tagline(self) -> str:
        """Get the tagline to display"""
        return self.tagline or "Powered by VerifyAP"


# Default organization for single-tenant or demo
DEFAULT_ORG = OrganizationSettings(
    id="default",
    name="VerifyAP",
    logo_url=None,
    primary_color="#667eea",
    secondary_color="#764ba2",
    portal_name="VerifyAP",
    tagline="3-Way Match Automation",
    show_powered_by=False  # Don't show "powered by" on default
)
