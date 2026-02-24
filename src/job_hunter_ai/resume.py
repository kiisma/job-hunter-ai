from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Iterable

from .vacancies import Vacancy


def read_base_resume(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def tailor_resume(base_resume: str, vacancy: Vacancy, matched_keywords: Iterable[str]) -> str:
    kws = ", ".join(matched_keywords) if matched_keywords else "релевантные технологии"
    addition = dedent(
        f"""

        ---
        ## Адаптация под вакансию: {vacancy.name}
        **Компания:** {vacancy.employer}
        **Почему подхожу:**
        - Практический опыт по направлениям: {kws}.
        - Быстро встраиваюсь в процессы и беру ownership за результат.
        - Умею переводить бизнес-задачи в технические решения.
        """
    ).strip()
    return f"{base_resume.strip()}\n\n{addition}\n"


def build_cover_letter(candidate_name: str, vacancy: Vacancy, matched_keywords: Iterable[str]) -> str:
    kws = ", ".join(matched_keywords) if matched_keywords else "ключевым требованиям роли"
    return dedent(
        f"""
        Здравствуйте!

        Меня зовут {candidate_name}. Хочу откликнуться на позицию "{vacancy.name}" в {vacancy.employer}.

        По описанию вакансии вижу хорошее совпадение по навыкам: {kws}. 
        Буду полезен(а) в задачах разработки, оптимизации и доставки фич до production.

        Готов(а) выполнить тестовое задание и обсудить, как смогу усилить команду.

        С уважением,
        {candidate_name}
        """
    ).strip()
