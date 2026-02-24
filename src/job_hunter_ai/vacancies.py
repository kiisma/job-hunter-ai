from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class Vacancy:
    id: str
    name: str
    employer: str
    alternate_url: str
    description: str
    key_skills: List[str]


class HHVacancyClient:
    """Simple client for hh.ru public vacancies API."""

    BASE_URL = "https://api.hh.ru"

    def __init__(self, user_agent: str = "job-hunter-ai/0.1") -> None:
        self.user_agent = user_agent

    def _get_json(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        query = f"?{urlencode(params)}" if params else ""
        request = Request(f"{url}{query}", headers={"User-Agent": self.user_agent})
        try:
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError):
            return None

    def search(self, text: str, area: str, per_page: int, pages: int) -> List[dict]:
        items: List[dict] = []
        for page in range(pages):
            payload = self._get_json(
                f"{self.BASE_URL}/vacancies",
                params={"text": text, "area": area, "per_page": per_page, "page": page},
            )
            if not payload:
                continue
            items.extend(payload.get("items", []))
        return items

    def load_details(self, vacancy_id: str) -> Optional[Vacancy]:
        data = self._get_json(f"{self.BASE_URL}/vacancies/{vacancy_id}")
        if not data:
            return None
        return Vacancy(
            id=str(data.get("id", "")),
            name=data.get("name", ""),
            employer=(data.get("employer") or {}).get("name", ""),
            alternate_url=data.get("alternate_url", ""),
            description=data.get("description", ""),
            key_skills=[s.get("name", "") for s in (data.get("key_skills") or []) if s.get("name")],
        )
