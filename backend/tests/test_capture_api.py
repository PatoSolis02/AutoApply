from __future__ import annotations

import json
import sqlite3
import threading
import unittest
from http.client import HTTPConnection

from app.main import create_server


class CaptureApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = self._create_tmpdir()
        self.db_path = self._tmpdir + "/capture-test.db"
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

        return tempfile.mkdtemp(prefix="capture-api-tests-")

    def _post_json(self, path: str, payload: dict) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("POST", path, body=json.dumps(payload), headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        conn.close()
        return response.status, json.loads(body)

    def test_capture_validation_error_returns_400(self) -> None:
        status, body = self._post_json(
            "/api/v1/jobs/capture",
            {
                "company": "Acme",
                "job_url": "https://www.linkedin.com/jobs/view/123",
                "description_raw": "Build APIs",
                "captured_at": "2026-02-21T10:00:00Z",
            },
        )

        self.assertEqual(status, 400)
        self.assertEqual(body["detail"], "invalid request payload")

    def test_capture_validation_error_emits_structured_failure_log(self) -> None:
        with self.assertLogs("autoapply.api", level="WARNING") as captured:
            status, body = self._post_json(
                "/api/v1/jobs/capture",
                {
                    "company": "Acme",
                    "job_url": "https://www.linkedin.com/jobs/view/123",
                    "description_raw": "Build APIs",
                    "captured_at": "2026-02-21T10:00:00Z",
                },
            )

        self.assertEqual(status, 400)
        self.assertEqual(body["detail"], "invalid request payload")
        entries = "\n".join(captured.output)
        self.assertIn('"event":"request.failed"', entries)
        self.assertIn('"error_class":"bad_request"', entries)
        self.assertIn('"request_id":"', entries)

    def test_capture_success_persists_application_and_job_posting(self) -> None:
        payload = {
            "title": "Backend Engineer",
            "company": "Acme",
            "location": "Rochester, NY",
            "job_url": "https://www.linkedin.com/jobs/view/123",
            "description_raw": (
                "We are hiring a Senior Backend Engineer.\n"
                "Responsibilities: Build API services.\n"
                "Requirements: 3+ years Python and FastAPI.\n"
                "Preferred: AWS experience.\n"
                "Full-time role."
            ),
            "captured_at": "2026-02-21T10:00:00Z",
        }

        status, body = self._post_json("/api/v1/jobs/capture", payload)
        self.assertEqual(status, 201)

        self.assertIn("application_id", body)
        self.assertIn("job_posting_id", body)

        with sqlite3.connect(self.db_path) as conn:
            app_row = conn.execute(
                "SELECT company, role_title, job_source, status, location FROM applications WHERE id = ?",
                (body["application_id"],),
            ).fetchone()
            posting_row = conn.execute(
                "SELECT application_id, raw_text, structured_json, captured_at FROM job_postings WHERE id = ?",
                (body["job_posting_id"],),
            ).fetchone()

        self.assertEqual(app_row, ("Acme", "Backend Engineer", "linkedin", "captured", "Rochester, NY"))
        self.assertIsNotNone(posting_row)
        self.assertEqual(posting_row[0], body["application_id"])
        self.assertEqual(posting_row[1], payload["description_raw"])
        self.assertEqual(posting_row[3], "2026-02-21T10:00:00+00:00")

        structured = json.loads(posting_row[2])
        self.assertEqual(structured["employment_type"], "full_time")
        self.assertEqual(structured["seniority"], "senior")
        self.assertIn("Python", structured["tech_stack"])


if __name__ == "__main__":
    unittest.main()
