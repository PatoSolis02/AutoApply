from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default as email_policy_default
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
from .resume_ingest import (
    ResumeParseError,
    ResumeParseValidationError,
    ResumeUnsupportedTypeError,
    parse_resume_upload,
)
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
_APPLICATION_AUDIT_EXPORT_PATTERN = re.compile(r"^/api/v1/applications/([^/]+)/audit-export$")
_RESUME_VERSION_PATTERN = re.compile(r"^/api/v1/resume-versions/([^/]+)$")
_RESUME_VERSION_APPROVE_PATTERN = re.compile(r"^/api/v1/resume-versions/([^/]+)/approve$")
_PROFILE_PATH = "/api/v1/profile"
_PROFILE_RESUME_PARSE_PATH = "/api/v1/profile/resume-parse"
_HEALTH_PATH = "/health"
_ALLOWED_STATUSES = {
    "captured",
    "drafting",
    "ready_to_apply",
    "applied",
    "interview",
    "rejected",
    "offer",
}


@dataclass
class _UploadedFormFile:
    filename: str
    content_type: str | None
    payload: bytes


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

            if parsed.path == _HEALTH_PATH:
                self._handle_health()
                return
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

            match = _APPLICATION_AUDIT_EXPORT_PATTERN.match(parsed.path)
            if match:
                self._handle_application_audit_export(match.group(1))
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

            if parsed.path == _PROFILE_RESUME_PARSE_PATH:
                self._handle_parse_resume_upload()
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
            payload = self._read_json_object()
            if payload is None:
                return

            capture, errors = validate_capture_payload(payload)
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

        def _handle_health(self) -> None:
            _json_response(self, HTTPStatus.OK, {"status": "ok"})

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
            payload = self._read_json_object()
            if payload is None:
                return

            target_status = self._read_required_non_empty_string(payload, "target_status")
            if target_status is None:
                return

            try:
                updated = capture_db.set_application_status(application_id, target_status)
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

        def _handle_application_audit_export(self, application_id: str) -> None:
            try:
                application = capture_db.get_application(application_id)
                job_posting = capture_db.get_job_posting_for_application(application_id)
            except DbNotFoundError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": str(err)})
                return

            _json_response(
                self,
                HTTPStatus.OK,
                {
                    "application": application,
                    "job_posting": job_posting,
                    "resume_versions": capture_db.list_resume_versions_for_application(application_id),
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                },
            )

        def _handle_generate_resume_version(self, application_id: str) -> None:
            payload = self._read_json_object()
            if payload is None:
                return

            template_id = self._read_required_non_empty_string(payload, "template_id")
            if template_id is None:
                return

            try:
                response_payload = handle_generate_resume_version(
                    generation_service,
                    application_id,
                    GenerateResumeRequest(template_id=template_id),
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

        def _handle_parse_resume_upload(self) -> None:
            form = self._read_multipart_form()
            if form is None:
                return

            fields, files = form

            if "file" not in files:
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {
                        "detail": "invalid request payload",
                        "errors": [{"field": "file", "message": "is required"}],
                    },
                )
                return

            upload_field = files["file"]
            filename = upload_field.filename
            payload = upload_field.payload
            upload_content_type = upload_field.content_type

            if not filename.strip():
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {
                        "detail": "invalid request payload",
                        "errors": [{"field": "file", "message": "must include a filename"}],
                    },
                )
                return
            if not payload:
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {
                        "detail": "invalid request payload",
                        "errors": [{"field": "file", "message": "must not be empty"}],
                    },
                )
                return

            profile_id_raw = fields.get("profile_id")
            profile_id = "primary"
            if profile_id_raw is not None:
                if not profile_id_raw.strip():
                    _json_response(
                        self,
                        HTTPStatus.BAD_REQUEST,
                        {
                            "detail": "invalid request payload",
                            "errors": [{"field": "profile_id", "message": "must be a non-empty string"}],
                        },
                    )
                    return
                profile_id = profile_id_raw.strip()

            try:
                parsed = parse_resume_upload(
                    filename=filename.strip(),
                    payload=payload,
                    profile_id=profile_id,
                    content_type=upload_content_type,
                )
            except ResumeUnsupportedTypeError as err:
                _json_response(self, HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"detail": str(err)})
                return
            except ResumeParseValidationError as err:
                _json_response(
                    self,
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                    {
                        "detail": "parsed profile failed validation",
                        "errors": err.errors,
                    },
                )
                return
            except ResumeParseError as err:
                _json_response(self, HTTPStatus.UNPROCESSABLE_ENTITY, {"detail": str(err)})
                return

            _json_response(self, HTTPStatus.OK, parsed)

        def _read_multipart_form(self) -> tuple[dict[str, str], dict[str, _UploadedFormFile]] | None:
            content_type = self.headers.get("Content-Type", "")
            if not content_type.lower().startswith("multipart/form-data"):
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {
                        "detail": "invalid request payload",
                        "errors": [{"field": "content_type", "message": "must be multipart/form-data"}],
                    },
                )
                return None

            content_length = self.headers.get("Content-Length", "0")
            try:
                length = int(content_length)
            except ValueError:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid request payload"})
                return None
            if length <= 0:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid request payload"})
                return None

            raw_body = self.rfile.read(length)
            parse_bytes = (
                f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
                + raw_body
            )
            message = BytesParser(policy=email_policy_default).parsebytes(parse_bytes)

            if not message.is_multipart():
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid request payload"})
                return None

            fields: dict[str, str] = {}
            files: dict[str, _UploadedFormFile] = {}

            for part in message.iter_parts():
                if part.get_content_disposition() != "form-data":
                    continue
                name = part.get_param("name", header="Content-Disposition")
                if not isinstance(name, str) or not name:
                    continue

                filename = part.get_filename()
                payload = part.get_payload(decode=True) or b""
                if isinstance(filename, str) and filename:
                    files[name] = _UploadedFormFile(
                        filename=filename,
                        content_type=part.get_content_type(),
                        payload=payload,
                    )
                    continue

                fields[name] = payload.decode("utf-8", errors="replace")

            return fields, files

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

        def _read_json_object(self) -> dict[str, Any] | None:
            payload = self._read_json_body()
            if payload is None:
                return None
            if not isinstance(payload, dict):
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid request payload"})
                return None
            return payload

        def _read_required_non_empty_string(self, payload: dict[str, Any], field: str) -> Optional[str]:
            value = payload.get(field)
            if not isinstance(value, str) or not value.strip():
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {
                        "detail": "invalid request payload",
                        "errors": [{"field": field, "message": "is required"}],
                    },
                )
                return None
            return value.strip()

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
