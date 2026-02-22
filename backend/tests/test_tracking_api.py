from __future__ import annotations

import json
import threading
import unittest
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

    def _capture_application(self, *, company: str = "Acme", title: str = "Backend Engineer") -> str:
        status, body = self._request_json(
            "POST",
            "/api/v1/jobs/capture",
            {
                "title": title,
                "company": company,
                "location": "Rochester, NY",
                "job_url": "https://www.linkedin.com/jobs/view/123",
                "description_raw": "Build API services with Python and SQL.",
                "captured_at": "2026-02-21T10:00:00Z",
            },
        )
        self.assertEqual(status, 201)
        return body["application_id"]

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
