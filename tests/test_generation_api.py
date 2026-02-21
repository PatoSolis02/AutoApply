from __future__ import annotations

import unittest

from autoapply import api as api_module
from autoapply.contracts import GenerateResumeRequest, GenerateResumeResult
from autoapply.repositories import NotFoundError
from autoapply.service import GenerationOutcome


class GenerationApiHandlerTests(unittest.TestCase):
    def test_handler_returns_201_payload(self) -> None:
        class _Service:
            def generate_resume_version(self, application_id: str, request: GenerateResumeRequest):
                self.application_id = application_id
                self.request = request
                return GenerationOutcome(
                    status_code=201,
                    result=GenerateResumeResult(
                        resume_version_id="ver-1",
                        warnings=["profile summary is empty"],
                        blocked_reasons=[],
                    ),
                )

        service = _Service()
        payload = api_module.handle_generate_resume_version(
            service,
            "app-1",
            GenerateResumeRequest(template_id="modern"),
        )

        self.assertEqual(service.application_id, "app-1")
        self.assertEqual(service.request.template_id, "modern")
        self.assertEqual(
            payload,
            {
                "resume_version_id": "ver-1",
                "warnings": ["profile summary is empty"],
                "blocked_reasons": [],
            },
        )

    def test_handler_translates_not_found_to_404(self) -> None:
        class _Service:
            def generate_resume_version(self, application_id: str, request: GenerateResumeRequest):
                raise NotFoundError(f"application '{application_id}' not found")

        with self.assertRaises(api_module.ApiError) as ctx:
            api_module.handle_generate_resume_version(
                _Service(),
                "missing-app",
                GenerateResumeRequest(template_id="modern"),
            )

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "application 'missing-app' not found")

    def test_handler_translates_compliance_to_422(self) -> None:
        class _Service:
            def generate_resume_version(self, application_id: str, request: GenerateResumeRequest):
                return GenerationOutcome(
                    status_code=422,
                    result=GenerateResumeResult(
                        resume_version_id="",
                        warnings=[],
                        blocked_reasons=["unsupported claims detected"],
                    ),
                )

        with self.assertRaises(api_module.ApiError) as ctx:
            api_module.handle_generate_resume_version(
                _Service(),
                "app-1",
                GenerateResumeRequest(template_id="modern"),
            )

        self.assertEqual(ctx.exception.status_code, 422)
        self.assertEqual(
            ctx.exception.detail,
            {
                "warnings": [],
                "blocked_reasons": ["unsupported claims detected"],
            },
        )


if __name__ == "__main__":
    unittest.main()
