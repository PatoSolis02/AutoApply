from __future__ import annotations

import base64
import io
import json
import re
import zipfile
import zlib
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from autoapply.llm import LlmExecutionMetadata, LlmRuntime, PromptMessage, load_llm_config

CONTRACT_VERSION = "resume_parse.v1"

_SECTION_HEADERS = {
    "summary": "summary",
    "professional summary": "summary",
    "about": "summary",
    "objective": "summary",
    "profile": "summary",
    "skills": "skills",
    "technical skills": "skills",
    "skills technologies": "skills",
    "core skills": "skills",
    "technical proficiencies": "skills",
    "technologies": "skills",
    "tools": "skills",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment": "experience",
    "work history": "experience",
    "employment history": "experience",
    "projects": "projects",
    "selected projects": "projects",
    "education": "education",
    "academic background": "education",
}
_SUPPORTED_FILE_TYPES = {"pdf", "docx"}
_MONTH_YEAR_TOKEN_PATTERN = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}"
)
_DATE_TOKEN_PATTERN = rf"(?:{_MONTH_YEAR_TOKEN_PATTERN}|\d{{1,2}}/\d{{4}}|\d{{4}})"
_DATE_RANGE_PATTERN = re.compile(
    rf"(?P<start>{_DATE_TOKEN_PATTERN})\s*(?:[-\u2013\u2014]|to)\s*(?P<end>(?:present|current|now|{_DATE_TOKEN_PATTERN}))",
    flags=re.IGNORECASE,
)
_BULLET_PATTERN = re.compile(r"^(?:[-*]|\u2022|\u25e6|\u2023|\u2043)\s+")
_PDF_BT_BLOCK_PATTERN = re.compile(r"BT(.*?)ET", flags=re.DOTALL)
_PDF_TEXT_SHOW_PATTERN = re.compile(
    r"(?P<literal>\((?:\\.|[^\\)])*\))\s*(?P<literal_operator>Tj|\"|')|"
    r"(?P<hex><[0-9A-Fa-f\s]+>)\s*(?P<hex_operator>Tj|\"|')|"
    r"\[(?P<array>.*?)\]\s*TJ",
    flags=re.DOTALL,
)
_PDF_ARRAY_TOKEN_PATTERN = re.compile(
    r"\((?P<literal>(?:\\.|[^\\)])*)\)|<(?P<hex>[0-9A-Fa-f\s]+)>",
    flags=re.DOTALL,
)
_MONTH_TO_NUM = {
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "may": "05",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}
_PDF_FILTER_ALIASES = {
    "FlateDecode": "FlateDecode",
    "Fl": "FlateDecode",
    "ASCII85Decode": "ASCII85Decode",
    "A85": "ASCII85Decode",
    "ASCIIHexDecode": "ASCIIHexDecode",
    "AHx": "ASCIIHexDecode",
}
_NAME_BLACKLIST = {"resume", "curriculum vitae", "cv"}
_HEADLINE_LABELS = {"headline", "title", "role", "position"}
_HEADER_METADATA_LABELS = {
    "name",
    "email",
    "phone",
    "mobile",
    "linkedin",
    "github",
    "website",
    "portfolio",
    "location",
    "address",
}
_TITLE_HINT_PATTERN = re.compile(
    r"\b(engineer|developer|manager|analyst|intern|lead|director|architect|consultant|designer|scientist|administrator|specialist|coordinator|officer|founder|president)\b",
    flags=re.IGNORECASE,
)
_SKILL_KEYWORDS = [
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Node.js",
    "FastAPI",
    "Flask",
    "Django",
    "SQL",
    "PostgreSQL",
    "SQLite",
    "Redis",
    "AWS",
    "GCP",
    "Azure",
    "Docker",
    "Kubernetes",
    "Terraform",
    "Git",
    "Linux",
]
_MAX_LLM_SOURCE_LINES = 200
_MAX_LLM_SOURCE_CHARS = 12000
_NO_UPDATE = object()


class ResumeParseError(Exception):
    """Base error for resume upload parsing."""


class ResumeUnsupportedTypeError(ResumeParseError):
    """Raised when upload is not a supported resume type."""


class ResumeParseValidationError(ResumeParseError):
    """Raised when parsed profile data fails contract validation."""

    def __init__(self, errors: list[dict[str, str]]):
        super().__init__("parsed profile failed validation")
        self.errors = errors


def parse_resume_upload(
    *,
    filename: str,
    payload: bytes,
    profile_id: str = "primary",
    content_type: str | None = None,
    llm_runtime: LlmRuntime | None = None,
) -> dict[str, Any]:
    file_type = _detect_file_type(filename, content_type)
    text = _extract_text(file_type, payload)
    lines = _normalize_lines(text)
    profile, warnings = _map_to_profile(lines=lines, profile_id=profile_id)
    normalized_profile, normalized_warnings, normalization = _normalize_profile_with_llm(
        lines=lines,
        profile=profile,
        warnings=warnings,
        llm_runtime=llm_runtime or LlmRuntime(load_llm_config()),
    )
    errors = _validate_profile(normalized_profile)
    if errors:
        raise ResumeParseValidationError(errors)

    return {
        "contract_version": CONTRACT_VERSION,
        "source": {
            "filename": filename,
            "content_type": content_type or "",
            "file_type": file_type,
            "size_bytes": len(payload),
        },
        "profile": normalized_profile,
        "warnings": normalized_warnings,
        "normalization": normalization,
    }


def _normalize_profile_with_llm(
    *,
    lines: list[str],
    profile: dict[str, Any],
    warnings: list[str],
    llm_runtime: LlmRuntime,
) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    baseline_profile = _clone_profile(profile)
    baseline_warnings = [warning for warning in warnings if isinstance(warning, str) and warning.strip()]

    execution = llm_runtime.run_with_fallback(
        workflow="resume_parse",
        messages=_build_parse_normalization_messages(lines=lines, profile=baseline_profile, warnings=baseline_warnings),
        llm_transform=lambda response: _llm_transform_parse_profile(
            response_text=response.text,
            baseline_profile=baseline_profile,
        ),
        deterministic_fn=lambda: _normalization_result_from_profile(baseline_profile, baseline_warnings),
    )
    normalized_profile = execution.value["profile"]
    normalized_warnings = execution.value["warnings"]
    changes = _build_profile_change_trace(lines=lines, before=baseline_profile, after=normalized_profile)
    normalization = _build_normalization_metadata(execution.metadata, changes)
    return normalized_profile, normalized_warnings, normalization


def _build_parse_normalization_messages(
    *,
    lines: list[str],
    profile: dict[str, Any],
    warnings: list[str],
) -> list[PromptMessage]:
    rendered_lines = "\n".join(f"{idx + 1}: {line}" for idx, line in enumerate(lines[:_MAX_LLM_SOURCE_LINES]))
    if len(rendered_lines) > _MAX_LLM_SOURCE_CHARS:
        rendered_lines = rendered_lines[:_MAX_LLM_SOURCE_CHARS]

    source_profile = json.dumps(profile, ensure_ascii=True)
    source_warnings = json.dumps(warnings, ensure_ascii=True)
    return [
        PromptMessage(
            role="system",
            content=(
                "You normalize deterministic resume parser output into canonical profile fields. "
                "Do not invent facts and do not add experiences/projects/education not present in the source lines. "
                "Return JSON only."
            ),
        ),
        PromptMessage(
            role="user",
            content=(
                "Source resume lines:\n"
                f"{rendered_lines}\n\n"
                "Deterministic parser output JSON:\n"
                f"{source_profile}\n\n"
                "Deterministic warnings:\n"
                f"{source_warnings}\n\n"
                "Return exactly this shape as JSON:\n"
                "{\"profile\": { ... }}\n"
                "Use the same contract fields and preserve existing entry ids when present."
            ),
        ),
    ]


def _llm_transform_parse_profile(
    *,
    response_text: str,
    baseline_profile: dict[str, Any],
) -> dict[str, Any]:
    payload = _extract_json_object(response_text)
    candidate_profile: Any = payload.get("profile")
    if not isinstance(candidate_profile, dict):
        candidate_profile = payload
    normalized_profile = _merge_profile_candidate(baseline=baseline_profile, candidate=candidate_profile)
    errors = _validate_profile(normalized_profile)
    if errors:
        raise ValueError("llm normalization failed profile validation")
    return _normalization_result_from_profile(normalized_profile)


def _extract_json_object(text: str) -> dict[str, Any]:
    content = text.strip()
    if content.startswith("```"):
        content = "\n".join(
            line for line in content.splitlines() if not line.strip().startswith("```")
        ).strip()
    if not content:
        raise ValueError("llm response was empty")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("llm response did not include json object")
        parsed = json.loads(content[start : end + 1])

    if not isinstance(parsed, dict):
        raise ValueError("llm response json must be an object")
    return parsed


def _merge_profile_candidate(*, baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    merged = _clone_profile(baseline)
    if not isinstance(candidate, dict):
        return merged

    full_name = _as_non_empty_string(candidate.get("full_name"))
    if full_name is not None:
        merged["full_name"] = full_name

    headline = _as_nullable_string_update(candidate.get("headline"))
    if headline is not _NO_UPDATE:
        merged["headline"] = headline

    summary = _as_nullable_string_update(candidate.get("summary"))
    if summary is not _NO_UPDATE:
        merged["summary"] = summary

    skills = _as_string_list(candidate.get("skills"))
    if skills is not None:
        merged["skills"] = _dedupe_case_preserving(skills)

    merged["experiences"] = _merge_experience_entries(
        baseline_entries=_safe_dict_list(baseline.get("experiences")),
        candidate_entries=candidate.get("experiences"),
    )
    merged["projects"] = _merge_project_entries(
        baseline_entries=_safe_dict_list(baseline.get("projects")),
        candidate_entries=candidate.get("projects"),
    )
    merged["education"] = _merge_education_entries(
        baseline_entries=_safe_dict_list(baseline.get("education")),
        candidate_entries=candidate.get("education"),
    )
    return merged


def _merge_experience_entries(*, baseline_entries: list[dict[str, Any]], candidate_entries: Any) -> list[dict[str, Any]]:
    if not isinstance(candidate_entries, list):
        return [_clone_profile(entry) for entry in baseline_entries]

    merged: list[dict[str, Any]] = []
    target_count = max(len(baseline_entries), len(candidate_entries))
    for idx in range(target_count):
        candidate = candidate_entries[idx] if idx < len(candidate_entries) else None
        if idx < len(baseline_entries):
            entry = _clone_profile(baseline_entries[idx])
            if isinstance(candidate, dict):
                company = _as_non_empty_string(candidate.get("company"))
                if company is not None:
                    entry["company"] = company

                title = _as_non_empty_string(candidate.get("title"))
                if title is not None:
                    entry["title"] = title

                start_date = _as_non_empty_string(candidate.get("start_date"))
                if start_date is not None:
                    entry["start_date"] = start_date

                end_date = _as_nullable_string_update(candidate.get("end_date"))
                if end_date is not _NO_UPDATE:
                    entry["end_date"] = end_date

                bullets = _as_string_list(candidate.get("bullets"))
                if bullets is not None:
                    entry["bullets"] = bullets

                skills = _as_string_list(candidate.get("skills"))
                if skills is not None:
                    entry["skills"] = _dedupe_case_preserving(skills)
            merged.append(entry)
            continue

        if not isinstance(candidate, dict):
            continue
        company = _as_non_empty_string(candidate.get("company"))
        title = _as_non_empty_string(candidate.get("title"))
        if company is None or title is None:
            continue

        start_date = _as_non_empty_string(candidate.get("start_date")) or ""
        end_date = _as_nullable_string_update(candidate.get("end_date"))
        if end_date is _NO_UPDATE:
            end_date = None
        entry = _new_experience(idx + 1, company, title, start_date, end_date)
        entry_id = _as_non_empty_string(candidate.get("id"))
        if entry_id is not None:
            entry["id"] = entry_id

        bullets = _as_string_list(candidate.get("bullets"))
        skills = _as_string_list(candidate.get("skills"))
        entry["bullets"] = bullets or []
        entry["skills"] = _dedupe_case_preserving(skills or [])
        merged.append(entry)

    return merged


def _merge_project_entries(*, baseline_entries: list[dict[str, Any]], candidate_entries: Any) -> list[dict[str, Any]]:
    if not isinstance(candidate_entries, list):
        return [_clone_profile(entry) for entry in baseline_entries]

    merged: list[dict[str, Any]] = []
    target_count = max(len(baseline_entries), len(candidate_entries))
    for idx in range(target_count):
        candidate = candidate_entries[idx] if idx < len(candidate_entries) else None
        if idx < len(baseline_entries):
            entry = _clone_profile(baseline_entries[idx])
            if isinstance(candidate, dict):
                name = _as_non_empty_string(candidate.get("name"))
                if name is not None:
                    entry["name"] = name

                description = _as_non_empty_string(candidate.get("description"))
                if description is not None:
                    entry["description"] = description

                url = _as_nullable_string_update(candidate.get("url"))
                if url is not _NO_UPDATE:
                    entry["url"] = url

                bullets = _as_string_list(candidate.get("bullets"))
                if bullets is not None:
                    entry["bullets"] = bullets

                skills = _as_string_list(candidate.get("skills"))
                if skills is not None:
                    entry["skills"] = _dedupe_case_preserving(skills)
            merged.append(entry)
            continue

        if not isinstance(candidate, dict):
            continue
        name = _as_non_empty_string(candidate.get("name"))
        if name is None:
            continue
        description = _as_non_empty_string(candidate.get("description")) or ""
        entry = _new_project(idx + 1, name, description)
        entry_id = _as_non_empty_string(candidate.get("id"))
        if entry_id is not None:
            entry["id"] = entry_id

        url = _as_nullable_string_update(candidate.get("url"))
        if url is not _NO_UPDATE:
            entry["url"] = url

        bullets = _as_string_list(candidate.get("bullets"))
        skills = _as_string_list(candidate.get("skills"))
        entry["bullets"] = bullets or []
        entry["skills"] = _dedupe_case_preserving(skills or [])
        merged.append(entry)
    return merged


def _merge_education_entries(*, baseline_entries: list[dict[str, Any]], candidate_entries: Any) -> list[dict[str, Any]]:
    if not isinstance(candidate_entries, list):
        return [_clone_profile(entry) for entry in baseline_entries]

    merged: list[dict[str, Any]] = []
    target_count = max(len(baseline_entries), len(candidate_entries))
    for idx in range(target_count):
        candidate = candidate_entries[idx] if idx < len(candidate_entries) else None
        if idx < len(baseline_entries):
            entry = _clone_profile(baseline_entries[idx])
            if isinstance(candidate, dict):
                school = _as_non_empty_string(candidate.get("school"))
                if school is not None:
                    entry["school"] = school

                degree = _as_non_empty_string(candidate.get("degree"))
                if degree is not None:
                    entry["degree"] = degree

                field = _as_nullable_string_update(candidate.get("field"))
                if field is not _NO_UPDATE:
                    entry["field"] = field

                start_date = _as_nullable_string_update(candidate.get("start_date"))
                if start_date is not _NO_UPDATE:
                    entry["start_date"] = start_date

                end_date = _as_nullable_string_update(candidate.get("end_date"))
                if end_date is not _NO_UPDATE:
                    entry["end_date"] = end_date
            merged.append(entry)
            continue

        if not isinstance(candidate, dict):
            continue
        school = _as_non_empty_string(candidate.get("school"))
        if school is None:
            continue
        degree = _as_non_empty_string(candidate.get("degree")) or ""
        entry = {
            "id": f"edu-{idx + 1}",
            "school": school,
            "degree": degree,
            "field": None,
            "start_date": None,
            "end_date": None,
        }
        entry_id = _as_non_empty_string(candidate.get("id"))
        if entry_id is not None:
            entry["id"] = entry_id

        field = _as_nullable_string_update(candidate.get("field"))
        if field is not _NO_UPDATE:
            entry["field"] = field
        start_date = _as_nullable_string_update(candidate.get("start_date"))
        if start_date is not _NO_UPDATE:
            entry["start_date"] = start_date
        end_date = _as_nullable_string_update(candidate.get("end_date"))
        if end_date is not _NO_UPDATE:
            entry["end_date"] = end_date
        merged.append(entry)
    return merged


def _as_non_empty_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


def _as_nullable_string_update(value: Any) -> str | None | object:
    if value is None:
        return None
    if not isinstance(value, str):
        return _NO_UPDATE
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


def _as_string_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        normalized = item.strip()
        if not normalized:
            continue
        out.append(normalized)
    return out


def _safe_dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        out.append(item)
    return out


def _normalization_result_from_profile(profile: dict[str, Any], warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "profile": _clone_profile(profile),
        "warnings": _derive_profile_warnings(profile) if warnings is None else list(warnings),
    }


def _derive_profile_warnings(profile: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not profile.get("experiences"):
        warnings.append("experience section was empty or not detected")
    if not profile.get("skills"):
        warnings.append("skills section was empty or not detected")
    if not profile.get("education"):
        warnings.append("education section was empty or not detected")
    if not profile.get("projects"):
        warnings.append("projects section was empty or not detected")
    return warnings


def _build_normalization_metadata(
    metadata: LlmExecutionMetadata,
    changes: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "mode": metadata.mode,
        "reason": metadata.reason,
        "provider": metadata.provider,
        "model": metadata.model,
        "prompt_version": metadata.prompt_version,
        "applied": metadata.mode == "llm" and bool(changes),
        "change_count": len(changes),
        "changes": changes,
    }


def _build_profile_change_trace(
    *,
    lines: list[str],
    before: dict[str, Any],
    after: dict[str, Any],
) -> list[dict[str, Any]]:
    before_flat = _flatten_profile_for_trace(before)
    after_flat = _flatten_profile_for_trace(after)
    changes: list[dict[str, Any]] = []
    for field in sorted(set(before_flat) | set(after_flat)):
        before_value = before_flat.get(field)
        after_value = after_flat.get(field)
        if before_value == after_value:
            continue
        item: dict[str, Any] = {
            "field": field,
            "before": before_value,
            "after": after_value,
        }
        evidence = _find_trace_evidence_line(lines, before_value=before_value, after_value=after_value)
        if evidence is not None:
            item["evidence_line"] = evidence
        changes.append(item)
    return changes


def _flatten_profile_for_trace(profile: dict[str, Any]) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    out["full_name"] = _as_trace_string(profile.get("full_name"))
    out["headline"] = _as_trace_string(profile.get("headline"))
    out["summary"] = _as_trace_string(profile.get("summary"))

    skills = profile.get("skills")
    if isinstance(skills, list):
        for idx, item in enumerate(skills):
            out[f"skills[{idx}]"] = _as_trace_string(item)

    experiences = profile.get("experiences")
    if isinstance(experiences, list):
        for exp_idx, entry in enumerate(experiences):
            if not isinstance(entry, dict):
                continue
            for key in ("company", "title", "start_date", "end_date"):
                out[f"experiences[{exp_idx}].{key}"] = _as_trace_string(entry.get(key))
            bullets = entry.get("bullets")
            if isinstance(bullets, list):
                for bullet_idx, bullet in enumerate(bullets):
                    out[f"experiences[{exp_idx}].bullets[{bullet_idx}]"] = _as_trace_string(bullet)
            skills_list = entry.get("skills")
            if isinstance(skills_list, list):
                for skill_idx, skill in enumerate(skills_list):
                    out[f"experiences[{exp_idx}].skills[{skill_idx}]"] = _as_trace_string(skill)

    projects = profile.get("projects")
    if isinstance(projects, list):
        for proj_idx, entry in enumerate(projects):
            if not isinstance(entry, dict):
                continue
            for key in ("name", "description", "url"):
                out[f"projects[{proj_idx}].{key}"] = _as_trace_string(entry.get(key))
            bullets = entry.get("bullets")
            if isinstance(bullets, list):
                for bullet_idx, bullet in enumerate(bullets):
                    out[f"projects[{proj_idx}].bullets[{bullet_idx}]"] = _as_trace_string(bullet)
            skills_list = entry.get("skills")
            if isinstance(skills_list, list):
                for skill_idx, skill in enumerate(skills_list):
                    out[f"projects[{proj_idx}].skills[{skill_idx}]"] = _as_trace_string(skill)

    education = profile.get("education")
    if isinstance(education, list):
        for edu_idx, entry in enumerate(education):
            if not isinstance(entry, dict):
                continue
            for key in ("school", "degree", "field", "start_date", "end_date"):
                out[f"education[{edu_idx}].{key}"] = _as_trace_string(entry.get(key))

    return out


def _as_trace_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized


def _find_trace_evidence_line(
    lines: list[str],
    *,
    before_value: str | None,
    after_value: str | None,
) -> str | None:
    candidates = [after_value, before_value]
    lowered_lines = [line.lower() for line in lines]
    for candidate in candidates:
        if not candidate:
            continue
        lowered_candidate = candidate.lower()
        for idx, line in enumerate(lowered_lines):
            if lowered_candidate in line:
                return f"{idx + 1}: {lines[idx]}"
    return None


def _clone_profile(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _clone_profile(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_clone_profile(item) for item in value]
    return value


def _detect_file_type(filename: str, content_type: str | None) -> str:
    ext = Path(filename).suffix.lower()
    normalized_content_type = (content_type or "").split(";")[0].strip().lower()

    if ext == ".pdf" or normalized_content_type == "application/pdf":
        return "pdf"
    if ext == ".docx" or normalized_content_type in {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    }:
        return "docx"
    raise ResumeUnsupportedTypeError("only .pdf and .docx uploads are supported")


def _extract_text(file_type: str, payload: bytes) -> str:
    if file_type not in _SUPPORTED_FILE_TYPES:
        raise ResumeUnsupportedTypeError(f"unsupported file type '{file_type}'")
    if file_type == "pdf":
        return _extract_pdf_text(payload)
    return _extract_docx_text(payload)


def _extract_pdf_text(payload: bytes) -> str:
    if not payload.startswith(b"%PDF"):
        raise ResumeParseError("invalid pdf payload")

    stream_texts = _extract_pdf_stream_texts(payload)
    to_unicode_map = _build_tounicode_map(stream_texts)

    chunks: list[str] = []
    for source in stream_texts:
        if "BT" not in source:
            continue
        chunks.extend(_extract_pdf_chunks_from_source(source, to_unicode_map))

    if not chunks:
        decoded = payload.decode("latin-1", errors="ignore")
        chunks.extend(_extract_pdf_chunks_from_source(decoded, to_unicode_map))

    normalized_chunks = [chunk.strip() for chunk in chunks if chunk and chunk.strip()]
    if not normalized_chunks:
        raise ResumeParseError("unable to extract text from pdf")
    return "\n".join(normalized_chunks)


def _decode_pdf_literal(value: str) -> str:
    out: list[str] = []
    escaped = False
    octal_buf = ""
    for char in value:
        if octal_buf:
            if char.isdigit() and len(octal_buf) < 3:
                octal_buf += char
                continue
            out.append(chr(int(octal_buf, 8)))
            octal_buf = ""

        if escaped:
            if char in {"\\", "(", ")"}:
                out.append(char)
            elif char in {"n", "r", "t"}:
                out.append({"n": "\n", "r": "\r", "t": "\t"}[char])
            elif char.isdigit():
                octal_buf = char
            else:
                out.append(char)
            escaped = False
            continue

        if char == "\\":
            escaped = True
            continue
        out.append(char)

    if octal_buf:
        out.append(chr(int(octal_buf, 8)))
    return "".join(out)


def _extract_pdf_stream_texts(payload: bytes) -> list[str]:
    texts: list[str] = []
    search_start = 0

    while True:
        stream_start = payload.find(b"stream", search_start)
        if stream_start == -1:
            break

        data_start = stream_start + len(b"stream")
        if payload[data_start : data_start + 2] == b"\r\n":
            data_start += 2
        elif payload[data_start : data_start + 1] in {b"\r", b"\n"}:
            data_start += 1

        stream_end = payload.find(b"endstream", data_start)
        if stream_end == -1:
            break

        stream_payload = payload[data_start:stream_end].rstrip(b"\r\n")
        stream_filters = _extract_pdf_stream_filters(payload, stream_start)
        for variant in _pdf_stream_variants(stream_payload, stream_filters):
            text = variant.decode("latin-1", errors="ignore")
            if text:
                texts.append(text)

        search_start = stream_end + len(b"endstream")

    return texts


def _extract_pdf_stream_filters(payload: bytes, stream_start: int) -> list[str]:
    window_start = max(0, stream_start - 4096)
    dictionary_start = payload.rfind(b"<<", window_start, stream_start)
    if dictionary_start == -1:
        return []

    dictionary_end = payload.find(b">>", dictionary_start, stream_start)
    if dictionary_end == -1:
        return []

    dictionary = payload[dictionary_start : dictionary_end + 2].decode("latin-1", errors="ignore")
    match = re.search(r"/Filter\s*(\[(?P<array>.*?)\]|(?P<single>/[A-Za-z0-9]+))", dictionary, flags=re.DOTALL)
    if match is None:
        return []

    names: list[str] = []
    if match.group("array"):
        names = re.findall(r"/([A-Za-z0-9]+)", match.group("array"))
    elif match.group("single"):
        names = [match.group("single")[1:]]

    filters: list[str] = []
    for name in names:
        normalized = _PDF_FILTER_ALIASES.get(name, "")
        if normalized:
            filters.append(normalized)
    return filters


def _pdf_stream_variants(stream_payload: bytes, filters: list[str]) -> list[bytes]:
    variants = [stream_payload]

    if filters:
        decoded_with_filters = _decode_pdf_stream_with_filters(stream_payload, filters)
        if decoded_with_filters and decoded_with_filters not in variants:
            variants.append(decoded_with_filters)

    for candidate in [stream_payload, _decode_pdf_ascii85(stream_payload), _decode_pdf_asciihex(stream_payload)]:
        if not candidate:
            continue
        for wbits in (None, -15):
            try:
                decoded = zlib.decompress(candidate) if wbits is None else zlib.decompress(candidate, wbits)
            except zlib.error:
                continue
            if decoded and decoded not in variants:
                variants.append(decoded)

    return variants


def _decode_pdf_stream_with_filters(stream_payload: bytes, filters: list[str]) -> bytes | None:
    decoded = stream_payload
    for filter_name in filters:
        if filter_name == "FlateDecode":
            decoded = _decode_flate(decoded)
        elif filter_name == "ASCII85Decode":
            decoded = _decode_pdf_ascii85(decoded)
        elif filter_name == "ASCIIHexDecode":
            decoded = _decode_pdf_asciihex(decoded)
        else:
            return None

        if decoded is None:
            return None
    return decoded


def _decode_flate(payload: bytes) -> bytes | None:
    for wbits in (None, -15):
        try:
            return zlib.decompress(payload) if wbits is None else zlib.decompress(payload, wbits)
        except zlib.error:
            continue
    return None


def _decode_pdf_ascii85(payload: bytes) -> bytes | None:
    if not payload:
        return None

    for adobe in (True, False):
        try:
            return base64.a85decode(payload, adobe=adobe, ignorechars=b" \t\r\n")
        except (TypeError, ValueError):
            continue
    return None


def _decode_pdf_asciihex(payload: bytes) -> bytes | None:
    if not payload:
        return None

    cleaned = re.sub(rb"\s+", b"", payload)
    if b">" in cleaned:
        cleaned = cleaned.split(b">", 1)[0]
    if not cleaned:
        return b""
    if len(cleaned) % 2 == 1:
        cleaned += b"0"
    try:
        return bytes.fromhex(cleaned.decode("ascii"))
    except ValueError:
        return None


def _build_tounicode_map(stream_texts: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for text in stream_texts:
        lowered = text.lower()
        if "begincmap" not in lowered:
            continue
        _parse_bfchar_blocks(text, mapping)
        _parse_bfrange_blocks(text, mapping)
    return mapping


def _parse_bfchar_blocks(text: str, mapping: dict[str, str]) -> None:
    for block in re.findall(r"\d+\s+beginbfchar(.*?)endbfchar", text, flags=re.DOTALL):
        for src, dst in re.findall(r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            decoded = _decode_cmap_unicode(dst)
            if decoded:
                mapping[src.upper()] = decoded


def _parse_bfrange_blocks(text: str, mapping: dict[str, str]) -> None:
    for block in re.findall(r"\d+\s+beginbfrange(.*?)endbfrange", text, flags=re.DOTALL):
        for src_start, src_end, dst_start in re.findall(
            r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>",
            block,
        ):
            width = len(src_start)
            start = int(src_start, 16)
            end = int(src_end, 16)
            dst = int(dst_start, 16)
            for offset, code in enumerate(range(start, end + 1)):
                value = dst + offset
                if value > 0x10FFFF:
                    continue
                mapping[f"{code:0{width}X}"] = chr(value)

        for src_start, src_end, array_body in re.findall(
            r"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]",
            block,
            flags=re.DOTALL,
        ):
            width = len(src_start)
            start = int(src_start, 16)
            end = int(src_end, 16)
            destinations = re.findall(r"<([0-9A-Fa-f]+)>", array_body)

            for idx, code in enumerate(range(start, end + 1)):
                if idx >= len(destinations):
                    break
                decoded = _decode_cmap_unicode(destinations[idx])
                if decoded:
                    mapping[f"{code:0{width}X}"] = decoded


def _decode_cmap_unicode(value: str) -> str:
    if not value:
        return ""
    if len(value) % 2 == 1:
        value = f"0{value}"
    raw = bytes.fromhex(value)
    if not raw:
        return ""
    for encoding in ("utf-16-be", "utf-8", "latin-1"):
        try:
            decoded = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if decoded:
            return decoded
    return ""


def _extract_pdf_chunks_from_source(source: str, to_unicode_map: dict[str, str]) -> list[str]:
    chunks: list[str] = []

    for block in _PDF_BT_BLOCK_PATTERN.findall(source):
        chunk = _extract_pdf_chunk_from_block(block, to_unicode_map)
        if chunk:
            chunks.append(chunk)

    if chunks:
        return chunks

    for match in _PDF_TEXT_SHOW_PATTERN.finditer(source):
        chunk = _decode_pdf_text_show_match(match, to_unicode_map)
        if chunk:
            chunks.append(chunk)
    return chunks


def _extract_pdf_chunk_from_block(block: str, to_unicode_map: dict[str, str]) -> str:
    parts: list[str] = []

    for match in _PDF_TEXT_SHOW_PATTERN.finditer(block):
        decoded = _decode_pdf_text_show_match(match, to_unicode_map)
        if not decoded:
            continue
        if _text_show_operator(match) in {"'", '"'} and parts:
            parts.append("\n")
        parts.append(decoded)

    return "".join(parts).strip()


def _decode_pdf_text_show_match(match: re.Match[str], to_unicode_map: dict[str, str]) -> str:
    literal = match.group("literal")
    if literal:
        return _decode_pdf_literal(literal[1:-1]).strip()

    hex_value = match.group("hex")
    if hex_value:
        return _decode_pdf_hex(hex_value[1:-1], to_unicode_map).strip()

    array_body = match.group("array")
    if array_body:
        return _decode_pdf_tj_array(array_body, to_unicode_map).strip()

    return ""


def _text_show_operator(match: re.Match[str]) -> str:
    literal_operator = match.group("literal_operator")
    if literal_operator:
        return literal_operator
    hex_operator = match.group("hex_operator")
    if hex_operator:
        return hex_operator
    return "TJ"


def _decode_pdf_tj_array(array_body: str, to_unicode_map: dict[str, str]) -> str:
    parts: list[str] = []
    for token in _PDF_ARRAY_TOKEN_PATTERN.finditer(array_body):
        literal = token.group("literal")
        if literal is not None:
            decoded_literal = _decode_pdf_literal(literal)
            if decoded_literal:
                parts.append(decoded_literal)
            continue

        hex_value = token.group("hex")
        if hex_value:
            decoded_hex = _decode_pdf_hex(hex_value, to_unicode_map)
            if decoded_hex:
                parts.append(decoded_hex)
    return "".join(parts)


def _decode_pdf_hex(value: str, to_unicode_map: dict[str, str]) -> str:
    normalized = "".join(char for char in value if char in "0123456789abcdefABCDEF").upper()
    if not normalized:
        return ""
    if len(normalized) % 2 == 1:
        normalized = f"0{normalized}"

    if to_unicode_map:
        decoded = _decode_pdf_hex_with_cmap(normalized, to_unicode_map)
        if decoded:
            return decoded

    raw = bytes.fromhex(normalized)
    for encoding in ("utf-16-be", "utf-8", "latin-1"):
        try:
            decoded = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if decoded:
            return decoded
    return ""


def _decode_pdf_hex_with_cmap(value: str, to_unicode_map: dict[str, str]) -> str:
    key_lengths = sorted({len(key) for key in to_unicode_map}, reverse=True)
    if not key_lengths:
        return ""

    out: list[str] = []
    cursor = 0
    while cursor < len(value):
        matched = False
        for length in key_lengths:
            candidate = value[cursor : cursor + length]
            if len(candidate) != length:
                continue
            mapped = to_unicode_map.get(candidate)
            if mapped is None:
                continue
            out.append(mapped)
            cursor += length
            matched = True
            break

        if matched:
            continue

        fallback = value[cursor : cursor + 4]
        if len(fallback) == 4:
            try:
                out.append(bytes.fromhex(fallback).decode("utf-16-be"))
                cursor += 4
                continue
            except UnicodeDecodeError:
                pass

        fallback = value[cursor : cursor + 2]
        if len(fallback) == 2:
            out.append(bytes.fromhex(fallback).decode("latin-1", errors="ignore"))
            cursor += 2
            continue

        break

    return "".join(out)


def _extract_docx_text(payload: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            document_xml = archive.read("word/document.xml")
    except (OSError, KeyError, zipfile.BadZipFile) as err:
        raise ResumeParseError("invalid docx payload") from err

    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError as err:
        raise ResumeParseError("unable to parse docx document xml") from err

    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    lines: list[str] = []
    for paragraph in root.findall(".//w:p", namespace):
        text_parts: list[str] = []
        for node in paragraph.findall(".//w:t", namespace):
            if node.text:
                text_parts.append(node.text)
        line = "".join(text_parts).strip()
        if line:
            lines.append(line)

    if not lines:
        raise ResumeParseError("unable to extract text from docx")
    return "\n".join(lines)


def _normalize_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.replace("\r", "\n").split("\n"):
        normalized = re.sub(r"\s+", " ", raw_line).strip()
        if normalized:
            lines.append(normalized)
    return lines


def _map_to_profile(*, lines: list[str], profile_id: str) -> tuple[dict[str, Any], list[str]]:
    header_lines, sections = _split_sections(lines)
    full_name = _extract_full_name(header_lines)
    headline = _extract_headline(header_lines, full_name)

    summary = _extract_summary(sections.get("summary", []))
    skills = _extract_skills(sections.get("skills", []))
    experiences = _extract_experiences(sections.get("experience", []))
    projects = _extract_projects(sections.get("projects", []))
    education = _extract_education(sections.get("education", []))
    inferred_skills = _infer_skills_from_entries(experiences, projects)
    if skills:
        skills = _dedupe_case_preserving([*skills, *inferred_skills])
    else:
        skills = inferred_skills

    if not summary:
        summary = _fallback_summary(header_lines, full_name, headline)

    warnings: list[str] = []
    if not experiences:
        warnings.append("experience section was empty or not detected")
    if not skills:
        warnings.append("skills section was empty or not detected")
    if not education:
        warnings.append("education section was empty or not detected")
    if not projects:
        warnings.append("projects section was empty or not detected")

    profile = {
        "id": profile_id,
        "full_name": full_name,
        "headline": headline,
        "summary": summary,
        "experiences": experiences,
        "projects": projects,
        "skills": skills,
        "education": education,
    }
    return profile, warnings


def _split_sections(lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    header_lines: list[str] = []
    sections: dict[str, list[str]] = {
        "summary": [],
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
    }

    current_section: str | None = None
    for line in lines:
        section = _section_for_line(line)
        if section is not None:
            current_section = section
            continue

        if current_section is None:
            header_lines.append(line)
            continue

        sections[current_section].append(line)

    return header_lines, sections


def _section_for_line(line: str) -> str | None:
    normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
    return _SECTION_HEADERS.get(normalized)


def _extract_full_name(header_lines: list[str]) -> str:
    for line in header_lines:
        labeled_name = _extract_labeled_value(line, {"name"})
        if labeled_name:
            return labeled_name

    for line in header_lines:
        if not _is_name_candidate(line):
            continue
        return line
    return ""


def _extract_headline(header_lines: list[str], full_name: str) -> str | None:
    for line in header_lines:
        labeled_headline = _extract_labeled_value(line, _HEADLINE_LABELS)
        if labeled_headline:
            return labeled_headline

    for line in header_lines:
        if line == full_name or _looks_like_contact(line):
            continue
        if _is_header_metadata_line(line) or _looks_like_location(line):
            continue
        if _section_for_line(line) is not None:
            continue
        if len(line) <= 120 and any(ch.isalpha() for ch in line):
            return line
    return None


def _looks_like_contact(line: str) -> bool:
    lowered = line.lower()
    if "@" in lowered or "http://" in lowered or "https://" in lowered:
        return True
    if "linkedin.com" in lowered or "github.com" in lowered:
        return True
    if re.search(r"\+?\d[\d(). -]{7,}\d", line):
        return True
    if _is_header_metadata_line(line):
        return True
    return False


def _is_header_metadata_line(line: str) -> bool:
    lower = line.lower()
    return any(lower.startswith(f"{label}:") for label in _HEADER_METADATA_LABELS)


def _looks_like_location(line: str) -> bool:
    cleaned = line.strip()
    if not cleaned:
        return False
    if cleaned.lower() in {"remote", "remote, us", "united states"}:
        return True
    if re.fullmatch(r"[A-Za-z .'-]+,\s*[A-Z]{2}", cleaned):
        return True
    if re.fullmatch(r"[A-Za-z .'-]+,\s*[A-Za-z .'-]+", cleaned) and len(cleaned.split()) <= 4:
        return True
    return False


def _extract_labeled_value(line: str, labels: set[str]) -> str:
    if ":" not in line:
        return ""
    label_raw, value = line.split(":", 1)
    normalized_label = re.sub(r"[^a-z ]", "", label_raw.lower()).strip()
    if normalized_label not in labels:
        return ""
    normalized_value = value.strip()
    return normalized_value if normalized_value else ""


def _is_name_candidate(line: str) -> bool:
    if _looks_like_contact(line) or _looks_like_location(line):
        return False
    if _section_for_line(line) is not None:
        return False
    lowered = line.lower().strip()
    if lowered in _NAME_BLACKLIST:
        return False
    if any(ch.isdigit() for ch in line):
        return False
    words = [word for word in line.split() if word.strip()]
    if not 1 <= len(words) <= 6:
        return False
    if line.strip() == line.strip().lower():
        return False
    return any(ch.isalpha() for ch in line)


def _extract_summary(lines: list[str]) -> str | None:
    if not lines:
        return None
    pieces = [_strip_bullet(line) for line in lines if _strip_bullet(line)]
    if not pieces:
        return None
    return " ".join(pieces[:3])


def _fallback_summary(header_lines: list[str], full_name: str, headline: str | None) -> str | None:
    candidates = [line for line in header_lines if not _looks_like_contact(line)]
    candidates = [line for line in candidates if line != full_name and line != headline]
    if not candidates:
        return None
    return " ".join(candidates[:2])


def _extract_skills(lines: list[str]) -> list[str]:
    tokens: list[str] = []
    for line in lines:
        cleaned = _strip_bullet(line)
        if not cleaned:
            continue
        segments = [segment.strip() for segment in cleaned.split(";") if segment.strip()]
        if not segments:
            segments = [cleaned]

        pieces: list[str] = []
        for segment in segments:
            if ":" in segment:
                _, segment = segment.split(":", 1)
            pieces.extend(part.strip() for part in re.split(r"[,|/]", segment) if part.strip())
        if not pieces and cleaned:
            pieces = [cleaned]
        tokens.extend(piece for piece in pieces if len(piece) <= 64)

    if not tokens:
        return []
    return _dedupe_case_preserving(tokens)


def _extract_experiences(lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    counter = 1

    for line in lines:
        if _is_bullet_line(line):
            if current is None:
                current = _new_experience(counter, "Unknown", "Unknown", "", None)
                counter += 1
            current["bullets"].append(_strip_bullet(line))
            continue

        if current is not None and _is_date_only_line(line):
            start_date, end_date = _extract_date_range(line)
            if start_date:
                current["start_date"] = start_date
            current["end_date"] = end_date
            continue

        parsed_heading = _parse_heading_line(line)
        if parsed_heading is not None:
            if current is not None:
                current["skills"] = _infer_skills(current["bullets"])
                entries.append(current)
            current = _new_experience(
                counter,
                parsed_heading["company"],
                parsed_heading["title"],
                parsed_heading["start_date"],
                parsed_heading["end_date"],
            )
            counter += 1
            continue

        if current is None:
            current = _new_experience(counter, line, "Contributor", "", None)
            counter += 1
        else:
            current["bullets"].append(_strip_bullet(line))

    if current is not None:
        current["skills"] = _infer_skills(current["bullets"])
        entries.append(current)

    return entries


def _new_experience(
    entry_number: int,
    company: str,
    title: str,
    start_date: str,
    end_date: str | None,
) -> dict[str, Any]:
    return {
        "id": f"exp-{entry_number}",
        "company": company,
        "title": title,
        "start_date": start_date,
        "end_date": end_date,
        "bullets": [],
        "skills": [],
    }


def _parse_heading_line(line: str) -> dict[str, str | None] | None:
    start_date, end_date = _extract_date_range(line)
    line_without_dates = _DATE_RANGE_PATTERN.sub("", line).strip(" |-\u2013\u2014")

    parsed_title_company = _parse_title_company(line_without_dates)
    if parsed_title_company is not None:
        return {
            "title": parsed_title_company["title"],
            "company": parsed_title_company["company"],
            "start_date": start_date,
            "end_date": end_date,
        }
    return None


def _parse_title_company(value: str) -> dict[str, str] | None:
    if "|" in value:
        parts = [part.strip() for part in value.split("|") if part.strip()]
        if len(parts) >= 2:
            return _pair_to_title_company(parts[0], parts[1])

    for pattern in (r"\s+at\s+", r"\s+@\s+"):
        split = re.split(pattern, value, maxsplit=1, flags=re.IGNORECASE)
        if len(split) == 2:
            return _pair_to_title_company(split[0], split[1])

    for separator_pattern in (r"\s+[,\u2013\u2014-]\s+", r",\s*"):
        split = re.split(separator_pattern, value, maxsplit=1)
        if len(split) == 2:
            return _pair_to_title_company(split[0], split[1])

    return None


def _pair_to_title_company(first: str, second: str) -> dict[str, str] | None:
    first = first.strip(" ,|")
    second = second.strip(" ,|")
    if not first or not second:
        return None

    first_is_title = _looks_like_title(first)
    second_is_title = _looks_like_title(second)
    if second_is_title and not first_is_title:
        return {"title": second, "company": first}
    return {"title": first, "company": second}


def _looks_like_title(value: str) -> bool:
    return bool(_TITLE_HINT_PATTERN.search(value))


def _is_date_only_line(line: str) -> bool:
    start_date, _ = _extract_date_range(line)
    if not start_date:
        return False
    without_dates = _DATE_RANGE_PATTERN.sub("", line).strip(" |-\u2013\u2014")
    return not without_dates


def _extract_projects(lines: list[str]) -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    counter = 1

    for line in lines:
        cleaned = _strip_bullet(line)
        if _is_bullet_line(line):
            if current is None:
                current = _new_project(counter, "Untitled Project", "")
                counter += 1
            current["bullets"].append(cleaned)
            continue

        if "|" in cleaned:
            name, description = [piece.strip() for piece in cleaned.split("|", 1)]
            if current is not None:
                current["skills"] = _infer_skills([current["description"], *current["bullets"]])
                projects.append(current)
            current = _new_project(counter, name, description)
            counter += 1
            continue

        if current is None:
            current = _new_project(counter, cleaned, "")
            counter += 1
            continue

        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            current["url"] = cleaned
        elif not current["description"]:
            current["description"] = cleaned
        else:
            current["bullets"].append(cleaned)

    if current is not None:
        current["skills"] = _infer_skills([current["description"], *current["bullets"]])
        projects.append(current)

    return projects


def _new_project(entry_number: int, name: str, description: str) -> dict[str, Any]:
    return {
        "id": f"proj-{entry_number}",
        "name": name,
        "description": description,
        "bullets": [],
        "skills": [],
        "url": None,
    }


def _extract_education(lines: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    counter = 1

    for line in lines:
        cleaned = _strip_bullet(line)
        if not cleaned:
            continue

        start_date, end_date = _extract_date_range(cleaned)
        details = _DATE_RANGE_PATTERN.sub("", cleaned).strip(" |-")
        parts = [piece.strip() for piece in re.split(r"[|,]", details) if piece.strip()]

        school = parts[0] if parts else details
        degree = parts[1] if len(parts) > 1 else ""
        field = parts[2] if len(parts) > 2 else None

        entries.append(
            {
                "id": f"edu-{counter}",
                "school": school,
                "degree": degree,
                "field": field,
                "start_date": start_date or None,
                "end_date": end_date,
            }
        )
        counter += 1

    return entries


def _extract_date_range(value: str) -> tuple[str, str | None]:
    match = _DATE_RANGE_PATTERN.search(value)
    if match is None:
        return "", None

    start = _normalize_date(match.group("start"))
    end_raw = match.group("end").strip()
    end = None if end_raw.lower() in {"present", "current", "now"} else _normalize_date(end_raw)
    return start, end


def _normalize_date(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"\d{4}", value):
        return f"{value}-01-01"

    slash_match = re.fullmatch(r"(\d{1,2})/(\d{4})", value)
    if slash_match:
        month = int(slash_match.group(1))
        year = slash_match.group(2)
        if 1 <= month <= 12:
            return f"{year}-{month:02d}-01"

    parts = value.split()
    if len(parts) == 2 and parts[1].isdigit():
        month = _MONTH_TO_NUM.get(parts[0].lower()[:3], "01")
        return f"{parts[1]}-{month}-01"
    return ""


def _infer_skills(lines: list[str]) -> list[str]:
    found: list[str] = []
    for line in lines:
        for keyword in _SKILL_KEYWORDS:
            if re.search(rf"\b{re.escape(keyword)}\b", line, flags=re.IGNORECASE):
                found.append(keyword)
    return _dedupe_case_preserving(found)


def _infer_skills_from_entries(experiences: list[dict[str, Any]], projects: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for experience in experiences:
        lines.extend(experience.get("bullets", []))
    for project in projects:
        if project.get("description"):
            lines.append(str(project["description"]))
        lines.extend(project.get("bullets", []))
    return _infer_skills(lines)


def _dedupe_case_preserving(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(normalized)
    return out


def _is_bullet_line(line: str) -> bool:
    return bool(_BULLET_PATTERN.match(line))


def _strip_bullet(line: str) -> str:
    return _BULLET_PATTERN.sub("", line).strip()


def _validate_profile(profile: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if not isinstance(profile.get("id"), str) or not str(profile["id"]).strip():
        errors.append({"field": "profile.id", "message": "must be a non-empty string"})

    full_name = profile.get("full_name")
    if not isinstance(full_name, str) or not full_name.strip():
        errors.append({"field": "profile.full_name", "message": "is required"})

    if not any(
        [
            bool(profile.get("summary")),
            bool(profile.get("experiences")),
            bool(profile.get("projects")),
            bool(profile.get("skills")),
            bool(profile.get("education")),
        ]
    ):
        errors.append({"field": "profile", "message": "no structured profile content was parsed"})

    for index, experience in enumerate(profile.get("experiences", [])):
        if not isinstance(experience, dict):
            errors.append({"field": f"profile.experiences[{index}]", "message": "must be an object"})
            continue
        if not isinstance(experience.get("company"), str) or not str(experience["company"]).strip():
            errors.append(
                {
                    "field": f"profile.experiences[{index}].company",
                    "message": "is required",
                }
            )
        if not isinstance(experience.get("title"), str) or not str(experience["title"]).strip():
            errors.append(
                {
                    "field": f"profile.experiences[{index}].title",
                    "message": "is required",
                }
            )
        bullets = experience.get("bullets")
        if not isinstance(bullets, list) or any(not isinstance(item, str) for item in bullets):
            errors.append(
                {
                    "field": f"profile.experiences[{index}].bullets",
                    "message": "must be an array of strings",
                }
            )

    return errors
