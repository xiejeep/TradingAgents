import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class HistoryIndex:
    def __init__(self, results_dir: str):
        self.index_path = Path(results_dir) / "analysis_index.json"
        self._ensure_index()

    def _ensure_index(self):
        if not self.index_path.exists():
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self._write({"analyses": []})

    def _read(self) -> dict:
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"analyses": []}

    def _write(self, data: dict):
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def add_entry(
        self,
        ticker: str,
        analysis_date: str,
        decision: str,
        rating: Optional[str] = None,
        report_path: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> str:
        entry_id = datetime.now().strftime("%Y%m%d%H%M%S%f")[:16]
        data = self._read()
        entry = {
            "id": entry_id,
            "ticker": ticker,
            "analysis_date": analysis_date,
            "completed_at": datetime.now().isoformat(),
            "decision": decision,
            "rating": rating,
            "report_path": report_path,
        }
        data["analyses"].append(entry)
        self._write(data)
        return entry_id

    def list_entries(
        self,
        ticker: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        data = self._read()
        entries = data.get("analyses", [])
        if ticker:
            ticker_upper = ticker.upper()
            entries = [e for e in entries if e.get("ticker", "").upper() == ticker_upper]
        entries = sorted(entries, key=lambda e: e.get("completed_at", ""), reverse=True)
        return entries[offset:offset + limit]

    def get_entry(self, entry_id: str) -> Optional[dict]:
        data = self._read()
        for entry in data.get("analyses", []):
            if entry.get("id") == entry_id:
                return entry
        return None

    def total_count(self, ticker: Optional[str] = None) -> int:
        data = self._read()
        entries = data.get("analyses", [])
        if ticker:
            ticker_upper = ticker.upper()
            entries = [e for e in entries if e.get("ticker", "").upper() == ticker_upper]
        return len(entries)


def get_history_index(results_dir: str) -> HistoryIndex:
    return HistoryIndex(results_dir)
