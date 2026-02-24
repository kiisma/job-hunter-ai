from __future__ import annotations

from pathlib import Path
from typing import List

from .config import RunConfig
from .matcher import rank_vacancies
from .responder import ApplicationDraft, save_application_queue
from .resume import build_cover_letter, read_base_resume, tailor_resume
from .vacancies import HHVacancyClient, Vacancy


class JobHunterWorkflow:
    def __init__(self, config: RunConfig) -> None:
        self.config = config
        self.client = HHVacancyClient()

    def _fetch_vacancies(self) -> List[Vacancy]:
        raw_items = self.client.search(
            text=self.config.search.query,
            area=self.config.search.area,
            per_page=self.config.search.per_page,
            pages=self.config.search.pages,
        )
        vacancies: List[Vacancy] = []
        for item in raw_items:
            vacancy_id = str(item.get("id", ""))
            if not vacancy_id:
                continue
            details = self.client.load_details(vacancy_id)
            if details:
                vacancies.append(details)
        return vacancies

    def run(self) -> List[ApplicationDraft]:
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        base_resume = read_base_resume(self.config.profile.base_resume_path)
        profile_keywords = [*self.config.profile.skills, *self.config.profile.core_experience]

        ranked = rank_vacancies(self._fetch_vacancies(), profile_keywords)

        selected = [r for r in ranked if r.score >= self.config.min_score][: self.config.max_targets]
        queue: List[ApplicationDraft] = []

        for index, item in enumerate(selected, start=1):
            target_dir = self.config.output_dir / f"{index:02d}_{item.vacancy.id}"
            target_dir.mkdir(parents=True, exist_ok=True)

            tailored_resume = tailor_resume(base_resume, item.vacancy, item.matched_keywords)
            cover_letter = build_cover_letter(
                candidate_name=self.config.profile.name,
                vacancy=item.vacancy,
                matched_keywords=item.matched_keywords,
            )

            resume_path = target_dir / "resume.md"
            letter_path = target_dir / "cover_letter.txt"
            resume_path.write_text(tailored_resume, encoding="utf-8")
            letter_path.write_text(cover_letter, encoding="utf-8")

            queue.append(
                ApplicationDraft(
                    vacancy_id=item.vacancy.id,
                    vacancy_name=item.vacancy.name,
                    employer=item.vacancy.employer,
                    vacancy_url=item.vacancy.alternate_url,
                    score=round(item.score, 3),
                    resume_path=str(resume_path),
                    cover_letter_path=str(letter_path),
                )
            )

        save_application_queue(queue, self.config.output_dir / "application_queue.json")
        return queue
