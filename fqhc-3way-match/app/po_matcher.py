"""
PO Matcher Module
Handles CSV loading, PO lookup, and quantity matching logic
"""

import csv
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal


@dataclass
class POLineItem:
    """Represents a single line item in a PO"""
    item_id: str
    description: str
    quantity_ordered: float
    unit_price: float
    total: float
    
    def __post_init__(self):
        """Convert strings to appropriate types"""
        self.quantity_ordered = float(self.quantity_ordered)
        self.unit_price = float(self.unit_price)
        self.total = float(self.total)


@dataclass
class PurchaseOrder:
    """Represents a complete Purchase Order from Netsuite"""
    po_number: str
    vendor_name: str
    vendor_id: str
    po_date: str
    expected_delivery_date: str
    total_amount: float
    status: str
    line_items: List[POLineItem]
    
    def __post_init__(self):
        """Ensure line_items is a list"""
        if not isinstance(self.line_items, list):
            self.line_items = []


@dataclass
class MatchResult:
    """Result of matching a packing slip against a PO"""
    po_found: bool
    po_number: Optional[str]
    vendor_match: bool
    discrepancies: List[str]
    matched_items: List[Dict]
    unmatched_items: List[Dict]
    has_discrepancies: bool
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class POManager:
    """
    Manages the Purchase Order database
    Loads from CSV and provides lookup/matching functionality
    """
    
    def __init__(self):
        self.po_dict: Dict[str, PurchaseOrder] = {}
        self.vendor_index: Dict[str, List[str]] = {}  # vendor_name -> list of PO numbers
    
    def load_from_csv(self, csv_path: str):
        """
        Load POs from Netsuite CSV export
        
        Expected CSV format:
        PO Number, Vendor Name, Vendor ID, PO Date, Expected Delivery, Status, 
        Item ID, Item Description, Quantity Ordered, Unit Price, Line Total
        
        Note: Netsuite exports have one row per line item, so we need to group by PO
        """
        po_staging: Dict[str, Dict] = {}
        
        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                po_number = row['PO Number'].strip()
                
                # Initialize PO if first time seeing it
                if po_number not in po_staging:
                    po_staging[po_number] = {
                        'po_number': po_number,
                        'vendor_name': row['Vendor Name'].strip(),
                        'vendor_id': row.get('Vendor ID', '').strip(),
                        'po_date': row.get('PO Date', '').strip(),
                        'expected_delivery_date': row.get('Expected Delivery', '').strip(),
                        'status': row.get('Status', 'Open').strip(),
                        'line_items': [],
                        'total_amount': 0.0
                    }
                
                # Add line item
                line_item = POLineItem(
                    item_id=row.get('Item ID', '').strip(),
                    description=row.get('Item Description', '').strip(),
                    quantity_ordered=float(row.get('Quantity Ordered', 0)),
                    unit_price=float(row.get('Unit Price', 0)),
                    total=float(row.get('Line Total', 0))
                )
                
                po_staging[po_number]['line_items'].append(line_item)
                po_staging[po_number]['total_amount'] += line_item.total
        
        # Convert staging dict to PurchaseOrder objects
        for po_number, po_data in po_staging.items():
            po = PurchaseOrder(**po_data)
            self.po_dict[po_number] = po
            
            # Build vendor index for faster lookups
            vendor_name = po.vendor_name.lower()
            if vendor_name not in self.vendor_index:
                self.vendor_index[vendor_name] = []
            self.vendor_index[vendor_name].append(po_number)
        
        print(f"✓ Loaded {len(self.po_dict)} POs with {sum(len(po.line_items) for po in self.po_dict.values())} total line items")
    
    def get_po(self, po_number: str) -> Optional[PurchaseOrder]:
        """Retrieve a PO by number"""
        # Normalize PO number (remove spaces, handle common formats)
        normalized = self._normalize_po_number(po_number)
        return self.po_dict.get(normalized)
    
    def _normalize_po_number(self, po_number: str) -> str:
        """
        Normalize PO number for matching
        Handles variations like: PO12345, PO-12345, 12345
        """
        if not po_number:
            return ""
        
        # Remove common prefixes and special characters
        normalized = po_number.upper().strip()
        normalized = normalized.replace('PO-', '').replace('PO', '').replace('#', '').replace(' ', '')
        
        # Check if this normalized version exists
        if normalized in self.po_dict:
            return normalized
        
        # Check with PO prefix
        with_prefix = f"PO{normalized}"
        if with_prefix in self.po_dict:
            return with_prefix
        
        # Return original if no match found
        return po_number.strip()
    
    def match_packing_slip(self, vision_data: Dict) -> MatchResult:
        """
        Match packing slip data (from Vision API) against PO database
        Identifies discrepancies in quantities and items
        """
        po_number = vision_data.get('po_number', '')
        vendor_from_slip = vision_data.get('vendor_name', '').lower()
        items_received = vision_data.get('line_items', [])
        
        # Look up PO
        po = self.get_po(po_number)
        
        if not po:
            return MatchResult(
                po_found=False,
                po_number=po_number,
                vendor_match=False,
                discrepancies=[f"PO {po_number} not found in database"],
                matched_items=[],
                unmatched_items=items_received,
                has_discrepancies=True
            )
        
        # Check vendor match
        vendor_match = self._fuzzy_vendor_match(vendor_from_slip, po.vendor_name.lower())
        
        discrepancies = []
        if not vendor_match:
            discrepancies.append(
                f"Vendor mismatch: Slip shows '{vision_data.get('vendor_name')}' "
                f"but PO is for '{po.vendor_name}'"
            )
        
        # Match line items
        matched_items = []
        unmatched_items = []
        
        for received_item in items_received:
            item_desc = received_item.get('description', '').lower()
            qty_received = float(received_item.get('quantity_received', 0))
            
            # Try to find matching line item in PO
            matched = False
            for po_item in po.line_items:
                # Fuzzy match on description or item ID
                if (self._fuzzy_item_match(item_desc, po_item.description.lower()) or 
                    item_desc in po_item.item_id.lower()):
                    
                    matched = True
                    qty_ordered = po_item.quantity_ordered
                    
                    match_info = {
                        'description': received_item.get('description'),
                        'qty_received': qty_received,
                        'qty_ordered': qty_ordered,
                        'po_item_id': po_item.item_id,
                        'match_type': 'exact' if qty_received == qty_ordered else 'discrepancy'
                    }
                    
                    # Check quantity discrepancy
                    if qty_received != qty_ordered:
                        discrepancy_msg = (
                            f"{po_item.description}: "
                            f"Received {qty_received} but PO ordered {qty_ordered} "
                            f"(Difference: {qty_received - qty_ordered:+.0f})"
                        )
                        discrepancies.append(discrepancy_msg)
                        match_info['discrepancy'] = discrepancy_msg
                    
                    # Check for handwritten notes
                    if received_item.get('has_handwritten_notes'):
                        notes = received_item.get('handwritten_notes', '')
                        discrepancies.append(
                            f"{po_item.description}: Handwritten note found - '{notes}'"
                        )
                        match_info['notes'] = notes
                    
                    matched_items.append(match_info)
                    break
            
            if not matched:
                unmatched_items.append(received_item)
                discrepancies.append(
                    f"Item not in PO: {received_item.get('description')} "
                    f"(Qty: {qty_received})"
                )
        
        # Check for items in PO that weren't received
        received_descriptions = {item.get('description', '').lower() for item in items_received}
        for po_item in po.line_items:
            found_in_shipment = any(
                self._fuzzy_item_match(desc, po_item.description.lower()) 
                for desc in received_descriptions
            )
            if not found_in_shipment:
                discrepancies.append(
                    f"Missing from shipment: {po_item.description} "
                    f"(PO ordered {po_item.quantity_ordered})"
                )
        
        return MatchResult(
            po_found=True,
            po_number=po_number,
            vendor_match=vendor_match,
            discrepancies=discrepancies,
            matched_items=matched_items,
            unmatched_items=unmatched_items,
            has_discrepancies=len(discrepancies) > 0
        )
    
    def _fuzzy_vendor_match(self, vendor1: str, vendor2: str) -> bool:
        """
        Fuzzy match vendor names
        Handles variations like "McKesson Corp" vs "McKesson Corporation"
        """
        if not vendor1 or not vendor2:
            return False
        
        # Exact match
        if vendor1 == vendor2:
            return True
        
        # Remove common suffixes
        suffixes = ['inc', 'inc.', 'corp', 'corp.', 'corporation', 'llc', 'ltd', 'ltd.', 'co.', 'company']
        clean1 = vendor1.lower()
        clean2 = vendor2.lower()
        
        for suffix in suffixes:
            clean1 = clean1.replace(suffix, '').strip()
            clean2 = clean2.replace(suffix, '').strip()
        
        # Check if one contains the other
        return clean1 in clean2 or clean2 in clean1
    
    def _fuzzy_item_match(self, item1: str, item2: str, threshold: float = 0.6) -> bool:
        """
        Fuzzy match item descriptions
        Uses simple word overlap ratio
        """
        if not item1 or not item2:
            return False
        
        # Exact match
        if item1 == item2:
            return True
        
        # Word overlap
        words1 = set(item1.lower().split())
        words2 = set(item2.lower().split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'of', 'in', 'for', 'with'}
        words1 -= stop_words
        words2 -= stop_words
        
        if not words1 or not words2:
            return False
        
        overlap = len(words1 & words2)
        total = min(len(words1), len(words2))
        
        return (overlap / total) >= threshold if total > 0 else False
    
    def get_vendor_pos(self, vendor_name: str) -> List[PurchaseOrder]:
        """Get all POs for a specific vendor"""
        vendor_key = vendor_name.lower()
        po_numbers = self.vendor_index.get(vendor_key, [])
        return [self.po_dict[po_num] for po_num in po_numbers]
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        total_value = sum(po.total_amount for po in self.po_dict.values())
        total_items = sum(len(po.line_items) for po in self.po_dict.values())
        
        return {
            'total_pos': len(self.po_dict),
            'total_line_items': total_items,
            'total_value': total_value,
            'unique_vendors': len(self.vendor_index)
        }
