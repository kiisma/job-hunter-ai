from __future__ import annotations

import json
from typing import Iterable
from urllib.error import URLError
from urllib.request import Request, urlopen

from .models import JobPosting


class BaseProvider:
    source: str = "unknown"

    def fetch(self, keywords: list[str], limit: int = 20) -> list[JobPosting]:
        raise NotImplementedError


class RemoteOKProvider(BaseProvider):
    source = "remoteok"
    endpoint = "https://remoteok.com/api"

    def fetch(self, keywords: list[str], limit: int = 20) -> list[JobPosting]:
        req = Request(self.endpoint, headers={"User-Agent": "job-hunter-ai/0.2"})
        with urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _parse_remoteok(payload, keywords, limit)


class RemotiveProvider(BaseProvider):
    source = "remotive"
    endpoint = "https://remotive.com/api/remote-jobs"

    def fetch(self, keywords: list[str], limit: int = 20) -> list[JobPosting]:
        req = Request(self.endpoint, headers={"User-Agent": "job-hunter-ai/0.2"})
        with urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _parse_remotive(payload.get("jobs", []), keywords, limit)


def _matches(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    blob = text.lower()
    return any(k.lower() in blob for k in keywords)


def _parse_remoteok(payload: list[dict], keywords: list[str], limit: int) -> list[JobPosting]:
    jobs: list[JobPosting] = []
    for item in payload:
        if not isinstance(item, dict) or "id" not in item:
            continue
        title = (item.get("position") or "").strip()
        company = (item.get("company") or "").strip()
        description = (item.get("description") or "").strip()
        if not _matches(f"{title} {company} {description}", keywords):
            continue
        jobs.append(
            JobPosting(
                id=str(item.get("id")),
                title=title,
                company=company,
                location=item.get("location") or "Remote",
                url=item.get("url") or item.get("apply_url") or "",
                description=description,
                salary=str(item.get("salary_min")) if item.get("salary_min") else None,
                source="remoteok",
                published_at=item.get("date"),
            )
        )
        if len(jobs) >= limit:
            break
    return jobs


def _parse_remotive(payload: list[dict], keywords: list[str], limit: int) -> list[JobPosting]:
    jobs: list[JobPosting] = []
    for item in payload:
        title = (item.get("title") or "").strip()
        company = (item.get("company_name") or "").strip()
        description = (item.get("description") or "").strip()
        if not _matches(f"{title} {company} {description}", keywords):
            continue
        jobs.append(
            JobPosting(
                id=str(item.get("id")),
                title=title,
                company=company,
                location=item.get("candidate_required_location") or "Remote",
                url=item.get("url") or "",
                description=description,
                salary=item.get("salary"),
                source="remotive",
                published_at=item.get("publication_date"),
            )
        )
        if len(jobs) >= limit:
            break
    return jobs


def fetch_from_providers(keywords: list[str], limit: int, providers: list[BaseProvider]) -> list[JobPosting]:
    per_provider = max(5, limit)
    all_jobs: list[JobPosting] = []
    seen: set[str] = set()

    for provider in providers:
        try:
            jobs = provider.fetch(keywords, limit=per_provider)
        except (URLError, TimeoutError, ValueError):
            continue
        for job in jobs:
            key = f"{job.source}:{job.id}"
            if key in seen:
                continue
            seen.add(key)
            all_jobs.append(job)
            if len(all_jobs) >= limit:
                return all_jobs
    return all_jobs


def rank_jobs(jobs: Iterable[JobPosting], keywords: list[str]) -> list[tuple[float, JobPosting]]:
    tokens = [k.lower() for k in keywords]
    ranked: list[tuple[float, JobPosting]] = []
    for job in jobs:
        text = f"{job.title} {job.company} {job.description}".lower()
        score = sum(text.count(t) for t in tokens)
        if "senior" in text:
            score += 0.3
        ranked.append((score, job))
    return sorted(ranked, key=lambda x: x[0], reverse=True)
