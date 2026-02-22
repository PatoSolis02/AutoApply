from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from typing import Any, Optional, Union
from urllib.parse import parse_qs, urlparse

from .db import CaptureDatabase, DbComplianceError, DbConflictError, DbNotFoundError
from .ingest import build_structured_job_posting
from .runtime_generation import SqliteGenerateRepository
from .schemas import validate_capture_payload, validate_user_profile_payload

from autoapply.api import ApiError, handle_generate_resume_version
from autoapply.artifacts import ArtifactWriter
from autoapply.compliance import ComplianceGate
from autoapply.contracts import GenerateResumeRequest
from autoapply.service import ResumeGenerationService
from autoapply.tailoring import TailoringEngine

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "autoapply.db"
_APPLICATION_ID_PATTERN = re.compile(r"^/api/v1/applications/([^/]+)$")
_APPLICATION_STATUS_PATTERN = re.compile(r"^/api/v1/applications/([^/]+)/status$")
_APPLICATION_RESUME_VERSIONS_PATTERN = re.compile(r"^/api/v1/applications/([^/]+)/resume-versions$")
_APPLICATION_GENERATE_PATTERN = re.compile(r"^/api/v1/applications/([^/]+)/resume-versions/generate$")
_RESUME_VERSION_PATTERN = re.compile(r"^/api/v1/resume-versions/([^/]+)$")
_RESUME_VERSION_APPROVE_PATTERN = re.compile(r"^/api/v1/resume-versions/([^/]+)/approve$")
_PROFILE_PATH = "/api/v1/profile"
_ALLOWED_STATUSES = {
    "captured",
    "drafting",
    "ready_to_apply",
    "applied",
    "interview",
    "rejected",
    "offer",
}


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
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)

            if parsed.path == "/api/v1/applications":
                self._handle_list_applications(parsed.query)
                return
            if parsed.path == _PROFILE_PATH:
                self._handle_get_profile()
                return

            match = _APPLICATION_ID_PATTERN.match(parsed.path)
            if match:
                self._handle_get_application(match.group(1))
                return

            match = _APPLICATION_RESUME_VERSIONS_PATTERN.match(parsed.path)
            if match:
                self._handle_get_resume_versions_for_application(match.group(1))
                return

            match = _RESUME_VERSION_PATTERN.match(parsed.path)
            if match:
                self._handle_get_resume_version(match.group(1))
                return

            _json_response(self, HTTPStatus.NOT_FOUND, {"detail": "not found"})

        def do_PATCH(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            match = _APPLICATION_STATUS_PATTERN.match(parsed.path)
            if match is None:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": "not found"})
                return
            self._handle_update_application_status(match.group(1))

        def do_PUT(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == _PROFILE_PATH:
                self._handle_upsert_profile()
                return
            _json_response(self, HTTPStatus.NOT_FOUND, {"detail": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)

            if parsed.path == "/api/v1/jobs/capture":
                self._handle_capture()
                return

            match = _APPLICATION_GENERATE_PATTERN.match(parsed.path)
            if match:
                self._handle_generate_resume_version(match.group(1))
                return

            match = _RESUME_VERSION_APPROVE_PATTERN.match(parsed.path)
            if match:
                self._handle_approve_resume_version(match.group(1))
                return

            _json_response(self, HTTPStatus.NOT_FOUND, {"detail": "not found"})

        def _handle_capture(self) -> None:
            body = self._read_json_body()
            if body is None:
                return
            if not isinstance(body, dict):
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid request payload"})
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

        def _handle_get_profile(self) -> None:
            try:
                profile = capture_db.get_user_profile()
            except DbNotFoundError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": str(err)})
                return
            _json_response(self, HTTPStatus.OK, profile)

        def _handle_upsert_profile(self) -> None:
            body = self._read_json_body()
            if body is None:
                return

            profile_payload, errors = validate_user_profile_payload(body)
            if profile_payload is None:
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {"detail": "invalid request payload", "errors": errors},
                )
                return

            capture_db.upsert_user_profile(
                profile_id=profile_payload.profile_id,
                full_name=profile_payload.full_name,
                headline=profile_payload.headline,
                summary=profile_payload.summary,
                experiences=profile_payload.experiences,
                projects=profile_payload.projects,
                skills=profile_payload.skills,
                education=profile_payload.education,
            )
            profile = capture_db.get_user_profile()
            _json_response(self, HTTPStatus.OK, profile)

        def _handle_list_applications(self, query: str) -> None:
            params = parse_qs(query)
            page = self._read_positive_int(params.get("page", ["1"])[0], default=1)
            page_size = self._read_positive_int(params.get("page_size", ["20"])[0], default=20)
            if page is None or page_size is None:
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {"detail": "invalid query parameters: page and page_size must be positive integers"},
                )
                return

            status = params.get("status", [None])[0]
            if status is not None and status not in _ALLOWED_STATUSES:
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {"detail": f"invalid status '{status}'"},
                )
                return

            company = params.get("company", [None])[0]
            items, total = capture_db.list_applications(
                status=status,
                company=company,
                page=page,
                page_size=page_size,
            )
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    "items": items,
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                },
            )

        def _handle_get_application(self, application_id: str) -> None:
            try:
                application = capture_db.get_application(application_id)
            except DbNotFoundError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": str(err)})
                return

            latest = capture_db.get_latest_resume_version(application_id)
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    **application,
                    "latest_resume_version": latest,
                },
            )

        def _handle_update_application_status(self, application_id: str) -> None:
            payload = self._read_json_body()
            if payload is None:
                return
            if not isinstance(payload, dict):
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid request payload"})
                return

            target_status = payload.get("target_status")
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
                updated = capture_db.set_application_status(application_id, target_status.strip())
            except DbNotFoundError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": str(err)})
                return
            except DbConflictError as err:
                _json_response(self, HTTPStatus.CONFLICT, {"detail": str(err)})
                return
            except DbComplianceError as err:
                _json_response(self, HTTPStatus.UNPROCESSABLE_ENTITY, {"detail": str(err)})
                return

            latest = capture_db.get_latest_resume_version(application_id)
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    **updated,
                    "application": updated,
                    "latest_resume_version": latest,
                },
            )

        def _handle_get_resume_versions_for_application(self, application_id: str) -> None:
            try:
                capture_db.get_application(application_id)
            except DbNotFoundError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": str(err)})
                return

            versions = capture_db.list_resume_versions(application_id)
            _json_response(self, HTTPStatus.OK, {"items": versions})

        def _handle_get_resume_version(self, resume_version_id: str) -> None:
            try:
                resume_version = capture_db.get_resume_version(resume_version_id)
            except DbNotFoundError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": str(err)})
                return
            _json_response(self, HTTPStatus.OK, resume_version)

        def _handle_generate_resume_version(self, application_id: str) -> None:
            payload = self._read_json_body()
            if payload is None:
                return
            if not isinstance(payload, dict):
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid request payload"})
                return

            template_id = payload.get("template_id")
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
                response_payload = handle_generate_resume_version(
                    generation_service,
                    application_id,
                    GenerateResumeRequest(template_id=template_id.strip()),
                )
            except ApiError as err:
                _json_response(self, err.status_code, {"detail": err.detail})
                return

            _json_response(self, HTTPStatus.CREATED, response_payload)

        def _handle_approve_resume_version(self, resume_version_id: str) -> None:
            try:
                current = capture_db.get_resume_version(resume_version_id)
                approved = capture_db.approve_resume_version(resume_version_id)
            except DbNotFoundError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": str(err)})
                return
            except DbComplianceError as err:
                _json_response(self, HTTPStatus.UNPROCESSABLE_ENTITY, {"detail": str(err)})
                return

            application_id = str(current["application_id"])
            try:
                application = capture_db.get_application(application_id)
            except DbNotFoundError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": str(err)})
                return

            current_status = str(application["status"])
            if current_status != "ready_to_apply":
                try:
                    capture_db.set_application_status(application_id, "ready_to_apply")
                except DbConflictError as err:
                    _json_response(self, HTTPStatus.CONFLICT, {"detail": str(err)})
                    return
                except DbComplianceError as err:
                    _json_response(self, HTTPStatus.UNPROCESSABLE_ENTITY, {"detail": str(err)})
                    return

            _json_response(self, HTTPStatus.OK, approved)

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

        def _read_positive_int(self, value: str, *, default: int) -> Optional[int]:
            if value is None or value == "":
                return default
            try:
                parsed = int(value)
            except ValueError:
                return None
            if parsed <= 0:
                return None
            return parsed

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
