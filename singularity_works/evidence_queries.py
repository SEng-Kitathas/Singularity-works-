from __future__ import annotations

from typing import Any


def matches(record: dict[str, Any], **criteria: Any) -> bool:
        payload = record.get("payload", {})
        for key, value in criteria.items():
            if record.get(key) != value and payload.get(key) != value:
                return False
        return True

def filter_records(ledger, **criteria: Any) -> list[dict[str, Any]]:
        return [r for r in ledger.load_all() if matches(r, **criteria)]

def session_records(ledger, session_id: str | None) -> list[dict[str, Any]]:
        records = ledger.load_all()
        if not session_id:
            return records
        return [r for r in records if session_id in str(r.get("record_id", ""))]

