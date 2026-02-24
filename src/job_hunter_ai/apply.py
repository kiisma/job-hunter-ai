from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

from .models import JobPosting, TailoredApplication


def save_application(job: JobPosting, app: TailoredApplication, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = out_dir / f"{job.source}_{job.id}_{ts}.json"
    payload = {
        "job": job.__dict__,
        "tailored_resume": app.tailored_resume,
        "cover_letter": app.cover_letter,
        "score": app.score,
        "matched_keywords": app.matched_keywords,
        "missing_keywords": app.missing_keywords,
        "status": "prepared",
        "next_steps": [
            "Review tailored resume and adjust quantified achievements.",
            "Submit on job URL.",
            "Track response in your spreadsheet/CRM.",
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
