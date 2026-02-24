from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class SearchConfig:
    query: str
    area: str = "1"
    per_page: int = 30
    pages: int = 2


@dataclass
class CandidateProfile:
    name: str
    target_role: str
    skills: List[str]
    core_experience: List[str]
    base_resume_path: Path


@dataclass
class RunConfig:
    search: SearchConfig
    profile: CandidateProfile
    min_score: float = 0.25
    max_targets: int = 10
    output_dir: Path = field(default_factory=lambda: Path("output"))
