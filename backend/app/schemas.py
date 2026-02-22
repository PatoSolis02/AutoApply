from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


@dataclass(frozen=True)
class CapturePayload:
    title: str
    company: str
    location: Optional[str]
    job_url: str
    description_raw: str
    captured_at: str


@dataclass(frozen=True)
class UserProfilePayload:
    profile_id: str
    full_name: str
    headline: Optional[str]
    summary: Optional[str]
    experiences: list[dict[str, Any]]
    projects: list[dict[str, Any]]
    skills: list[str]
    education: list[dict[str, Any]]



def _parse_datetime(value: str) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None

    normalized = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt.isoformat()



def _valid_http_url(value: str) -> bool:
    if not isinstance(value, str):
        return False

    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)



def validate_capture_payload(payload: object) -> Tuple[Optional[CapturePayload], List[Dict[str, str]]]:
    if not isinstance(payload, dict):
        return None, [{"field": "body", "message": "must be a JSON object"}]

    errors: list[dict[str, str]] = []

    def read_required(name: str) -> str:
        value = payload.get(name)
        if not isinstance(value, str) or not value.strip():
            errors.append({"field": name, "message": "is required"})
            return ""
        return value.strip()

    title = read_required("title")
    company = read_required("company")
    description_raw = read_required("description_raw")

    location_raw = payload.get("location")
    location = None
    if location_raw is not None:
        if not isinstance(location_raw, str):
            errors.append({"field": "location", "message": "must be a string or null"})
        else:
            location = location_raw.strip() or None

    job_url = payload.get("job_url")
    if not _valid_http_url(job_url):
        errors.append({"field": "job_url", "message": "must be a valid URL"})
        job_url = ""

    captured_at_raw = payload.get("captured_at")
    captured_at = _parse_datetime(captured_at_raw)
    if captured_at is None:
        errors.append({"field": "captured_at", "message": "must be an ISO 8601 datetime"})
        captured_at = ""

    if errors:
        return None, errors

    return (
        CapturePayload(
            title=title,
            company=company,
            location=location,
            job_url=job_url,
            description_raw=description_raw,
            captured_at=captured_at,
        ),
        [],
    )


def _optional_string(payload: dict[str, Any], key: str, errors: list[dict[str, str]]) -> Optional[str]:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        errors.append({"field": key, "message": "must be a string or null"})
        return None
    normalized = value.strip()
    return normalized or None


def _optional_list_of_objects(payload: dict[str, Any], key: str, errors: list[dict[str, str]]) -> list[dict[str, Any]]:
    value = payload.get(key)
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        errors.append({"field": key, "message": "must be an array of objects"})
        return []
    return [dict(item) for item in value]


def _optional_list_of_strings(payload: dict[str, Any], key: str, errors: list[dict[str, str]]) -> list[str]:
    value = payload.get(key)
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        errors.append({"field": key, "message": "must be an array of strings"})
        return []
    return [item.strip() for item in value if item.strip()]


def validate_user_profile_payload(payload: object) -> Tuple[Optional[UserProfilePayload], List[Dict[str, str]]]:
    if not isinstance(payload, dict):
        return None, [{"field": "body", "message": "must be a JSON object"}]

    errors: list[dict[str, str]] = []

    profile_id_raw = payload.get("id", "primary")
    if not isinstance(profile_id_raw, str) or not profile_id_raw.strip():
        errors.append({"field": "id", "message": "must be a non-empty string when provided"})
        profile_id = "primary"
    else:
        profile_id = profile_id_raw.strip()

    full_name_raw = payload.get("full_name")
    if not isinstance(full_name_raw, str) or not full_name_raw.strip():
        errors.append({"field": "full_name", "message": "is required"})
        full_name = ""
    else:
        full_name = full_name_raw.strip()

    headline = _optional_string(payload, "headline", errors)
    summary = _optional_string(payload, "summary", errors)
    experiences = _optional_list_of_objects(payload, "experiences", errors)
    projects = _optional_list_of_objects(payload, "projects", errors)
    skills = _optional_list_of_strings(payload, "skills", errors)
    education = _optional_list_of_objects(payload, "education", errors)

    if errors:
        return None, errors

    return (
        UserProfilePayload(
            profile_id=profile_id,
            full_name=full_name,
            headline=headline,
            summary=summary,
            experiences=experiences,
            projects=projects,
            skills=skills,
            education=education,
        ),
        [],
    )
