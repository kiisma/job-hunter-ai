from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List


@dataclass
class ApplicationDraft:
    vacancy_id: str
    vacancy_name: str
    employer: str
    vacancy_url: str
    score: float
    resume_path: str
    cover_letter_path: str


def save_application_queue(items: List[ApplicationDraft], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([asdict(item) for item in items], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
