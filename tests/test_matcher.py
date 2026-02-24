import unittest

from job_hunter_ai.matcher import rank_vacancies
from job_hunter_ai.vacancies import Vacancy


class MatcherTests(unittest.TestCase):
    def test_rank_vacancies_orders_by_score(self) -> None:
        v1 = Vacancy(
            id="1",
            name="Python Developer",
            employer="A",
            alternate_url="http://example.com/1",
            description="FastAPI and PostgreSQL",
            key_skills=["Python", "FastAPI"],
        )
        v2 = Vacancy(
            id="2",
            name="Java Developer",
            employer="B",
            alternate_url="http://example.com/2",
            description="Spring",
            key_skills=["Java"],
        )

        ranked = rank_vacancies([v2, v1], ["python", "fastapi", "postgresql"])
        self.assertEqual(ranked[0].vacancy.id, "1")
        self.assertGreater(ranked[0].score, ranked[1].score)


if __name__ == "__main__":
    unittest.main()
