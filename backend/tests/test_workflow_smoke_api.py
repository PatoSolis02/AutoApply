from __future__ import annotations

import json
import threading
import unittest
from http.client import HTTPConnection
from typing import Any

from app.main import create_server


class TestWorkflowSmokeApi(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = self._create_tmpdir()
        self.db_path = self._tmpdir + "/workflow-smoke-test.db"
        self.server = create_server(db_path=self.db_path, host="127.0.0.1", port=0)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _create_tmpdir(self) -> str:
        import tempfile

        return tempfile.mkdtemp(prefix="workflow-smoke-api-tests-")

    def _request_json(self, method: str, path: str, payload: Any = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps(payload) if payload is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        body_text = response.read().decode("utf-8")
        conn.close()
        return response.status, json.loads(body_text)

    def _assert_stage(self, stage: str, expected_status: int, response: tuple[int, dict]) -> dict:
        status, body = response
        self.assertEqual(
            status,
            expected_status,
            msg=f"[stage={stage}] expected HTTP {expected_status}, got {status}. body={body}",
        )
        return body

    def _seed_profile(self) -> None:
        self._assert_stage(
            "profile",
            200,
            self._request_json(
                "PUT",
                "/api/v1/profile",
                {
                    "id": "primary",
                    "full_name": "Taylor Dev",
                    "headline": "Backend Engineer",
                    "summary": "Builds Python APIs.",
                    "skills": ["Python", "SQL"],
                    "experiences": [
                        {
                            "id": "exp-1",
                            "company": "Acme",
                            "title": "Engineer",
                            "start_date": "2024-01-01",
                            "end_date": None,
                            "bullets": ["Built API services with Python and SQL."],
                            "skills": ["Python", "SQL"],
                        }
                    ],
                    "projects": [],
                    "education": [],
                },
            ),
        )

    def _capture_application(self) -> str:
        body = self._assert_stage(
            "capture",
            201,
            self._request_json(
                "POST",
                "/api/v1/jobs/capture",
                {
                    "title": "Platform Engineer",
                    "company": "Nimbus",
                    "location": "Rochester, NY",
                    "job_url": "https://www.linkedin.com/jobs/view/123",
                    "description_raw": "Build API services with Python and SQL.",
                    "captured_at": "2026-02-21T10:00:00Z",
                },
            ),
        )
        return body["application_id"]

    def _set_drafting(self, application_id: str) -> None:
        body = self._assert_stage(
            "set-drafting",
            200,
            self._request_json(
                "PATCH",
                f"/api/v1/applications/{application_id}/status",
                {"target_status": "drafting"},
            ),
        )
        self.assertEqual(body["status"], "drafting", msg="[stage=set-drafting] application did not enter drafting")

    def _generate(self, application_id: str) -> str:
        body = self._assert_stage(
            "generate",
            201,
            self._request_json(
                "POST",
                f"/api/v1/applications/{application_id}/resume-versions/generate",
                {"template_id": "modern"},
            ),
        )
        resume_version_id = body.get("resume_version_id")
        self.assertTrue(resume_version_id, msg="[stage=generate] missing resume_version_id in response")
        return str(resume_version_id)

    def test_smoke_primary_flow_capture_generate_review_approve_audit(self) -> None:
        self._seed_profile()
        application_id = self._capture_application()
        self._set_drafting(application_id)
        resume_version_id = self._generate(application_id)

        review = self._assert_stage(
            "review",
            200,
            self._request_json("GET", f"/api/v1/resume-versions/{resume_version_id}"),
        )
        self.assertEqual(review["id"], resume_version_id, msg="[stage=review] wrong resume version returned")
        self.assertIn("change_log", review, msg="[stage=review] missing change_log")
        self.assertIn("claims_map", review, msg="[stage=review] missing claims_map")
        self.assertGreater(len(review["claims_map"]), 0, msg="[stage=review] claims_map should not be empty")

        approved = self._assert_stage(
            "approve",
            200,
            self._request_json("POST", f"/api/v1/resume-versions/{resume_version_id}/approve", {}),
        )
        self.assertTrue(approved["approval"]["approved"], msg="[stage=approve] approval flag was false")

        audit = self._assert_stage(
            "audit",
            200,
            self._request_json("GET", f"/api/v1/applications/{application_id}/audit-export"),
        )
        self.assertEqual(audit["application"]["id"], application_id, msg="[stage=audit] wrong application payload")
        self.assertEqual(
            audit["job_posting"]["application_id"],
            application_id,
            msg="[stage=audit] job posting application_id mismatch",
        )
        self.assertEqual(len(audit["resume_versions"]), 1, msg="[stage=audit] expected exactly one resume version")
        self.assertEqual(
            audit["resume_versions"][0]["id"],
            resume_version_id,
            msg="[stage=audit] wrong resume version in export",
        )
        self.assertIn("generated_at", audit, msg="[stage=audit] missing generated_at")

    def test_smoke_ready_to_apply_is_blocked_before_approve(self) -> None:
        self._seed_profile()
        application_id = self._capture_application()
        self._set_drafting(application_id)
        self._generate(application_id)

        status, body = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "ready_to_apply"},
        )
        self.assertEqual(
            status,
            422,
            msg=f"[stage=approve-gate] expected HTTP 422 before approval, got {status}. body={body}",
        )
        self.assertIn("approval gate failed", body["detail"], msg="[stage=approve-gate] unexpected error detail")


if __name__ == "__main__":
    unittest.main()
