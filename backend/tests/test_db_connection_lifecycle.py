from __future__ import annotations

import gc
import sqlite3
import tempfile
import unittest
import warnings

from app.db import CaptureDatabase


class DbConnectionLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="db-connection-lifecycle-")
        self.db = CaptureDatabase(f"{self._tmpdir.name}/lifecycle.db")
        self.db.init_schema()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_connection_context_closes_connection_after_success(self) -> None:
        with self.db.connection() as conn:
            conn.execute("SELECT 1").fetchone()

        with self.assertRaisesRegex(sqlite3.ProgrammingError, "closed database"):
            conn.execute("SELECT 1").fetchone()

    def test_connection_context_closes_connection_after_exception(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "boom"):
            with self.db.connection() as conn:
                conn.execute("SELECT 1").fetchone()
                raise RuntimeError("boom")

        with self.assertRaisesRegex(sqlite3.ProgrammingError, "closed database"):
            conn.execute("SELECT 1").fetchone()

    def test_runtime_db_calls_emit_no_resource_warning(self) -> None:
        application_id, _ = self.db.insert_capture(
            title="Backend Engineer",
            company="Acme",
            location="Rochester, NY",
            job_url="https://www.linkedin.com/jobs/view/123",
            description_raw="Build APIs",
            captured_at="2026-02-24T00:00:00Z",
            structured_json={"summary": None, "responsibilities": [], "requirements": []},
        )

        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always", ResourceWarning)
            for _ in range(10):
                self.db.get_application(application_id)
                self.db.list_applications(status=None, company=None, page=1, page_size=10)
            gc.collect()

        resource_warnings = [warning for warning in captured if issubclass(warning.category, ResourceWarning)]
        self.assertEqual(resource_warnings, [])


if __name__ == "__main__":
    unittest.main()
