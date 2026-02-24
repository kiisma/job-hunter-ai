from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(slots=True)
class Settings:
    default_limit: int = int(os.getenv("JOB_LIMIT", "25"))
    store_path: Path = Path(os.getenv("JOB_STORE_PATH", ".job_hunter/store.json"))


settings = Settings()
