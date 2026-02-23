from __future__ import annotations

import json
import threading
import unittest
from http.client import HTTPConnection
from typing import Any

from app.main import create_server


class ProfileApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = self._create_tmpdir()
        self.db_path = self._tmpdir + "/profile-test.db"
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

        return tempfile.mkdtemp(prefix="profile-api-tests-")

    def _request_json(self, method: str, path: str, payload: Any = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps(payload).encode("utf-8") if payload is not None else b""
        headers = {"Content-Type": "application/json"}
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        raw = response.read().decode("utf-8")
        conn.close()
        return response.status, (json.loads(raw) if raw else {})

    def test_get_profile_returns_404_when_missing(self) -> None:
        status, body = self._request_json("GET", "/api/v1/profile")
        self.assertEqual(status, 404)
        self.assertIn("not found", body["detail"])

    def test_put_profile_upserts_and_can_be_fetched(self) -> None:
        payload = {
            "id": "primary",
            "full_name": "Taylor Dev",
            "headline": "Backend Engineer",
            "summary": "Builds reliable APIs.",
            "skills": ["Python", "SQL", "FastAPI"],
            "experiences": [
                {
                    "id": "exp-1",
                    "company": "DataCo",
                    "title": "Engineer",
                    "bullets": ["Built APIs", "Improved reliability"],
                }
            ],
            "projects": [{"id": "proj-1", "name": "Internal Platform"}],
            "education": [{"id": "edu-1", "school": "RIT"}],
        }

        status, body = self._request_json("PUT", "/api/v1/profile", payload)
        self.assertEqual(status, 200)
        self.assertEqual(body["full_name"], "Taylor Dev")
        self.assertEqual(body["skills"], ["Python", "SQL", "FastAPI"])
        self.assertEqual(len(body["experiences"]), 1)

        status, fetched = self._request_json("GET", "/api/v1/profile")
        self.assertEqual(status, 200)
        self.assertEqual(fetched["id"], "primary")
        self.assertEqual(fetched["headline"], "Backend Engineer")
        self.assertEqual(fetched["projects"][0]["id"], "proj-1")

    def test_put_profile_validates_payload(self) -> None:
        status, body = self._request_json(
            "PUT",
            "/api/v1/profile",
            {
                "full_name": "",
                "skills": ["Python", 42],
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["detail"], "invalid request payload")
        fields = {item["field"] for item in body["errors"]}
        self.assertIn("full_name", fields)
        self.assertIn("skills", fields)

    def test_put_profile_defaults_primary_id_and_normalizes_optional_fields(self) -> None:
        status, body = self._request_json(
            "PUT",
            "/api/v1/profile",
            {
                "full_name": "  Taylor Dev  ",
                "headline": " ",
                "skills": [" Python ", "", "SQL", "   "],
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["id"], "primary")
        self.assertEqual(body["full_name"], "Taylor Dev")
        self.assertIsNone(body["headline"])
        self.assertIsNone(body["summary"])
        self.assertEqual(body["skills"], ["Python", "SQL"])
        self.assertEqual(body["experiences"], [])
        self.assertEqual(body["projects"], [])
        self.assertEqual(body["education"], [])

    def test_put_profile_rejects_non_object_payload(self) -> None:
        status, body = self._request_json("PUT", "/api/v1/profile", ["not-an-object"])
        self.assertEqual(status, 400)
        self.assertEqual(body["detail"], "invalid request payload")
        self.assertEqual(body["errors"], [{"field": "body", "message": "must be a JSON object"}])

    def test_put_profile_rejects_invalid_optional_collections(self) -> None:
        status, body = self._request_json(
            "PUT",
            "/api/v1/profile",
            {
                "full_name": "Taylor Dev",
                "experiences": [{"id": "exp-1"}, "invalid"],
                "projects": "invalid",
                "skills": "invalid",
                "education": [1],
            },
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["detail"], "invalid request payload")
        fields = {item["field"] for item in body["errors"]}
        self.assertIn("experiences", fields)
        self.assertIn("projects", fields)
        self.assertIn("skills", fields)
        self.assertIn("education", fields)


if __name__ == "__main__":
    unittest.main()
