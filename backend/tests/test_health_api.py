from __future__ import annotations

import json
import threading
import unittest
from http.client import HTTPConnection

from app.main import create_server


class HealthApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = self._create_tmpdir()
        self.db_path = self._tmpdir + "/health-test.db"
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

        return tempfile.mkdtemp(prefix="health-api-tests-")

    def _request_json(self, method: str, path: str) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(method, path)
        response = conn.getresponse()
        raw = response.read().decode("utf-8")
        conn.close()
        return response.status, (json.loads(raw) if raw else {})

    def test_health_returns_ok(self) -> None:
        status, body = self._request_json("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
