from __future__ import annotations

import unittest

from autoapply.contracts import RenderBullet, RenderModel, RenderSectionEntry
from autoapply.generation_format_contract import (
    GENERATED_RESUME_FORMAT_BASELINE,
    GENERATED_RESUME_FORMAT_CONTRACT_VERSION,
    collect_contract_violations,
    ordered_output_sections,
    output_section_order,
)
from tests.fixtures import sample_job_posting, sample_user_profile
from autoapply.tailoring import TailoringEngine


class GenerationFormatContractTests(unittest.TestCase):
    def test_contract_constants_are_versioned_and_baseline_anchored(self) -> None:
        self.assertEqual(GENERATED_RESUME_FORMAT_CONTRACT_VERSION, "resume_format.v1")
        self.assertEqual(GENERATED_RESUME_FORMAT_BASELINE, "artifacts/resume_samples/Redacted Resume.pdf")
        self.assertEqual(output_section_order(), ("education", "experience", "projects", "skills"))

    def test_tailored_model_conforms_to_contract(self) -> None:
        model = TailoringEngine().build_render_model(sample_user_profile(), sample_job_posting())
        self.assertEqual(collect_contract_violations(model), [])
        self.assertEqual(ordered_output_sections(model), ["education", "experience", "projects", "skills"])

    def test_contract_rejects_unsupported_or_out_of_order_sections(self) -> None:
        bad_model = RenderModel(
            headline="Taylor Dev",
            summary="",
            selected_experience_ids=[],
            selected_project_ids=[],
            selected_skill_keywords=["Python"],
            sections={
                "projects": [
                    RenderSectionEntry(
                        entry_id="proj-1",
                        bullets=[RenderBullet(id="project:proj-1:0", text="Built feature")],
                    )
                ],
                "experience": [
                    RenderSectionEntry(
                        entry_id="exp-1",
                        bullets=[RenderBullet(id="experience:exp-1:0", text="Built service")],
                    )
                ],
                "awards": [
                    RenderSectionEntry(
                        entry_id="award-1",
                        bullets=[RenderBullet(id="award:1:0", text="Won prize")],
                    )
                ],
            },
        )

        errors = collect_contract_violations(bad_model)
        self.assertTrue(any("unsupported section keys" in error for error in errors))
        self.assertTrue(any("section order must follow contract order" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
