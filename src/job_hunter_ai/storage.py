from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .models import ApplicationRecord, JobPosting, TailoredApplication


class ApplicationStore:
    """Simple local store to avoid duplicate applications."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict:
        if not self.db_path.exists():
            return {"records": []}
        return json.loads(self.db_path.read_text(encoding="utf-8"))

    def _write(self, payload: dict) -> None:
        self.db_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def contains_job(self, source: str, job_id: str) -> bool:
        payload = self._read()
        key = f"{source}:{job_id}"
        return any(item.get("key") == key for item in payload.get("records", []))

    def save(self, record: ApplicationRecord) -> None:
        payload = self._read()
        key = f"{record.job.source}:{record.job.id}"
        payload.setdefault("records", []).append(
            {
                "key": key,
                "created_at": record.created_at.astimezone(timezone.utc).isoformat(),
                "status": record.status,
                "job": asdict(record.job),
                "application": asdict(record.application),
            }
        )
        self._write(payload)

    def make_record(self, job: JobPosting, app: TailoredApplication) -> ApplicationRecord:
        return ApplicationRecord(job=job, application=app, created_at=datetime.now(timezone.utc))
