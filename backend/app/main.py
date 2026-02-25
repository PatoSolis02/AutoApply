from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.parser import BytesParser
from email.policy import default as email_policy_default
import hashlib
import hmac
import json
import logging
import os
import secrets
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import time
from typing import Any, Optional, Union
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from .db import CaptureDatabase, DbComplianceError, DbConflictError, DbNotFoundError
from .fit_scoring import FitScoringEngine
from .ingest import build_structured_job_posting
from .resume_ingest import (
    ResumeParseError,
    ResumeParseValidationError,
    ResumeUnsupportedTypeError,
    parse_resume_upload,
)
from .runtime_generation import SqliteGenerateRepository
from .schemas import (
    validate_auth_login_payload,
    validate_auth_signup_payload,
    validate_capture_payload,
    validate_user_profile_payload,
)

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
_PROFILE_RESUME_PARSE_LEGACY_PATH = "/api/v1/profile/ingest"
_AUTH_SIGNUP_PATH = "/api/v1/auth/signup"
_AUTH_LOGIN_PATH = "/api/v1/auth/login"
_AUTH_LOGOUT_PATH = "/api/v1/auth/logout"
_AUTH_SESSION_PATH = "/api/v1/auth/session"
_HEALTH_PATH = "/health"
_REQUEST_ID_HEADER = "X-Request-Id"
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_AUDIT_EXPORT_DEFAULT_RESUME_VERSIONS_LIMIT = 250
_AUDIT_EXPORT_MAX_RESUME_VERSIONS_LIMIT = 500
_AUDIT_EXPORT_RESUME_VERSIONS_CHUNK_SIZE = 100
_PASSWORD_HASH_ITERATIONS = 310_000
_PASSWORD_HASH_ALGORITHM = "sha256"
_PASSWORD_HASH_PREFIX = "pbkdf2_sha256"
_ALLOWED_STATUSES = {
    "captured",
    "drafting",
    "ready_to_apply",
    "applied",
    "interview",
    "rejected",
    "offer",
}
_LOGGER = logging.getLogger("autoapply.api")
if not _LOGGER.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(message)s"))
_LOGGER.addHandler(_handler)
_LOGGER.setLevel(logging.INFO)
_LOGGER.propagate = False


def _read_auth_session_ttl_seconds() -> int:
    default_seconds = 60 * 60 * 12
    raw_value = (os.environ.get("AUTOAPPLY_AUTH_SESSION_TTL_SECONDS", "") or "").strip()
    if not raw_value:
        return default_seconds
    try:
        parsed = int(raw_value)
    except ValueError:
        return default_seconds
    return parsed if parsed > 0 else default_seconds


_AUTH_SESSION_TTL_SECONDS = _read_auth_session_ttl_seconds()


@dataclass
class _UploadedFormFile:
    filename: str
    content_type: str | None
    payload: bytes


def _emit_structured_log(level: int, event: str, **fields: Any) -> None:
    payload: dict[str, Any] = {
        "event": event,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    payload.update({key: value for key, value in fields.items() if value is not None})
    _LOGGER.log(level, json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str))


def _normalize_request_id(header_value: str | None) -> tuple[str, str]:
    candidate = (header_value or "").strip()
    if _REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate, "client"
    return str(uuid4()), "generated"


def _classify_error(status: int, body: dict[str, Any]) -> str | None:
    if status < 400:
        return None
    if status == HTTPStatus.UNAUTHORIZED:
        return "unauthorized"
    if status == HTTPStatus.BAD_REQUEST:
        return "bad_request"
    if status == HTTPStatus.NOT_FOUND:
        return "not_found"
    if status == HTTPStatus.CONFLICT:
        return "conflict"
    if status == HTTPStatus.UNSUPPORTED_MEDIA_TYPE:
        return "unsupported_media_type"
    if status == HTTPStatus.UNPROCESSABLE_ENTITY:
        detail = body.get("detail")
        blocked_reasons = detail.get("blocked_reasons") if isinstance(detail, dict) else None
        if isinstance(blocked_reasons, list):
            return "compliance_failure"
        if isinstance(detail, str) and ("approval gate failed" in detail or "unsupported claims" in detail):
            return "compliance_failure"
        return "validation_failure"
    if status >= 500:
        return "internal_error"
    return "request_error"


def _failure_reason(body: dict[str, Any]) -> str | None:
    errors = body.get("errors")
    if isinstance(errors, list) and len(errors) > 0 and isinstance(errors[0], dict):
        field = errors[0].get("field")
        message = errors[0].get("message")
        if isinstance(field, str) and isinstance(message, str):
            return f"{field}: {message}"
    error = body.get("error")
    if isinstance(error, dict):
        code = error.get("code")
        message = error.get("message")
        if isinstance(code, str) and isinstance(message, str):
            return f"{code}: {message}"
    return None


def _truncate_detail(detail: Any, *, max_len: int = 240) -> str | None:
    if detail is None:
        return None
    if isinstance(detail, str):
        text = detail
    else:
        text = json.dumps(detail, sort_keys=True, default=str)
    if len(text) <= max_len:
        return text
    return f"{text[:max_len]}...(truncated)"


def _auth_error_response(handler: BaseHTTPRequestHandler, *, code: str, message: str) -> None:
    _json_response(
        handler,
        HTTPStatus.UNAUTHORIZED,
        {
            "detail": message,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        _PASSWORD_HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        _PASSWORD_HASH_ITERATIONS,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    digest_b64 = base64.b64encode(digest).decode("ascii")
    return f"{_PASSWORD_HASH_PREFIX}${_PASSWORD_HASH_ITERATIONS}${salt_b64}${digest_b64}"


def _verify_password(password: str, encoded: str) -> bool:
    parts = encoded.split("$")
    if len(parts) != 4:
        return False
    prefix, iterations_raw, salt_b64, digest_b64 = parts
    if prefix != _PASSWORD_HASH_PREFIX:
        return False
    try:
        iterations = int(iterations_raw)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(digest_b64.encode("ascii"))
    except (ValueError, binascii.Error):
        return False
    calculated = hashlib.pbkdf2_hmac(
        _PASSWORD_HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(expected, calculated)


def _hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_session_token() -> str:
    return secrets.token_urlsafe(32)


def _parse_utc_datetime(value: str | None) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _session_expiry_iso(*, now: datetime | None = None) -> str:
    base = now.astimezone(timezone.utc) if isinstance(now, datetime) else datetime.now(timezone.utc)
    return (base + timedelta(seconds=_AUTH_SESSION_TTL_SECONDS)).isoformat()


def _auth_success_payload(*, user: dict[str, Any], session: dict[str, Any], token: str) -> dict[str, Any]:
    return {
        "user": {
            "id": user["id"],
            "email": user["email"],
            "created_at": user["created_at"],
        },
        "session": {
            "id": session["id"],
            "created_at": session["created_at"],
            "expires_at": session["expires_at"],
        },
        "token": token,
    }


def _json_response(handler: BaseHTTPRequestHandler, status: int, body: dict[str, Any]) -> None:
    payload = json.dumps(body).encode("utf-8")
    request_id = getattr(handler, "_request_id", None)
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(payload)))
    if isinstance(request_id, str) and request_id:
        handler.send_header(_REQUEST_ID_HEADER, request_id)
    handler.end_headers()
    handler.wfile.write(payload)
    on_response_sent = getattr(handler, "_on_response_sent", None)
    if callable(on_response_sent):
        on_response_sent(status=status, body=body, payload_size=len(payload))


def _build_handler(capture_db: CaptureDatabase):
    generation_service = ResumeGenerationService(
        repository=SqliteGenerateRepository(capture_db),
        tailoring_engine=TailoringEngine(),
        artifact_writer=ArtifactWriter(Path(__file__).resolve().parents[2]),
        compliance_gate=ComplianceGate(),
    )
    fit_scoring_engine = FitScoringEngine()

    class CaptureRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self._begin_request("GET")
            parsed = urlparse(self.path)

            if parsed.path == _HEALTH_PATH:
                self._handle_health()
                return
            if parsed.path == _AUTH_SESSION_PATH:
                self._handle_get_auth_session()
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
                self._handle_application_audit_export(match.group(1), parsed.query)
                return

            match = _RESUME_VERSION_PATTERN.match(parsed.path)
            if match:
                self._handle_get_resume_version(match.group(1))
                return

            _json_response(self, HTTPStatus.NOT_FOUND, {"detail": "not found"})

        def do_PATCH(self) -> None:  # noqa: N802
            self._begin_request("PATCH")
            parsed = urlparse(self.path)
            match = _APPLICATION_STATUS_PATTERN.match(parsed.path)
            if match is None:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": "not found"})
                return
            self._handle_update_application_status(match.group(1))

        def do_PUT(self) -> None:  # noqa: N802
            self._begin_request("PUT")
            parsed = urlparse(self.path)
            if parsed.path == _PROFILE_PATH:
                self._handle_upsert_profile()
                return
            _json_response(self, HTTPStatus.NOT_FOUND, {"detail": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            self._begin_request("POST")
            parsed = urlparse(self.path)

            if parsed.path == _AUTH_SIGNUP_PATH:
                self._handle_auth_signup()
                return

            if parsed.path == _AUTH_LOGIN_PATH:
                self._handle_auth_login()
                return

            if parsed.path == _AUTH_LOGOUT_PATH:
                self._handle_auth_logout()
                return

            if parsed.path == "/api/v1/jobs/capture":
                self._handle_capture()
                return

            if parsed.path in {_PROFILE_RESUME_PARSE_PATH, _PROFILE_RESUME_PARSE_LEGACY_PATH}:
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
            _emit_structured_log(
                logging.INFO,
                "capture.created",
                request_id=self._request_id,
                application_id=application_id,
                job_posting_id=job_posting_id,
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

        def _handle_auth_signup(self) -> None:
            payload = self._read_json_object()
            if payload is None:
                return

            signup_payload, errors = validate_auth_signup_payload(payload)
            if signup_payload is None:
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {"detail": "invalid request payload", "errors": errors},
                )
                return

            try:
                user = capture_db.create_auth_user(
                    email=signup_payload.email,
                    password_hash=_hash_password(signup_payload.password),
                )
            except DbConflictError:
                _json_response(
                    self,
                    HTTPStatus.CONFLICT,
                    {
                        "detail": "email already registered",
                        "error": {
                            "code": "email_exists",
                            "message": "email already registered",
                        },
                    },
                )
                return

            token = _new_session_token()
            session = capture_db.create_auth_session(
                user_id=str(user["id"]),
                token_hash=_hash_session_token(token),
                expires_at=_session_expiry_iso(),
            )
            _emit_structured_log(
                logging.INFO,
                "auth.signup.succeeded",
                request_id=self._request_id,
                user_id=user["id"],
                session_id=session["id"],
            )
            _json_response(
                self,
                HTTPStatus.CREATED,
                _auth_success_payload(user=user, session=session, token=token),
            )

        def _handle_auth_login(self) -> None:
            payload = self._read_json_object()
            if payload is None:
                return

            login_payload, errors = validate_auth_login_payload(payload)
            if login_payload is None:
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {"detail": "invalid request payload", "errors": errors},
                )
                return

            try:
                user = capture_db.get_auth_user_by_email(login_payload.email)
            except DbNotFoundError:
                _auth_error_response(
                    self,
                    code="invalid_credentials",
                    message="Email or password is incorrect.",
                )
                return

            stored_hash = str(user.get("password_hash", ""))
            if not _verify_password(login_payload.password, stored_hash):
                _auth_error_response(
                    self,
                    code="invalid_credentials",
                    message="Email or password is incorrect.",
                )
                return

            token = _new_session_token()
            session = capture_db.create_auth_session(
                user_id=str(user["id"]),
                token_hash=_hash_session_token(token),
                expires_at=_session_expiry_iso(),
            )
            _emit_structured_log(
                logging.INFO,
                "auth.login.succeeded",
                request_id=self._request_id,
                user_id=user["id"],
                session_id=session["id"],
            )
            _json_response(
                self,
                HTTPStatus.OK,
                _auth_success_payload(user=user, session=session, token=token),
            )

        def _handle_auth_logout(self) -> None:
            session = self._read_active_auth_session()
            if session is None:
                return
            revoked = capture_db.revoke_auth_session(str(session["id"]))
            _emit_structured_log(
                logging.INFO,
                "auth.logout.succeeded",
                request_id=self._request_id,
                user_id=revoked["user"]["id"],
                session_id=revoked["id"],
            )
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "session": {
                        "id": revoked["id"],
                        "revoked_at": revoked["revoked_at"],
                    },
                },
            )

        def _handle_get_auth_session(self) -> None:
            session = self._read_active_auth_session()
            if session is None:
                return
            capture_db.touch_auth_session(str(session["id"]))
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    "authenticated": True,
                    "user": {
                        "id": session["user"]["id"],
                        "email": session["user"]["email"],
                        "created_at": session["user"]["created_at"],
                    },
                    "session": {
                        "id": session["id"],
                        "created_at": session["created_at"],
                        "expires_at": session["expires_at"],
                    },
                },
            )

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
            fit_profile = self._load_profile_for_fit()
            enriched_items = [
                self._enrich_application_fit(item, fit_profile, include_analysis=False)
                for item in items
            ]
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    "items": enriched_items,
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

            fit_profile = self._load_profile_for_fit()
            enriched = self._enrich_application_fit(application, fit_profile, include_analysis=True)
            latest = capture_db.get_latest_resume_version(application_id)
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    **enriched,
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
            _emit_structured_log(
                logging.INFO,
                "application.status.updated",
                request_id=self._request_id,
                application_id=application_id,
                status=str(updated.get("status")),
            )
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

        def _handle_application_audit_export(self, application_id: str, query: str) -> None:
            query_params = parse_qs(query, keep_blank_values=True)
            limit, limit_error = self._read_positive_query_int(
                query_params,
                "resume_versions_limit",
                default=_AUDIT_EXPORT_DEFAULT_RESUME_VERSIONS_LIMIT,
            )
            if limit_error is not None:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": limit_error})
                return
            if limit is None:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid resume_versions_limit"})
                return

            offset, offset_error = self._read_non_negative_query_int(
                query_params,
                "resume_versions_offset",
                default=0,
            )
            if offset_error is not None:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": offset_error})
                return
            if offset is None:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid resume_versions_offset"})
                return

            if limit > _AUDIT_EXPORT_MAX_RESUME_VERSIONS_LIMIT:
                _json_response(
                    self,
                    HTTPStatus.UNPROCESSABLE_ENTITY,
                    {
                        "detail": (
                            "resume_versions_limit exceeds maximum "
                            f"({_AUDIT_EXPORT_MAX_RESUME_VERSIONS_LIMIT})"
                        )
                    },
                )
                return

            try:
                application = capture_db.get_application(application_id)
                job_posting = capture_db.get_job_posting_for_application(application_id)
            except DbNotFoundError as err:
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": str(err)})
                return

            total_versions = capture_db.count_resume_versions_for_application(application_id)
            resume_versions = capture_db.list_resume_versions_for_application_window(
                application_id,
                limit=limit,
                offset=offset,
                chunk_size=_AUDIT_EXPORT_RESUME_VERSIONS_CHUNK_SIZE,
            )
            returned_versions = len(resume_versions)
            consumed_versions = min(total_versions, offset + returned_versions)
            remaining_versions = max(total_versions - consumed_versions, 0)
            fit_profile = self._load_profile_for_fit()
            enriched = self._enrich_application_fit(application, fit_profile, include_analysis=True)
            _json_response(
                self,
                HTTPStatus.OK,
                {
                    "application": enriched,
                    "job_posting": job_posting,
                    "resume_versions": resume_versions,
                    "resume_versions_page": {
                        "limit": limit,
                        "offset": offset,
                        "returned": returned_versions,
                        "total": total_versions,
                        "has_more": remaining_versions > 0,
                    },
                    "export_limits": {
                        "default_resume_versions_limit": _AUDIT_EXPORT_DEFAULT_RESUME_VERSIONS_LIMIT,
                        "max_resume_versions_limit": _AUDIT_EXPORT_MAX_RESUME_VERSIONS_LIMIT,
                    },
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
            _emit_structured_log(
                logging.INFO,
                "resume.version.generated",
                request_id=self._request_id,
                application_id=application_id,
                resume_version_id=response_payload.get("resume_version_id"),
                warnings_count=len(response_payload.get("warnings", [])),
                blocked_reasons_count=len(response_payload.get("blocked_reasons", [])),
            )

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

            _emit_structured_log(
                logging.INFO,
                "resume.version.approved",
                request_id=self._request_id,
                application_id=application_id,
                resume_version_id=resume_version_id,
                approval_recorded=bool(approved.get("approval", {}).get("approved", False)),
            )
            _json_response(self, HTTPStatus.OK, approved)

        def _handle_parse_resume_upload(self) -> None:
            form = self._read_multipart_form()
            if form is None:
                return

            fields, files = form
            upload = self._read_resume_upload_payload(files)
            if upload is None:
                return
            filename, payload, upload_content_type = upload

            profile_id = self._read_profile_id_field(fields)
            if profile_id is None:
                return

            try:
                parsed = parse_resume_upload(
                    filename=filename,
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

            _emit_structured_log(
                logging.INFO,
                "resume.parse.succeeded",
                request_id=self._request_id,
                profile_id=parsed.get("profile", {}).get("id"),
                file_type=parsed.get("source", {}).get("file_type"),
                parser_name=parsed.get("source", {}).get("parser"),
            )
            _json_response(self, HTTPStatus.OK, parsed)

        def _read_resume_upload_payload(
            self,
            files: dict[str, _UploadedFormFile],
        ) -> tuple[str, bytes, str | None] | None:
            upload_field_name = "file" if "file" in files else ("resume" if "resume" in files else None)
            if upload_field_name is None:
                self._invalid_request_field("file", "is required (or provide legacy 'resume' field)")
                return None

            upload_field = files[upload_field_name]
            filename = upload_field.filename.strip()
            if not filename:
                self._invalid_request_field(upload_field_name, "must include a filename")
                return None

            payload = upload_field.payload
            if not payload:
                self._invalid_request_field(upload_field_name, "must not be empty")
                return None
            return filename, payload, upload_field.content_type

        def _read_profile_id_field(self, fields: dict[str, str]) -> str | None:
            profile_id_raw = fields.get("profile_id")
            if profile_id_raw is None:
                return "primary"

            profile_id = profile_id_raw.strip()
            if not profile_id:
                self._invalid_request_field("profile_id", "must be a non-empty string")
                return None
            return profile_id

        def _load_profile_for_fit(self) -> dict[str, Any] | None:
            try:
                return capture_db.get_user_profile()
            except DbNotFoundError:
                return None

        def _enrich_application_fit(
            self,
            application: dict[str, Any],
            fit_profile: dict[str, Any] | None,
            *,
            include_analysis: bool,
        ) -> dict[str, Any]:
            application_id = str(application.get("id", ""))
            if not application_id:
                return dict(application)

            try:
                job_posting = capture_db.get_job_posting_for_application(application_id)
            except DbNotFoundError:
                if not include_analysis:
                    return dict(application)
                return {
                    **application,
                    "fit_analysis": {
                        "score": application.get("fit_score"),
                        "coverage": {
                            "requirements": {"matched": 0, "total": 0, "ratio": 1.0},
                            "preferred": {"matched": 0, "total": 0, "ratio": 1.0},
                            "keywords": {"matched": 0, "total": 0, "ratio": 1.0},
                        },
                        "matched_requirements": [],
                        "missing_requirements": [],
                        "matched_preferred": [],
                        "missing_preferred": [],
                        "matched_keywords": [],
                        "missing_keywords": [],
                        "gaps": [
                            {
                                "category": "job_posting",
                                "item": "Structured job data",
                                "severity": "high",
                                "reason": "Cannot score fit because job posting data is unavailable.",
                            }
                        ],
                        "notes": ["Structured job posting data is required for fit scoring."],
                    },
                }

            fit_analysis = fit_scoring_engine.evaluate(profile=fit_profile, job_posting=job_posting)
            fit_score = fit_analysis.get("score")
            if fit_score is None:
                fit_score = application.get("fit_score")

            enriched = {
                **application,
                "fit_score": fit_score,
            }
            if include_analysis:
                enriched["fit_analysis"] = fit_analysis
            return enriched

        def _begin_request(self, method: str) -> None:
            parsed = urlparse(self.path)
            request_id, request_id_source = _normalize_request_id(self.headers.get(_REQUEST_ID_HEADER))
            self._request_id = request_id
            self._request_method = method
            self._request_path = parsed.path
            self._request_started_at = time.perf_counter()
            self._response_logged = False
            _emit_structured_log(
                logging.INFO,
                "request.started",
                request_id=request_id,
                request_id_source=request_id_source,
                method=method,
                path=parsed.path,
                query=(parsed.query or None),
                remote_ip=self.client_address[0] if self.client_address else None,
                content_type=self.headers.get("Content-Type"),
                content_length=self.headers.get("Content-Length"),
            )

        def _on_response_sent(self, *, status: int, body: dict[str, Any], payload_size: int) -> None:
            if bool(getattr(self, "_response_logged", False)):
                return
            self._response_logged = True
            started = getattr(self, "_request_started_at", None)
            duration_ms: float | None = None
            if isinstance(started, (int, float)):
                duration_ms = round((time.perf_counter() - float(started)) * 1000, 3)

            error_class = _classify_error(status, body)
            event = "request.completed" if error_class is None else "request.failed"
            level = logging.INFO
            if status >= 500:
                level = logging.ERROR
            elif status >= 400:
                level = logging.WARNING

            _emit_structured_log(
                level,
                event,
                request_id=getattr(self, "_request_id", None),
                method=getattr(self, "_request_method", self.command),
                path=getattr(self, "_request_path", urlparse(self.path).path),
                status_code=status,
                duration_ms=duration_ms,
                response_bytes=payload_size,
                error_class=error_class,
                failure_reason=_failure_reason(body),
                detail=_truncate_detail(body.get("detail")),
            )

        def _read_bearer_token(self) -> str | None:
            authorization = self.headers.get("Authorization")
            if not isinstance(authorization, str) or not authorization.strip():
                _auth_error_response(
                    self,
                    code="auth_required",
                    message="Authorization header with Bearer token is required.",
                )
                return None

            parts = authorization.strip().split()
            if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
                _auth_error_response(
                    self,
                    code="invalid_authorization_header",
                    message="Authorization header must use Bearer token.",
                )
                return None
            return parts[1].strip()

        def _read_active_auth_session(self) -> dict[str, Any] | None:
            token = self._read_bearer_token()
            if token is None:
                return None

            token_hash = _hash_session_token(token)
            try:
                session = capture_db.get_auth_session_by_token_hash(token_hash)
            except DbNotFoundError:
                _auth_error_response(
                    self,
                    code="invalid_session",
                    message="Session is invalid or has been revoked.",
                )
                return None

            if session.get("revoked_at"):
                _auth_error_response(
                    self,
                    code="invalid_session",
                    message="Session is invalid or has been revoked.",
                )
                return None

            expires_at = _parse_utc_datetime(session.get("expires_at"))
            if expires_at is None:
                _auth_error_response(
                    self,
                    code="invalid_session",
                    message="Session is invalid or has been revoked.",
                )
                return None

            now = datetime.now(timezone.utc)
            if expires_at <= now:
                capture_db.revoke_auth_session(str(session["id"]), revoked_at=now.isoformat())
                _auth_error_response(
                    self,
                    code="session_expired",
                    message="Session has expired. Please log in again.",
                )
                return None

            return session

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
                self._invalid_request_field(field, "is required")
                return None
            return value.strip()

        def _invalid_request_field(self, field: str, message: str) -> None:
            _json_response(
                self,
                HTTPStatus.BAD_REQUEST,
                {
                    "detail": "invalid request payload",
                    "errors": [{"field": field, "message": message}],
                },
            )

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

        def _read_positive_query_int(
            self,
            params: dict[str, list[str]],
            field: str,
            *,
            default: int,
        ) -> tuple[int | None, str | None]:
            raw_values = params.get(field)
            if raw_values is None:
                return default, None
            raw_value = raw_values[0].strip()
            if raw_value == "":
                return None, f"invalid query parameter: {field} must be a positive integer"
            parsed = self._read_positive_int(raw_value, default=default)
            if parsed is None:
                return None, f"invalid query parameter: {field} must be a positive integer"
            return parsed, None

        def _read_non_negative_query_int(
            self,
            params: dict[str, list[str]],
            field: str,
            *,
            default: int,
        ) -> tuple[int | None, str | None]:
            raw_values = params.get(field)
            if raw_values is None:
                return default, None
            raw_value = raw_values[0].strip()
            if raw_value == "":
                return None, f"invalid query parameter: {field} must be a non-negative integer"
            try:
                parsed = int(raw_value)
            except ValueError:
                return None, f"invalid query parameter: {field} must be a non-negative integer"
            if parsed < 0:
                return None, f"invalid query parameter: {field} must be a non-negative integer"
            return parsed, None

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
