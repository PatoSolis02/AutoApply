from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

CONTRACT_VERSION = "resume_parse.v1"

_SECTION_HEADERS = {
    "summary": "summary",
    "professional summary": "summary",
    "profile": "summary",
    "skills": "skills",
    "technical skills": "skills",
    "core skills": "skills",
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment": "experience",
    "projects": "projects",
    "selected projects": "projects",
    "education": "education",
    "academic background": "education",
}
_SUPPORTED_FILE_TYPES = {"pdf", "docx"}
_DATE_RANGE_PATTERN = re.compile(
    r"(?P<start>(?:[A-Za-z]{3,9}\s+\d{4}|\d{4}))\s*[-]\s*(?P<end>(?:present|current|now|[A-Za-z]{3,9}\s+\d{4}|\d{4}))",
    flags=re.IGNORECASE,
)
_BULLET_PATTERN = re.compile(r"^[-*]\s+")
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
) -> dict[str, Any]:
    file_type = _detect_file_type(filename, content_type)
    text = _extract_text(file_type, payload)
    lines = _normalize_lines(text)
    profile, warnings = _map_to_profile(lines=lines, profile_id=profile_id)
    errors = _validate_profile(profile)
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
        "profile": profile,
        "warnings": warnings,
    }


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

    decoded = payload.decode("latin-1", errors="ignore")
    chunks: list[str] = []

    for match in re.finditer(r"\((.*?)\)\s*Tj", decoded, flags=re.DOTALL):
        text = _decode_pdf_literal(match.group(1))
        if text.strip():
            chunks.append(text.strip())

    for match in re.finditer(r"\[(.*?)\]\s*TJ", decoded, flags=re.DOTALL):
        pieces = re.findall(r"\((.*?)\)", match.group(1), flags=re.DOTALL)
        combined = "".join(_decode_pdf_literal(piece) for piece in pieces).strip()
        if combined:
            chunks.append(combined)

    if not chunks:
        raise ResumeParseError("unable to extract text from pdf")
    return "\n".join(chunks)


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
        if _looks_like_contact(line):
            continue
        if any(ch.isdigit() for ch in line):
            continue
        if 1 <= len(line.split()) <= 6:
            return line
    return ""


def _extract_headline(header_lines: list[str], full_name: str) -> str | None:
    for line in header_lines:
        if line == full_name or _looks_like_contact(line):
            continue
        if len(line) <= 120:
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
    return False


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
        if ":" in cleaned:
            _, cleaned = cleaned.split(":", 1)
        pieces = [part.strip() for part in re.split(r"[,|/]", cleaned) if part.strip()]
        if not pieces and cleaned:
            pieces = [cleaned]
        tokens.extend(pieces)

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
    line_without_dates = _DATE_RANGE_PATTERN.sub("", line).strip(" |-")

    if "|" in line_without_dates:
        parts = [part.strip() for part in line_without_dates.split("|") if part.strip()]
        if len(parts) >= 2:
            return {
                "title": parts[0],
                "company": parts[1],
                "start_date": start_date,
                "end_date": end_date,
            }
    if " at " in line_without_dates.lower():
        title, company = re.split(r"\s+at\s+", line_without_dates, maxsplit=1, flags=re.IGNORECASE)
        return {
            "title": title.strip(),
            "company": company.strip(),
            "start_date": start_date,
            "end_date": end_date,
        }
    return None


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
