"""
Test Script for PO Matcher
Validates CSV loading and matching logic
"""

import sys
sys.path.append('app')

from po_matcher import POManager, MatchResult


def test_csv_loading():
    """Test CSV loading functionality"""
    print("=" * 60)
    print("TEST 1: CSV Loading")
    print("=" * 60)
    
    manager = POManager()
    manager.load_from_csv('data/open_pos.csv')
    
    print(f"\n✓ Loaded {len(manager.po_dict)} Purchase Orders")
    print(f"✓ {len(manager.vendor_index)} unique vendors")
    
    # Show statistics
    stats = manager.get_statistics()
    print(f"\nStatistics:")
    print(f"  Total POs: {stats['total_pos']}")
    print(f"  Total Line Items: {stats['total_line_items']}")
    print(f"  Total Value: ${stats['total_value']:,.2f}")
    print(f"  Unique Vendors: {stats['unique_vendors']}")
    
    print("\n✅ CSV Loading Test PASSED\n")


def test_po_lookup():
    """Test PO retrieval"""
    print("=" * 60)
    print("TEST 2: PO Lookup")
    print("=" * 60)
    
    manager = POManager()
    manager.load_from_csv('data/open_pos.csv')
    
    # Test exact match
    po = manager.get_po('PO12345')
    assert po is not None, "Failed to find PO12345"
    print(f"\n✓ Found PO: {po.po_number}")
    print(f"  Vendor: {po.vendor_name}")
    print(f"  Line Items: {len(po.line_items)}")
    print(f"  Total: ${po.total_amount:,.2f}")
    
    # Test normalized match (without PO prefix)
    po2 = manager.get_po('12345')
    assert po2 is not None, "Failed normalized match"
    print(f"\n✓ Normalized match works: '12345' → 'PO12345'")
    
    # Test not found
    po3 = manager.get_po('PO99999')
    assert po3 is None, "Should not find non-existent PO"
    print(f"✓ Correctly returns None for non-existent PO")
    
    print("\n✅ PO Lookup Test PASSED\n")


def test_perfect_match():
    """Test matching with perfect packing slip data"""
    print("=" * 60)
    print("TEST 3: Perfect Match Scenario")
    print("=" * 60)
    
    manager = POManager()
    manager.load_from_csv('data/open_pos.csv')
    
    # Simulate vision API returning perfect data
    vision_data = {
        "po_number": "PO12345",
        "vendor_name": "McKesson Medical Supply",
        "line_items": [
            {
                "description": "Nitrile Gloves Large Box of 100",
                "quantity_received": 10,
                "has_handwritten_notes": False,
                "handwritten_notes": None
            },
            {
                "description": "Gauze Pads 4x4 Sterile 100ct",
                "quantity_received": 20,
                "has_handwritten_notes": False,
                "handwritten_notes": None
            },
            {
                "description": "Alcohol Prep Pads 200ct",
                "quantity_received": 15,
                "has_handwritten_notes": False,
                "handwritten_notes": None
            }
        ]
    }
    
    result = manager.match_packing_slip(vision_data)
    
    print(f"\nPO Found: {result.po_found}")
    print(f"Vendor Match: {result.vendor_match}")
    print(f"Discrepancies: {len(result.discrepancies)}")
    print(f"Matched Items: {len(result.matched_items)}")
    
    assert result.po_found, "Should find PO"
    assert result.vendor_match, "Vendor should match"
    assert len(result.discrepancies) == 0, "Should have no discrepancies"
    
    print("\n✅ Perfect Match Test PASSED\n")


def test_quantity_discrepancy():
    """Test matching with quantity discrepancies"""
    print("=" * 60)
    print("TEST 4: Quantity Discrepancy Detection")
    print("=" * 60)
    
    manager = POManager()
    manager.load_from_csv('data/open_pos.csv')
    
    # Simulate receiving fewer items than ordered
    vision_data = {
        "po_number": "PO12345",
        "vendor_name": "McKesson Medical Supply",
        "line_items": [
            {
                "description": "Nitrile Gloves Large Box of 100",
                "quantity_received": 8,  # Ordered 10, received 8
                "has_handwritten_notes": True,
                "handwritten_notes": "Checkmark and note: 2 boxes damaged"
            },
            {
                "description": "Gauze Pads 4x4 Sterile 100ct",
                "quantity_received": 20,
                "has_handwritten_notes": False,
                "handwritten_notes": None
            }
        ]
    }
    
    result = manager.match_packing_slip(vision_data)
    
    print(f"\nPO Found: {result.po_found}")
    print(f"Has Discrepancies: {result.has_discrepancies}")
    print(f"\nDiscrepancies Found:")
    for disc in result.discrepancies:
        print(f"  • {disc}")
    
    assert result.has_discrepancies, "Should flag discrepancies"
    assert len(result.discrepancies) >= 2, "Should have at least 2 discrepancies"
    
    # Check for handwritten note alert
    has_note_alert = any('Handwritten' in d for d in result.discrepancies)
    assert has_note_alert, "Should alert about handwritten note"
    
    print("\n✅ Quantity Discrepancy Test PASSED\n")


def test_missing_items():
    """Test when items are missing from shipment"""
    print("=" * 60)
    print("TEST 5: Missing Items Detection")
    print("=" * 60)
    
    manager = POManager()
    manager.load_from_csv('data/open_pos.csv')
    
    # Simulate receiving only 1 out of 3 items
    vision_data = {
        "po_number": "PO12345",
        "vendor_name": "McKesson Medical Supply",
        "line_items": [
            {
                "description": "Nitrile Gloves Large Box of 100",
                "quantity_received": 10,
                "has_handwritten_notes": False,
                "handwritten_notes": None
            }
            # Missing: Gauze Pads and Alcohol Prep Pads
        ]
    }
    
    result = manager.match_packing_slip(vision_data)
    
    print(f"\nHas Discrepancies: {result.has_discrepancies}")
    print(f"\nDiscrepancies Found:")
    for disc in result.discrepancies:
        print(f"  • {disc}")
    
    # Should flag 2 missing items
    missing_alerts = [d for d in result.discrepancies if 'Missing from shipment' in d]
    assert len(missing_alerts) == 2, f"Should flag 2 missing items, got {len(missing_alerts)}"
    
    print("\n✅ Missing Items Test PASSED\n")


def test_extra_items():
    """Test when extra items are received"""
    print("=" * 60)
    print("TEST 6: Extra Items Detection")
    print("=" * 60)
    
    manager = POManager()
    manager.load_from_csv('data/open_pos.csv')
    
    # Simulate receiving items not on the PO
    vision_data = {
        "po_number": "PO12345",
        "vendor_name": "McKesson Medical Supply",
        "line_items": [
            {
                "description": "Nitrile Gloves Large Box of 100",
                "quantity_received": 10,
                "has_handwritten_notes": False,
                "handwritten_notes": None
            },
            {
                "description": "Bandages Adhesive Assorted",  # Not on PO12345
                "quantity_received": 5,
                "has_handwritten_notes": False,
                "handwritten_notes": None
            }
        ]
    }
    
    result = manager.match_packing_slip(vision_data)
    
    print(f"\nHas Discrepancies: {result.has_discrepancies}")
    print(f"Unmatched Items: {len(result.unmatched_items)}")
    print(f"\nDiscrepancies Found:")
    for disc in result.discrepancies:
        print(f"  • {disc}")
    
    # Should have unmatched items
    assert len(result.unmatched_items) > 0, "Should flag extra items"
    
    print("\n✅ Extra Items Test PASSED\n")


def test_vendor_mismatch():
    """Test vendor name mismatch detection"""
    print("=" * 60)
    print("TEST 7: Vendor Mismatch Detection")
    print("=" * 60)
    
    manager = POManager()
    manager.load_from_csv('data/open_pos.csv')
    
    # Simulate wrong vendor on packing slip
    vision_data = {
        "po_number": "PO12345",
        "vendor_name": "Cardinal Health",  # Wrong! Should be McKesson
        "line_items": [
            {
                "description": "Nitrile Gloves Large Box of 100",
                "quantity_received": 10,
                "has_handwritten_notes": False,
                "handwritten_notes": None
            }
        ]
    }
    
    result = manager.match_packing_slip(vision_data)
    
    print(f"\nVendor Match: {result.vendor_match}")
    print(f"\nDiscrepancies Found:")
    for disc in result.discrepancies:
        print(f"  • {disc}")
    
    assert not result.vendor_match, "Should detect vendor mismatch"
    
    vendor_alert = any('Vendor mismatch' in d for d in result.discrepancies)
    assert vendor_alert, "Should have vendor mismatch alert"
    
    print("\n✅ Vendor Mismatch Test PASSED\n")


def test_fuzzy_matching():
    """Test fuzzy matching capabilities"""
    print("=" * 60)
    print("TEST 8: Fuzzy Matching")
    print("=" * 60)
    
    manager = POManager()
    manager.load_from_csv('data/open_pos.csv')
    
    # Test vendor fuzzy matching
    print("\nTesting vendor name variations:")
    
    test_cases = [
        ("McKesson Medical Supply", "McKesson Medical Supply", True),
        ("McKesson Medical Supply", "McKesson Medical", True),
        ("McKesson Corp", "McKesson Corporation", True),
        ("Cardinal Health Inc", "Cardinal Health", True),
        ("Totally Different Vendor", "McKesson Medical Supply", False),
    ]
    
    for vendor1, vendor2, expected in test_cases:
        result = manager._fuzzy_vendor_match(vendor1.lower(), vendor2.lower())
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{vendor1}' vs '{vendor2}': {result}")
        assert result == expected, f"Failed fuzzy match: {vendor1} vs {vendor2}"
    
    print("\n✅ Fuzzy Matching Test PASSED\n")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "=" * 60)
    print("FQHC 3-Way Match System - Test Suite")
    print("=" * 60 + "\n")
    
    try:
        test_csv_loading()
        test_po_lookup()
        test_perfect_match()
        test_quantity_discrepancy()
        test_missing_items()
        test_extra_items()
        test_vendor_mismatch()
        test_fuzzy_matching()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe PO matching logic is working correctly.")
        print("You can now run the FastAPI application.\n")
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"\nError: {e}\n")
        sys.exit(1)
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ UNEXPECTED ERROR")
        print("=" * 60)
        print(f"\nError: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
