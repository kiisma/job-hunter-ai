from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Set

from .vacancies import Vacancy

TOKEN_RE = re.compile(r"[a-zA-Zа-яА-Я0-9+#.]{2,}")


@dataclass
class MatchResult:
    vacancy: Vacancy
    score: float
    matched_keywords: List[str]


def tokenize(text: str) -> Set[str]:
    return {t.lower() for t in TOKEN_RE.findall(text)}


def rank_vacancies(vacancies: Sequence[Vacancy], profile_keywords: Iterable[str]) -> List[MatchResult]:
    profile_tokens = {x.lower() for x in profile_keywords}
    scored: List[MatchResult] = []

    for vacancy in vacancies:
        vacancy_tokens = tokenize(
            " ".join([vacancy.name, vacancy.description, " ".join(vacancy.key_skills)])
        )
        if not vacancy_tokens:
            continue
        overlap = sorted(profile_tokens.intersection(vacancy_tokens))
        score = len(overlap) / max(len(profile_tokens), 1)
        scored.append(MatchResult(vacancy=vacancy, score=score, matched_keywords=overlap))

    return sorted(scored, key=lambda x: x.score, reverse=True)
