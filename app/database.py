"""
VerifyAP — Database Layer
Async PostgreSQL with connection pooling via asyncpg.
Falls back to in-memory storage when DATABASE_URL is not set.
"""

import os
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

# ---------------------------------------------------------------------------
# In-Memory Fallback Store (used when no DATABASE_URL is configured)
# This preserves backward compatibility with the existing MVP.
# ---------------------------------------------------------------------------

class InMemoryStore:
    """Drop-in replacement that keeps data in dicts. Data lost on restart."""

    def __init__(self):
        self.purchase_orders: Dict[str, Dict] = {}
        self.po_line_items: Dict[str, List[Dict]] = {}
        self.packing_slips: Dict[str, Dict] = {}
        self.slip_line_items: Dict[str, List[Dict]] = {}
        self.invoices: Dict[str, Dict] = {}
        self.invoice_line_items: Dict[str, List[Dict]] = {}
        self.match_results: Dict[str, Dict] = {}
        self.match_line_details: Dict[str, List[Dict]] = {}
        self.document_events: List[Dict] = []

    # -- Purchase Orders ---------------------------------------------------

    def save_po(self, po_data: Dict) -> str:
        po_id = po_data.get("id", str(uuid.uuid4()))
        po_data["id"] = po_id
        po_data.setdefault("uploaded_at", datetime.now(timezone.utc).isoformat())
        po_data.setdefault("status", "active")
        self.purchase_orders[po_id] = po_data
        self._log_event(po_data.get("po_number"), "po_uploaded", "po", po_id)
        return po_id

    def save_po_lines(self, po_id: str, lines: List[Dict]):
        self.po_line_items[po_id] = lines

    def get_po(self, po_id: str) -> Optional[Dict]:
        po = self.purchase_orders.get(po_id)
        if po:
            po["line_items"] = self.po_line_items.get(po_id, [])
        return po

    def get_po_by_number(self, po_number: str) -> Optional[Dict]:
        for po in self.purchase_orders.values():
            if po.get("po_number") == po_number:
                po["line_items"] = self.po_line_items.get(po["id"], [])
                return po
        return None

    def list_pos(self, status: Optional[str] = None) -> List[Dict]:
        results = []
        for po_id, po in self.purchase_orders.items():
            if status and po.get("status") != status:
                continue
            po_copy = dict(po)
            po_copy["line_items"] = self.po_line_items.get(po_id, [])
            po_copy["slip_count"] = sum(
                1 for s in self.packing_slips.values() if s.get("po_id") == po_id
            )
            po_copy["invoice_count"] = sum(
                1 for i in self.invoices.values() if i.get("po_id") == po_id
            )
            # Find latest match
            latest_match = None
            for m in self.match_results.values():
                if m.get("po_id") == po_id:
                    if not latest_match or m.get("created_at", "") > latest_match.get("created_at", ""):
                        latest_match = m
            po_copy["match_status"] = latest_match.get("overall_status", "unmatched") if latest_match else "unmatched"
            po_copy["total_discrepancies"] = latest_match.get("total_discrepancies", 0) if latest_match else 0
            po_copy["amount_delta"] = latest_match.get("amount_delta", 0) if latest_match else 0
            po_copy["product_line_count"] = len([
                l for l in po_copy["line_items"] if not l.get("is_tax_line")
            ])
            results.append(po_copy)
        return sorted(results, key=lambda x: x.get("uploaded_at", ""), reverse=True)

    # -- Packing Slips -----------------------------------------------------

    def save_slip(self, slip_data: Dict) -> str:
        slip_id = slip_data.get("id", str(uuid.uuid4()))
        slip_data["id"] = slip_id
        slip_data.setdefault("uploaded_at", datetime.now(timezone.utc).isoformat())
        slip_data.setdefault("status", "pending")
        self.packing_slips[slip_id] = slip_data
        po_number = slip_data.get("po_number_ocr", "")
        self._log_event(po_number, "slip_uploaded", "slip", slip_id)
        return slip_id

    def save_slip_lines(self, slip_id: str, lines: List[Dict]):
        self.slip_line_items[slip_id] = lines

    def get_slip(self, slip_id: str) -> Optional[Dict]:
        slip = self.packing_slips.get(slip_id)
        if slip:
            slip["line_items"] = self.slip_line_items.get(slip_id, [])
        return slip

    def get_slips_for_po(self, po_id: str) -> List[Dict]:
        return [s for s in self.packing_slips.values() if s.get("po_id") == po_id]

    # -- Invoices ----------------------------------------------------------

    def save_invoice(self, inv_data: Dict) -> str:
        inv_id = inv_data.get("id", str(uuid.uuid4()))
        inv_data["id"] = inv_id
        inv_data.setdefault("uploaded_at", datetime.now(timezone.utc).isoformat())
        inv_data.setdefault("status", "pending")
        self.invoices[inv_id] = inv_data
        po_number = inv_data.get("po_number_ocr", "")
        self._log_event(po_number, "invoice_uploaded", "invoice", inv_id)
        return inv_id

    def save_invoice_lines(self, inv_id: str, lines: List[Dict]):
        self.invoice_line_items[inv_id] = lines

    def get_invoice(self, inv_id: str) -> Optional[Dict]:
        inv = self.invoices.get(inv_id)
        if inv:
            inv["line_items"] = self.invoice_line_items.get(inv_id, [])
        return inv

    # -- Match Results -----------------------------------------------------

    def save_match(self, match_data: Dict) -> str:
        match_id = match_data.get("id", str(uuid.uuid4()))
        match_data["id"] = match_id
        match_data.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        self.match_results[match_id] = match_data
        po_number = ""
        po = self.purchase_orders.get(match_data.get("po_id", ""))
        if po:
            po_number = po.get("po_number", "")
        event_type = "match_3way" if match_data.get("match_type") == "3way" else "match_2way"
        self._log_event(po_number, event_type, "match", match_id)
        return match_id

    def save_match_lines(self, match_id: str, lines: List[Dict]):
        self.match_line_details[match_id] = lines

    def get_match(self, match_id: str) -> Optional[Dict]:
        match = self.match_results.get(match_id)
        if match:
            match["line_details"] = self.match_line_details.get(match_id, [])
        return match

    def get_matches_for_po(self, po_id: str) -> List[Dict]:
        matches = [m for m in self.match_results.values() if m.get("po_id") == po_id]
        for m in matches:
            m["line_details"] = self.match_line_details.get(m["id"], [])
        return sorted(matches, key=lambda x: x.get("created_at", ""), reverse=True)

    def list_discrepancies(self) -> List[Dict]:
        results = []
        for match in self.match_results.values():
            if match.get("total_discrepancies", 0) > 0 or match.get("overall_status") in ("review", "reject"):
                entry = dict(match)
                po = self.purchase_orders.get(match.get("po_id", ""))
                inv = self.invoices.get(match.get("invoice_id", ""))
                entry["po_number"] = po.get("po_number", "") if po else ""
                entry["vendor_name"] = po.get("vendor_name", "") if po else ""
                entry["po_total"] = po.get("total_amount", 0) if po else 0
                entry["invoice_number"] = inv.get("invoice_number", "") if inv else ""
                entry["invoice_total"] = inv.get("total_amount", 0) if inv else 0
                entry["line_details"] = self.match_line_details.get(match["id"], [])
                entry["discrepancy_lines"] = [
                    l for l in entry["line_details"] if l.get("line_status") == "discrepancy"
                ]
                results.append(entry)
        return sorted(results, key=lambda x: x.get("created_at", ""), reverse=True)

    # -- Document Events ---------------------------------------------------

    def _log_event(self, po_number: str, event_type: str, entity_type: str, entity_id: str):
        po_id = None
        if po_number:
            for pid, po in self.purchase_orders.items():
                if po.get("po_number") == po_number:
                    po_id = pid
                    break
        self.document_events.append({
            "id": str(uuid.uuid4()),
            "po_id": po_id,
            "po_number": po_number,
            "event_type": event_type,
            "event_source": "user",
            "actor": "system",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

    def get_timeline_for_po(self, po_id: str) -> List[Dict]:
        events = [e for e in self.document_events if e.get("po_id") == po_id]
        return sorted(events, key=lambda x: x.get("created_at", ""))

    def get_all_events(self) -> List[Dict]:
        return sorted(self.document_events, key=lambda x: x.get("created_at", ""), reverse=True)

    # -- Lifecycle / Archive -----------------------------------------------

    def update_status(self, entity_type: str, entity_id: str, new_status: str):
        store_map = {
            "po": self.purchase_orders,
            "slip": self.packing_slips,
            "invoice": self.invoices,
        }
        store = store_map.get(entity_type)
        if store and entity_id in store:
            old_status = store[entity_id].get("status")
            store[entity_id]["status"] = new_status
            if new_status == "verified":
                store[entity_id]["verified_at"] = datetime.now(timezone.utc).isoformat()
            if new_status == "archived":
                store[entity_id]["archived_at"] = datetime.now(timezone.utc).isoformat()

    def get_archive_candidates(self, days: int = 30) -> List[Dict]:
        """Return POs in 'verified' status older than `days` days."""
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
        candidates = []
        for po in self.purchase_orders.values():
            if po.get("status") == "verified":
                verified = po.get("verified_at", "")
                if verified:
                    try:
                        vt = datetime.fromisoformat(verified.replace("Z", "+00:00")).timestamp()
                        if vt < cutoff:
                            candidates.append(po)
                    except (ValueError, TypeError):
                        pass
        return candidates

    def batch_archive(self, po_ids: List[str]) -> int:
        count = 0
        for po_id in po_ids:
            if po_id in self.purchase_orders:
                self.update_status("po", po_id, "archived")
                count += 1
        return count


# ---------------------------------------------------------------------------
# Global store instance
# ---------------------------------------------------------------------------

_db: Optional[InMemoryStore] = None

def get_db() -> InMemoryStore:
    """Return the database store. Creates it on first call."""
    global _db
    if _db is None:
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            # Future: initialize asyncpg pool here
            # For now, fall back to in-memory
            print("[VerifyAP] DATABASE_URL set but PostgreSQL driver not yet integrated. Using in-memory store.")
        else:
            print("[VerifyAP] No DATABASE_URL. Using in-memory store (data will not persist across restarts).")
        _db = InMemoryStore()
    return _db
