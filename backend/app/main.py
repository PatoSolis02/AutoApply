from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from typing import Any, Optional, Union
from urllib.parse import urlparse

from .db import CaptureDatabase, DbComplianceError, DbConflictError, DbNotFoundError
from .ingest import build_structured_job_posting
from .runtime_generation import SqliteGenerateRepository
from .schemas import validate_capture_payload

from autoapply.api import ApiError, handle_generate_resume_version
from autoapply.artifacts import ArtifactWriter
from autoapply.compliance import ComplianceGate
from autoapply.contracts import GenerateResumeRequest
from autoapply.service import ResumeGenerationService
from autoapply.tailoring import TailoringEngine

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "autoapply.db"
_GENERATE_PATH_RE = re.compile(r"^/api/v1/applications/([^/]+)/resume-versions/generate$")
_STATUS_PATH_RE = re.compile(r"^/api/v1/applications/([^/]+)/status$")
_APPROVE_PATH_RE = re.compile(r"^/api/v1/resume-versions/([^/]+)/approve$")


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: dict[str, Any]) -> None:
    payload = json.dumps(body).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def _build_handler(capture_db: CaptureDatabase):
    generation_service = ResumeGenerationService(
        repository=SqliteGenerateRepository(capture_db),
        tailoring_engine=TailoringEngine(),
        artifact_writer=ArtifactWriter(Path(__file__).resolve().parents[2]),
        compliance_gate=ComplianceGate(),
    )

    class CaptureRequestHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path

            if path == "/api/v1/jobs/capture":
                self._handle_capture()
                return

            match_generate = _GENERATE_PATH_RE.match(path)
            if match_generate is not None:
                self._handle_generate(match_generate.group(1))
                return

            match_approve = _APPROVE_PATH_RE.match(path)
            if match_approve is not None:
                self._handle_approve(match_approve.group(1))
                return

            _json_response(self, HTTPStatus.NOT_FOUND, {"detail": "not found"})

        def do_PATCH(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            match_status = _STATUS_PATH_RE.match(path)
            if match_status is None:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": "not found"})
                return
            self._handle_status_patch(match_status.group(1))

        def _handle_capture(self) -> None:
            body = self._read_json_body()
            if body is None:
                return

            capture, errors = validate_capture_payload(body)
            if capture is None:
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {"detail": "invalid request payload", "errors": errors},
                )
                return

            structured = build_structured_job_posting(capture.description_raw)
            application_id, job_posting_id = capture_db.insert_capture(
                title=capture.title,
                company=capture.company,
                location=capture.location,
                job_url=capture.job_url,
                description_raw=capture.description_raw,
                captured_at=capture.captured_at,
                structured_json=structured,
            )

            _json_response(
                self,
                HTTPStatus.CREATED,
                {
                    "application_id": application_id,
                    "job_posting_id": job_posting_id,
                },
            )

        def _handle_generate(self, application_id: str) -> None:
            body = self._read_json_body()
            if body is None:
                return
            if not isinstance(body, dict):
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid request payload"})
                return

            template_id = body.get("template_id")
            if not isinstance(template_id, str) or not template_id.strip():
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {
                        "detail": "invalid request payload",
                        "errors": [{"field": "template_id", "message": "is required"}],
                    },
                )
                return

            try:
                payload = handle_generate_resume_version(
                    generation_service,
                    application_id,
                    GenerateResumeRequest(template_id=template_id.strip()),
                )
            except ApiError as err:
                _json_response(self, err.status_code, {"detail": err.detail})
                return

            _json_response(self, HTTPStatus.CREATED, payload)

        def _handle_approve(self, resume_version_id: str) -> None:
            try:
                payload = capture_db.approve_resume_version(resume_version_id)
            except DbNotFoundError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": str(err)})
                return
            except DbComplianceError as err:
                _json_response(self, HTTPStatus.UNPROCESSABLE_ENTITY, {"detail": str(err)})
                return

            _json_response(self, HTTPStatus.OK, payload)

        def _handle_status_patch(self, application_id: str) -> None:
            body = self._read_json_body()
            if body is None:
                return
            if not isinstance(body, dict):
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid request payload"})
                return

            target_status = body.get("target_status")
            if not isinstance(target_status, str) or not target_status.strip():
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {
                        "detail": "invalid request payload",
                        "errors": [{"field": "target_status", "message": "is required"}],
                    },
                )
                return

            try:
                application = capture_db.set_application_status(application_id, target_status.strip())
            except DbNotFoundError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": str(err)})
                return
            except DbConflictError as err:
                _json_response(self, HTTPStatus.CONFLICT, {"detail": str(err)})
                return
            except DbComplianceError as err:
                _json_response(self, HTTPStatus.UNPROCESSABLE_ENTITY, {"detail": str(err)})
                return

            _json_response(self, HTTPStatus.OK, {"application": application})

        def _read_json_body(self) -> object | None:
            content_length = self.headers.get("Content-Length", "0")
            try:
                length = int(content_length)
            except ValueError:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid request payload"})
                return None

            raw_body = self.rfile.read(length)
            if len(raw_body) == 0:
                return {}

            try:
                return json.loads(raw_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {"detail": "invalid request payload", "errors": [{"field": "body", "message": "invalid JSON"}]},
                )
                return None

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    return CaptureRequestHandler


def create_server(
    db_path: Optional[Union[str, Path]] = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> ThreadingHTTPServer:
    db = CaptureDatabase(db_path or DEFAULT_DB_PATH)
    db.init_schema()
    return ThreadingHTTPServer((host, port), _build_handler(db))


def run_server(
    db_path: Optional[Union[str, Path]] = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    server = create_server(db_path=db_path, host=host, port=port)
    server.serve_forever()


if __name__ == "__main__":
    env_port = int(os.environ.get("AUTOAPPLY_API_PORT", "8000"))
    run_server(port=env_port)
