"""
Invoice matching logic for 3-way match
Compares Invoice vs PO vs Packing Slip
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class InvoiceLineItem:
    """Represents a line item from an invoice"""
    item_description: str
    quantity: float
    unit_price: float
    line_total: float


@dataclass
class InvoiceData:
    """Represents extracted invoice data"""
    invoice_number: str
    po_number: Optional[str]
    vendor_name: str
    invoice_date: Optional[str]
    line_items: List[InvoiceLineItem]
    total_amount: float
    tax_amount: Optional[float] = None
    shipping_amount: Optional[float] = None


class ThreeWayMatcher:
    """Performs 3-way matching between PO, Packing Slip, and Invoice"""
    
    def __init__(self):
        self.tolerance = 0.01  # 1% price tolerance
    
    def match_invoice(
        self, 
        invoice: InvoiceData, 
        po_data: Optional[Dict] = None,
        packing_slip_data: Optional[Dict] = None
    ) -> Dict:
        """
        Perform 3-way match
        
        Returns:
            {
                "match_status": "APPROVE" | "REVIEW" | "REJECT",
                "discrepancies": [...],
                "summary": "...",
                "details": {...}
            }
        """
        discrepancies = []
        warnings = []
        
        # Check if we have PO data
        if not po_data:
            return {
                "match_status": "REJECT",
                "discrepancies": [f"No PO found for PO# {invoice.po_number}"],
                "summary": "Cannot match - PO not found in system",
                "details": {}
            }
        
        # 1. Vendor Match
        if invoice.vendor_name.lower() != po_data.get('vendor', '').lower():
            discrepancies.append(
                f"Vendor mismatch: Invoice shows '{invoice.vendor_name}' but PO shows '{po_data.get('vendor')}'"
            )
        
        # 2. Line Item Matching
        invoice_items = {item.item_description.lower(): item for item in invoice.line_items}
        po_items = {item.get('description', '').lower(): item for item in po_data.get('line_items', [])}
        
        # Check for items on invoice not on PO
        for inv_desc, inv_item in invoice_items.items():
            if inv_desc not in po_items:
                discrepancies.append(
                    f"Invoice line '{inv_item.item_description}' not found on PO"
                )
            else:
                po_item = po_items[inv_desc]
                
                # Price comparison
                po_price = po_item.get('unit_price', 0)
                price_diff_pct = abs(inv_item.unit_price - po_price) / po_price if po_price > 0 else 1
                
                if price_diff_pct > self.tolerance:
                    discrepancies.append(
                        f"{inv_item.item_description}: Price mismatch - "
                        f"Invoice ${inv_item.unit_price:.2f} vs PO ${po_price:.2f} "
                        f"({price_diff_pct*100:.1f}% difference)"
                    )
                
                # Quantity comparison (if we have packing slip data)
                if packing_slip_data:
                    ps_items = {
                        item.get('description', '').lower(): item 
                        for item in packing_slip_data.get('line_items', [])
                    }
                    
                    if inv_desc in ps_items:
                        received_qty = ps_items[inv_desc].get('quantity_received', 0)
                        if inv_item.quantity > received_qty:
                            discrepancies.append(
                                f"{inv_item.item_description}: Billing for {inv_item.quantity} "
                                f"but only received {received_qty}"
                            )
                        elif inv_item.quantity < received_qty:
                            warnings.append(
                                f"{inv_item.item_description}: Received {received_qty} "
                                f"but only billed for {inv_item.quantity}"
                            )
        
        # 3. Total Amount Check
        po_total = sum(
            item.get('quantity_ordered', 0) * item.get('unit_price', 0) 
            for item in po_data.get('line_items', [])
        )
        
        if abs(invoice.total_amount - po_total) / po_total > 0.05:  # 5% tolerance
            warnings.append(
                f"Total amount difference: Invoice ${invoice.total_amount:.2f} "
                f"vs PO expected ${po_total:.2f}"
            )
        
        # Determine status
        if len(discrepancies) == 0:
            match_status = "APPROVE"
            summary = "✓ All checks passed - Ready for payment"
        elif len(discrepancies) <= 2 and len(warnings) > 0:
            match_status = "REVIEW"
            summary = f"⚠ {len(discrepancies)} discrepancies found - Needs review"
        else:
            match_status = "REJECT"
            summary = f"✗ {len(discrepancies)} discrepancies found - Do not pay"
        
        return {
            "match_status": match_status,
            "discrepancies": discrepancies,
            "warnings": warnings,
            "summary": summary,
            "details": {
                "invoice_total": invoice.total_amount,
                "po_total": po_total,
                "items_checked": len(invoice_items),
                "has_packing_slip": packing_slip_data is not None
            }
        }


def parse_invoice_from_vision(vision_data: Dict) -> InvoiceData:
    """Parse Claude Vision output into InvoiceData structure"""
    
    line_items = []
    for item in vision_data.get('line_items', []):
        line_items.append(InvoiceLineItem(
            item_description=item.get('description', ''),
            quantity=float(item.get('quantity', 0)),
            unit_price=float(item.get('unit_price', 0)),
            line_total=float(item.get('line_total', 0))
        ))
    
    return InvoiceData(
        invoice_number=vision_data.get('invoice_number', ''),
        po_number=vision_data.get('po_number'),
        vendor_name=vision_data.get('vendor', ''),
        invoice_date=vision_data.get('invoice_date'),
        line_items=line_items,
        total_amount=float(vision_data.get('total_amount', 0)),
        tax_amount=vision_data.get('tax_amount'),
        shipping_amount=vision_data.get('shipping_amount')
    )
