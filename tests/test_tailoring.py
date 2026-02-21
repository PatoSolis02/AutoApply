from __future__ import annotations

import unittest

from autoapply.tailoring import TailoringEngine
from tests.fixtures import sample_job_posting, sample_user_profile


class TailoringEngineTests(unittest.TestCase):
    def test_selection_is_deterministic_for_same_inputs(self) -> None:
        engine = TailoringEngine()
        profile = sample_user_profile()
        posting = sample_job_posting()

        first = engine.build_render_model(profile, posting)
        second = engine.build_render_model(profile, posting)

        self.assertEqual(first, second)
        self.assertEqual(first.selected_experience_ids[0], "exp-1")
        self.assertEqual(first.selected_project_ids[0], "proj-1")

    def test_selected_bullets_are_profile_backed(self) -> None:
        engine = TailoringEngine()
        profile = sample_user_profile()
        posting = sample_job_posting()
        model = engine.build_render_model(profile, posting)

        source_bullets = set()
        for entry in profile.experiences:
            source_bullets.update(entry.bullets)
        for entry in profile.projects:
            source_bullets.update(entry.bullets)

        generated_bullets = {
            bullet.text
            for section_name in ("experience", "projects")
            for section in model.sections[section_name]
            for bullet in section.bullets
        }

        self.assertTrue(generated_bullets)
        self.assertTrue(generated_bullets.issubset(source_bullets))


if __name__ == "__main__":
    unittest.main()
