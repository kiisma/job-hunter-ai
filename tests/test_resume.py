from pathlib import Path

from job_hunter_ai.models import JobPosting
from job_hunter_ai.resume import extract_keywords, tailor_resume
from job_hunter_ai.storage import ApplicationStore


def test_extract_keywords_nonempty():
    text = "Python backend developer with FastAPI and PostgreSQL"
    kws = extract_keywords(text)
    assert "python" in kws
    assert "backend" in kws


def test_tailor_resume_score_and_keywords():
    resume = "Python developer. Built APIs with FastAPI and Docker."
    job = JobPosting(
        id="1",
        title="Backend Python Engineer",
        company="Acme",
        location="Remote",
        url="https://example.com",
        description="Need python fastapi docker skills",
    )
    tailored = tailor_resume(resume, job)
    assert 0 <= tailored.score <= 1
    assert "Tailored Resume" in tailored.tailored_resume
    assert "Здравствуйте" in tailored.cover_letter
    assert "python" in tailored.matched_keywords


def test_store_dedup(tmp_path: Path):
    store = ApplicationStore(tmp_path / "store.json")
    job = JobPosting(
        id="42",
        title="Python Engineer",
        company="ACME",
        location="Remote",
        url="https://example.com",
        description="python",
        source="remoteok",
    )
    app = tailor_resume("python", job)
    store.save(store.make_record(job, app))
    assert store.contains_job("remoteok", "42") is True
