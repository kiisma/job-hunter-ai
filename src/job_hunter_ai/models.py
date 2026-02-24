from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class JobPosting:
    id: str
    title: str
    company: str
    location: str
    url: str
    description: str
    salary: str | None = None
    source: str = "unknown"
    published_at: str | None = None


@dataclass(slots=True)
class TailoredApplication:
    job_id: str
    tailored_resume: str
    cover_letter: str
    score: float
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ApplicationRecord:
    job: JobPosting
    application: TailoredApplication
    created_at: datetime
    status: str = "prepared"
