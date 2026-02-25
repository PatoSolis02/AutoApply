from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import unittest
from contextlib import closing
from datetime import datetime
from http.client import HTTPConnection
from typing import Any

from app.main import create_server


class AuthApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = self._create_tmpdir()
        self.db_path = self._tmpdir + "/auth-test.db"
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

        return tempfile.mkdtemp(prefix="auth-api-tests-")

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Any = None,
        *,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict, dict[str, str]]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps(payload) if payload is not None else None
        request_headers = dict(headers or {})
        if payload is not None:
            request_headers["Content-Type"] = "application/json"
        conn.request(method, path, body=body, headers=request_headers)
        response = conn.getresponse()
        raw_body = response.read().decode("utf-8")
        response_headers = {key.lower(): value for key, value in response.getheaders()}
        conn.close()
        return response.status, (json.loads(raw_body) if raw_body else {}), response_headers

    def _signup(self, *, email: str = "user@example.com", password: str = "StrongPass123!") -> tuple[int, dict]:
        status, body, _ = self._request_json(
            "POST",
            "/api/v1/auth/signup",
            {"email": email, "password": password},
        )
        return status, body

    def _login(self, *, email: str = "user@example.com", password: str = "StrongPass123!") -> tuple[int, dict]:
        status, body, _ = self._request_json(
            "POST",
            "/api/v1/auth/login",
            {"email": email, "password": password},
        )
        return status, body

    def _bearer_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def test_signup_persists_user_and_returns_session_token(self) -> None:
        status, body = self._signup()
        self.assertEqual(status, 201)
        self.assertIn("token", body)
        self.assertIn("user", body)
        self.assertIn("session", body)

        token = str(body["token"])
        user_id = str(body["user"]["id"])
        session_id = str(body["session"]["id"])
        expires_at = str(body["session"]["expires_at"])
        created_at = str(body["session"]["created_at"])
        self.assertTrue(token)
        self.assertRegex(body["user"]["email"], r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        self.assertGreater(datetime.fromisoformat(expires_at), datetime.fromisoformat(created_at))

        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            user_row = conn.execute(
                "SELECT id, email, password_hash FROM auth_users WHERE id = ?",
                (user_id,),
            ).fetchone()
            session_row = conn.execute(
                "SELECT id, token_hash FROM auth_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()

        self.assertIsNotNone(user_row)
        self.assertEqual(user_row["email"], "user@example.com")
        self.assertTrue(user_row["password_hash"].startswith("pbkdf2_sha256$"))
        self.assertNotEqual(user_row["password_hash"], "StrongPass123!")
        self.assertIsNotNone(session_row)
        self.assertEqual(session_row["token_hash"], hashlib.sha256(token.encode("utf-8")).hexdigest())

    def test_signup_duplicate_email_returns_conflict_error_code(self) -> None:
        first_status, _ = self._signup(email="duplicate@example.com")
        self.assertEqual(first_status, 201)

        status, body = self._signup(email="DUPLICATE@example.com")
        self.assertEqual(status, 409)
        self.assertEqual(body["detail"], "email already registered")
        self.assertEqual(body["error"]["code"], "email_exists")

    def test_login_invalid_credentials_returns_deterministic_error(self) -> None:
        self._signup(email="login@example.com", password="StrongPass123!")

        status, body = self._login(email="login@example.com", password="WrongPassword123!")
        self.assertEqual(status, 401)
        self.assertEqual(body["error"]["code"], "invalid_credentials")
        self.assertEqual(body["detail"], "Email or password is incorrect.")

    def test_login_success_returns_new_session_token(self) -> None:
        _, signup_body = self._signup(email="login-success@example.com")

        status, login_body = self._login(email="login-success@example.com")
        self.assertEqual(status, 200)
        self.assertIn("token", login_body)
        self.assertNotEqual(login_body["token"], signup_body["token"])
        self.assertNotEqual(login_body["session"]["id"], signup_body["session"]["id"])

    def test_session_requires_authorization_header(self) -> None:
        status, body, _ = self._request_json("GET", "/api/v1/auth/session")
        self.assertEqual(status, 401)
        self.assertEqual(body["error"]["code"], "auth_required")

    def test_session_rejects_malformed_authorization_header(self) -> None:
        status, body, _ = self._request_json(
            "GET",
            "/api/v1/auth/session",
            headers={"Authorization": "Token abc"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(body["error"]["code"], "invalid_authorization_header")

    def test_session_returns_authenticated_context_for_active_token(self) -> None:
        _, signup_body = self._signup(email="session@example.com")
        token = str(signup_body["token"])

        status, body, _ = self._request_json(
            "GET",
            "/api/v1/auth/session",
            headers=self._bearer_headers(token),
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["authenticated"])
        self.assertEqual(body["user"]["id"], signup_body["user"]["id"])
        self.assertEqual(body["user"]["email"], "session@example.com")

    def test_logout_revokes_session_and_session_endpoint_rejects_token(self) -> None:
        _, signup_body = self._signup(email="logout@example.com")
        token = str(signup_body["token"])

        status, body, _ = self._request_json(
            "POST",
            "/api/v1/auth/logout",
            {},
            headers=self._bearer_headers(token),
        )
        self.assertEqual(status, 200)
        self.assertTrue(body["ok"])

        session_status, session_body, _ = self._request_json(
            "GET",
            "/api/v1/auth/session",
            headers=self._bearer_headers(token),
        )
        self.assertEqual(session_status, 401)
        self.assertEqual(session_body["error"]["code"], "invalid_session")

    def test_expired_session_returns_session_expired_error_and_revokes_session(self) -> None:
        _, signup_body = self._signup(email="expired@example.com")
        token = str(signup_body["token"])
        session_id = str(signup_body["session"]["id"])

        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                "UPDATE auth_sessions SET expires_at = ?, revoked_at = NULL WHERE id = ?",
                ("2000-01-01T00:00:00+00:00", session_id),
            )
            conn.commit()

        status, body, _ = self._request_json(
            "GET",
            "/api/v1/auth/session",
            headers=self._bearer_headers(token),
        )
        self.assertEqual(status, 401)
        self.assertEqual(body["error"]["code"], "session_expired")

        with closing(sqlite3.connect(self.db_path)) as conn:
            row = conn.execute(
                "SELECT revoked_at FROM auth_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        self.assertIsNotNone(row)
        self.assertIsNotNone(row[0])


if __name__ == "__main__":
    unittest.main()
