from __future__ import annotations

import json
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from typing import Any

from app.db import CaptureDatabase
from app.main import create_server


class TrackingApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = self._create_tmpdir()
        self.db_path = self._tmpdir + "/tracking-test.db"
        self.server = create_server(db_path=self.db_path, host="127.0.0.1", port=0)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.db = CaptureDatabase(self.db_path)

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _create_tmpdir(self) -> str:
        import tempfile

        return tempfile.mkdtemp(prefix="tracking-api-tests-")

    def _request_json(self, method: str, path: str, payload: Any = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps(payload) if payload is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        body_text = response.read().decode("utf-8")
        conn.close()
        return response.status, json.loads(body_text)

    def _capture_application(
        self,
        *,
        company: str = "Acme",
        title: str = "Backend Engineer",
        description_raw: str = "Build API services with Python and SQL.",
    ) -> str:
        status, body = self._request_json(
            "POST",
            "/api/v1/jobs/capture",
            {
                "title": title,
                "company": company,
                "location": "Rochester, NY",
                "job_url": "https://www.linkedin.com/jobs/view/123",
                "description_raw": description_raw,
                "captured_at": "2026-02-21T10:00:00Z",
            },
        )
        self.assertEqual(status, 201)
        return body["application_id"]

    def _seed_resume_versions(self, application_id: str, *, total: int) -> list[str]:
        ids: list[str] = []
        base_time = datetime(2026, 2, 21, 10, 0, tzinfo=timezone.utc)
        for index in range(total):
            version_id = self.db.insert_resume_version(
                application_id=application_id,
                template_id="modern",
                render_model_json={},
                change_log={"added": [], "removed": [], "reworded": []},
                claims_map=[],
                created_at=(base_time + timedelta(minutes=index)).isoformat(),
            )
            ids.append(version_id)
        return ids

    def test_get_applications_returns_paginated_items(self) -> None:
        self._capture_application(company="Acme")
        self._capture_application(company="Beta")

        status, body = self._request_json("GET", "/api/v1/applications?page=1&page_size=1")
        self.assertEqual(status, 200)
        self.assertEqual(body["page"], 1)
        self.assertEqual(body["page_size"], 1)
        self.assertEqual(body["total"], 2)
        self.assertEqual(len(body["items"]), 1)

        status, body = self._request_json("GET", "/api/v1/applications?company=Acme")
        self.assertEqual(status, 200)
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["company"], "Acme")

    def test_get_application_returns_latest_resume_version(self) -> None:
        application_id = self._capture_application()
        first_id = self.db.insert_resume_version(
            application_id=application_id,
            template_id="modern",
            render_model_json={},
            change_log={"added": [], "removed": [], "reworded": []},
            claims_map=[],
            created_at="2026-02-21T10:00:00+00:00",
        )
        second_id = self.db.insert_resume_version(
            application_id=application_id,
            template_id="classic",
            render_model_json={},
            change_log={"added": [], "removed": [], "reworded": []},
            claims_map=[],
            created_at="2026-02-21T11:00:00+00:00",
        )

        status, body = self._request_json("GET", f"/api/v1/applications/{application_id}")
        self.assertEqual(status, 200)
        self.assertEqual(body["id"], application_id)
        self.assertEqual(body["latest_resume_version"]["id"], second_id)
        self.assertNotEqual(first_id, second_id)

    def test_get_application_includes_deterministic_fit_analysis(self) -> None:
        application_id = self._capture_application(
            description_raw=(
                "Senior Backend Engineer role.\n"
                "Requirements: 5+ years Python.\n"
                "Requirements: Experience with SQL databases.\n"
                "Requirements: REST API design.\n"
                "Preferred: Experience with AWS.\n"
                "Responsibilities: Build API services.\n"
            )
        )

        status, _ = self._request_json(
            "PUT",
            "/api/v1/profile",
            {
                "id": "primary",
                "full_name": "Taylor Dev",
                "headline": "Backend Engineer",
                "summary": "Builds API systems with Python and SQL.",
                "skills": ["Python", "SQL", "FastAPI", "Observability"],
                "experiences": [
                    {
                        "id": "exp-1",
                        "company": "DataCo",
                        "title": "Engineer",
                        "bullets": ["Built API services with Python and SQL."],
                        "skills": ["Python", "SQL"],
                    }
                ],
                "projects": [],
                "education": [],
            },
        )
        self.assertEqual(status, 200)

        first_status, first = self._request_json("GET", f"/api/v1/applications/{application_id}")
        second_status, second = self._request_json("GET", f"/api/v1/applications/{application_id}")
        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 200)

        self.assertIsInstance(first["fit_score"], float)
        self.assertEqual(first["fit_analysis"], second["fit_analysis"])
        self.assertEqual(first["fit_score"], second["fit_score"])
        self.assertIn("missing_requirements", first["fit_analysis"])
        self.assertGreater(len(first["fit_analysis"]["gaps"]), 0)

    def test_get_application_fit_analysis_reports_profile_gap_when_profile_missing(self) -> None:
        application_id = self._capture_application(
            description_raw=(
                "Backend role.\n"
                "Requirements: Experience with SQL databases.\n"
                "Requirements: REST API design.\n"
            )
        )

        status, body = self._request_json("GET", f"/api/v1/applications/{application_id}")
        self.assertEqual(status, 200)
        self.assertIsNone(body["fit_score"])
        self.assertIsNone(body["fit_analysis"]["score"])
        self.assertEqual(body["fit_analysis"]["gaps"][0]["category"], "profile")

    def test_patch_status_enforces_transition_and_approval_gate(self) -> None:
        application_id = self._capture_application()

        status, body = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "ready_to_apply"},
        )
        self.assertEqual(status, 409)
        self.assertIn("invalid transition", body["detail"])

        status, _ = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "drafting"},
        )
        self.assertEqual(status, 200)

        self.db.insert_resume_version(
            application_id=application_id,
            template_id="modern",
            render_model_json={},
            change_log={"added": [], "removed": [], "reworded": []},
            claims_map=[],
            approval_approved=False,
        )
        status, body = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "ready_to_apply"},
        )
        self.assertEqual(status, 422)
        self.assertIn("approval gate failed", body["detail"])

        self.db.insert_resume_version(
            application_id=application_id,
            template_id="modern",
            render_model_json={},
            change_log={"added": [], "removed": [], "reworded": []},
            claims_map=[],
            approval_approved=True,
            approval_approved_at="2026-02-21T11:00:00+00:00",
        )
        status, body = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "ready_to_apply"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ready_to_apply")

    def test_get_resume_versions_and_detail(self) -> None:
        application_id = self._capture_application()
        resume_version_id = self.db.insert_resume_version(
            application_id=application_id,
            template_id="modern",
            render_model_json={
                "headline": "Backend Engineer",
                "summary": "Builds APIs",
                "selected_experience_ids": [],
                "selected_project_ids": [],
                "selected_skill_keywords": [],
                "sections": {"experience": [], "projects": []},
            },
            change_log={"added": ["Built APIs"], "removed": [], "reworded": []},
            claims_map=[
                {
                    "bullet_id": "b-1",
                    "bullet_text": "Built APIs",
                    "source_type": "experience",
                    "source_id": "exp-1",
                    "evidence_text": "Built APIs",
                    "verification_status": "supported",
                }
            ],
        )

        status, body = self._request_json("GET", f"/api/v1/applications/{application_id}/resume-versions")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["items"]), 1)
        self.assertEqual(body["items"][0]["id"], resume_version_id)

        status, body = self._request_json("GET", f"/api/v1/resume-versions/{resume_version_id}")
        self.assertEqual(status, 200)
        self.assertEqual(body["id"], resume_version_id)
        self.assertIn("change_log", body)
        self.assertIn("claims_map", body)

    def test_approve_resume_version_sets_ready_to_apply(self) -> None:
        application_id = self._capture_application()
        status, _ = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "drafting"},
        )
        self.assertEqual(status, 200)

        resume_version_id = self.db.insert_resume_version(
            application_id=application_id,
            template_id="modern",
            render_model_json={},
            change_log={"added": [], "removed": [], "reworded": []},
            claims_map=[],
        )

        status, body = self._request_json("POST", f"/api/v1/resume-versions/{resume_version_id}/approve", {})
        self.assertEqual(status, 200)
        self.assertTrue(body["approval"]["approved"])
        self.assertIsNotNone(body["approval"]["approved_at"])

        status, body = self._request_json("GET", f"/api/v1/applications/{application_id}")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ready_to_apply")

    def test_status_patch_idempotent_for_same_target(self) -> None:
        application_id = self._capture_application()
        status, body = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "drafting"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "drafting")

        status, body = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "drafting"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "drafting")
        self.assertEqual(body["application"]["status"], "drafting")

    def test_ready_to_apply_requires_latest_approved_resume_version(self) -> None:
        application_id = self._capture_application()
        status, _ = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "drafting"},
        )
        self.assertEqual(status, 200)

        self.db.insert_resume_version(
            application_id=application_id,
            template_id="modern",
            render_model_json={},
            change_log={"added": [], "removed": [], "reworded": []},
            claims_map=[],
            approval_approved=True,
            approval_approved_at="2026-02-21T10:00:00+00:00",
            created_at="2026-02-21T10:00:00+00:00",
        )
        latest_version_id = self.db.insert_resume_version(
            application_id=application_id,
            template_id="modern",
            render_model_json={},
            change_log={"added": [], "removed": [], "reworded": []},
            claims_map=[],
            approval_approved=False,
            created_at="2026-02-21T11:00:00+00:00",
        )

        status, blocked = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "ready_to_apply"},
        )
        self.assertEqual(status, 422)
        self.assertIn("approval gate failed", blocked["detail"])

        status, approved = self._request_json("POST", f"/api/v1/resume-versions/{latest_version_id}/approve", {})
        self.assertEqual(status, 200)
        self.assertTrue(approved["approval"]["approved"])

        status, body = self._request_json("GET", f"/api/v1/applications/{application_id}")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ready_to_apply")

    def test_approve_resume_version_is_idempotent(self) -> None:
        application_id = self._capture_application()
        status, _ = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            {"target_status": "drafting"},
        )
        self.assertEqual(status, 200)

        resume_version_id = self.db.insert_resume_version(
            application_id=application_id,
            template_id="modern",
            render_model_json={},
            change_log={"added": [], "removed": [], "reworded": []},
            claims_map=[],
        )

        status, first = self._request_json("POST", f"/api/v1/resume-versions/{resume_version_id}/approve", {})
        self.assertEqual(status, 200)
        first_approved_at = first["approval"]["approved_at"]
        self.assertIsNotNone(first_approved_at)

        status, second = self._request_json("POST", f"/api/v1/resume-versions/{resume_version_id}/approve", {})
        self.assertEqual(status, 200)
        self.assertTrue(second["approval"]["approved"])
        self.assertEqual(second["approval"]["approved_at"], first_approved_at)

        status, body = self._request_json("GET", f"/api/v1/applications/{application_id}")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ready_to_apply")

    def test_audit_export_large_history_applies_default_limit(self) -> None:
        application_id = self._capture_application()
        version_ids = self._seed_resume_versions(application_id, total=620)

        status, body = self._request_json("GET", f"/api/v1/applications/{application_id}/audit-export")
        self.assertEqual(status, 200)

        page = body["resume_versions_page"]
        returned = len(body["resume_versions"])
        self.assertEqual(page["offset"], 0)
        self.assertEqual(page["total"], 620)
        self.assertEqual(page["returned"], returned)
        self.assertEqual(page["limit"], returned)
        self.assertTrue(page["has_more"])
        self.assertEqual(body["resume_versions"][0]["id"], version_ids[0])
        self.assertEqual(body["resume_versions"][-1]["id"], version_ids[returned - 1])
        self.assertEqual(
            page["limit"],
            body["export_limits"]["default_resume_versions_limit"],
        )

    def test_audit_export_supports_explicit_limit_and_offset(self) -> None:
        application_id = self._capture_application()
        version_ids = self._seed_resume_versions(application_id, total=320)

        status, body = self._request_json(
            "GET",
            f"/api/v1/applications/{application_id}/audit-export?resume_versions_limit=120&resume_versions_offset=150",
        )
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in body["resume_versions"]], version_ids[150:270])
        self.assertEqual(body["resume_versions_page"]["limit"], 120)
        self.assertEqual(body["resume_versions_page"]["offset"], 150)
        self.assertEqual(body["resume_versions_page"]["returned"], 120)
        self.assertEqual(body["resume_versions_page"]["total"], 320)
        self.assertTrue(body["resume_versions_page"]["has_more"])

        status, body = self._request_json(
            "GET",
            f"/api/v1/applications/{application_id}/audit-export?resume_versions_limit=120&resume_versions_offset=300",
        )
        self.assertEqual(status, 200)
        self.assertEqual([item["id"] for item in body["resume_versions"]], version_ids[300:320])
        self.assertEqual(body["resume_versions_page"]["returned"], 20)
        self.assertFalse(body["resume_versions_page"]["has_more"])

    def test_audit_export_rejects_invalid_limit_parameters(self) -> None:
        application_id = self._capture_application()

        status, body = self._request_json(
            "GET",
            f"/api/v1/applications/{application_id}/audit-export?resume_versions_limit=0",
        )
        self.assertEqual(status, 400)
        self.assertIn("resume_versions_limit must be a positive integer", body["detail"])

        status, body = self._request_json(
            "GET",
            f"/api/v1/applications/{application_id}/audit-export?resume_versions_limit=oops",
        )
        self.assertEqual(status, 400)
        self.assertIn("resume_versions_limit must be a positive integer", body["detail"])

        status, body = self._request_json(
            "GET",
            f"/api/v1/applications/{application_id}/audit-export?resume_versions_offset=-1",
        )
        self.assertEqual(status, 400)
        self.assertIn("resume_versions_offset must be a non-negative integer", body["detail"])

        status, body = self._request_json(
            "GET",
            f"/api/v1/applications/{application_id}/audit-export?resume_versions_limit=9999",
        )
        self.assertEqual(status, 422)
        self.assertIn("resume_versions_limit exceeds maximum", body["detail"])

    def test_endpoints_return_404_for_missing_entities(self) -> None:
        status, body = self._request_json("GET", "/api/v1/applications/missing")
        self.assertEqual(status, 404)
        self.assertIn("not found", body["detail"])

        status, body = self._request_json("GET", "/api/v1/resume-versions/missing")
        self.assertEqual(status, 404)
        self.assertIn("not found", body["detail"])

    def test_status_and_generate_reject_non_object_payloads(self) -> None:
        application_id = self._capture_application()

        status, body = self._request_json(
            "PATCH",
            f"/api/v1/applications/{application_id}/status",
            ["drafting"],
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["detail"], "invalid request payload")

        status, body = self._request_json(
            "POST",
            f"/api/v1/applications/{application_id}/resume-versions/generate",
            ["modern"],
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["detail"], "invalid request payload")


if __name__ == "__main__":
    unittest.main()
