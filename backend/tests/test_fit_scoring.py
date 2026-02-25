from __future__ import annotations

import unittest

from app.fit_scoring import FitScoringEngine


class FitScoringEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = FitScoringEngine()
        self.job_posting = {
            "structured_json": {
                "requirements": [
                    "3+ years Python",
                    "Experience with SQL databases",
                    "REST API design",
                ],
                "preferred_qualifications": [
                    "Experience with AWS",
                ],
                "tech_stack": ["Python", "SQL", "FastAPI"],
                "keywords": ["python", "sql", "aws", "observability"],
            }
        }
        self.profile = {
            "full_name": "Taylor Dev",
            "headline": "Backend Engineer",
            "summary": "Builds Python APIs and data systems.",
            "skills": ["Python", "SQL", "FastAPI", "Observability"],
            "experiences": [
                {
                    "company": "DataCo",
                    "title": "Software Engineer",
                    "bullets": [
                        "Built API services with Python and SQL.",
                        "Improved monitoring and observability.",
                    ],
                    "skills": ["Python", "SQL", "Monitoring"],
                }
            ],
            "projects": [],
            "education": [],
        }

    def test_evaluate_is_deterministic_for_repeated_inputs(self) -> None:
        first = self.engine.evaluate(profile=self.profile, job_posting=self.job_posting)
        second = self.engine.evaluate(profile=self.profile, job_posting=self.job_posting)

        self.assertEqual(first, second)
        self.assertIsInstance(first["score"], float)
        self.assertGreater(first["score"], 0.0)
        self.assertIn("REST API design", first["missing_requirements"])
        self.assertTrue(len(first["gaps"]) > 0)

    def test_evaluate_without_profile_returns_null_score_and_profile_gap(self) -> None:
        outcome = self.engine.evaluate(profile=None, job_posting=self.job_posting)

        self.assertIsNone(outcome["score"])
        self.assertEqual(outcome["gaps"][0]["category"], "profile")
        self.assertGreater(len(outcome["missing_requirements"]), 0)
        self.assertIn("Profile data is unavailable", outcome["notes"][0])


if __name__ == "__main__":
    unittest.main()
