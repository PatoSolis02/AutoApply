from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


@dataclass(frozen=True)
class CapturePayload:
    title: str
    company: str
    location: Optional[str]
    job_url: str
    description_raw: str
    captured_at: str



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
