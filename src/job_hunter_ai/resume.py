from __future__ import annotations

import re
from collections import Counter

from .models import JobPosting, TailoredApplication

WORD_RE = re.compile(r"[A-Za-zА-Яа-я0-9+#.-]{3,}")


def extract_keywords(text: str, top_k: int = 20) -> list[str]:
    words = [w.lower() for w in WORD_RE.findall(text)]
    stop = {
        "with", "that", "this", "from", "will", "have", "your", "you",
        "для", "как", "или", "это", "the", "and", "are", "our", "job",
    }
    counts = Counter(w for w in words if w not in stop)
    return [w for w, _ in counts.most_common(top_k)]


def tailor_resume(base_resume: str, job: JobPosting) -> TailoredApplication:
    job_keywords = extract_keywords(f"{job.description} {job.title}", top_k=14)
    resume_keywords = set(extract_keywords(base_resume, top_k=80))
    overlap = [kw for kw in job_keywords if kw in resume_keywords]
    missing = [kw for kw in job_keywords if kw not in resume_keywords][:6]
    score = len(overlap) / max(len(job_keywords), 1)

    tailored_resume = (
        f"# Tailored Resume for {job.title} @ {job.company}\n\n"
        f"## Target Role\n{job.title}\n\n"
        f"## Direct Match Keywords\n- " + "\n- ".join(overlap or ["Update project bullets to include required stack"]) +
        "\n\n## High-impact gaps to address\n- " + "\n- ".join(missing or ["No critical gaps detected"]) +
        "\n\n## Base Resume\n" + base_resume.strip()
    )

    cover_letter = (
        f"Здравствуйте, команда {job.company}!\n\n"
        f"Откликаюсь на позицию {job.title}."
        f" У меня есть релевантный опыт по: {', '.join(overlap[:8]) or 'backend-разработка, доставка фич, коммуникация с продуктом'}.\n"
        f"В первую неделю сфокусируюсь на закрытии пробелов: {', '.join(missing) if missing else 'критичных пробелов не вижу'}.\n\n"
        "Готов(а) быстро пройти интервью и выполнить тестовое задание."
    )

    return TailoredApplication(
        job_id=job.id,
        tailored_resume=tailored_resume,
        cover_letter=cover_letter,
        score=score,
        matched_keywords=overlap,
        missing_keywords=missing,
    )
