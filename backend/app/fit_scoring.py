from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re
from typing import Any

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "years",
    "year",
}


def _tokenize(text: str) -> set[str]:
    return {token for token in _TOKEN_RE.findall(text.lower()) if token not in _STOPWORDS}


def _normalize_phrase(value: str) -> str:
    return " ".join(value.strip().split())


def _read_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        normalized = _normalize_phrase(item)
        if normalized:
            out.append(normalized)
    return out


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _ratio(matched: int, total: int) -> float:
    if total <= 0:
        return 1.0
    return round(matched / total, 4)


def _is_supported_phrase(phrase: str, profile_tokens: set[str]) -> bool:
    phrase_tokens = [token for token in _tokenize(phrase) if not token.isdigit()]
    if not phrase_tokens:
        return False
    required_hits = 1 if len(phrase_tokens) == 1 else max(1, math.ceil(len(phrase_tokens) * 0.6))
    matched = sum(1 for token in phrase_tokens if token in profile_tokens)
    return matched >= required_hits


def _collect_profile_tokens(profile: dict[str, Any]) -> set[str]:
    fragments: list[str] = []
    for key in ("full_name", "headline", "summary"):
        value = profile.get(key)
        if isinstance(value, str):
            fragments.append(value)

    fragments.extend(_read_string_list(profile.get("skills")))

    for item in profile.get("experiences", []):
        if not isinstance(item, dict):
            continue
        for key in ("company", "title"):
            value = item.get(key)
            if isinstance(value, str):
                fragments.append(value)
        fragments.extend(_read_string_list(item.get("skills")))
        fragments.extend(_read_string_list(item.get("bullets")))

    for item in profile.get("projects", []):
        if not isinstance(item, dict):
            continue
        for key in ("name", "description"):
            value = item.get(key)
            if isinstance(value, str):
                fragments.append(value)
        fragments.extend(_read_string_list(item.get("skills")))
        fragments.extend(_read_string_list(item.get("bullets")))

    for item in profile.get("education", []):
        if not isinstance(item, dict):
            continue
        for key in ("school", "degree", "field"):
            value = item.get(key)
            if isinstance(value, str):
                fragments.append(value)

    tokens: set[str] = set()
    for fragment in fragments:
        tokens.update(_tokenize(fragment))
    return tokens


def _collect_job_inputs(job_posting: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    structured = job_posting.get("structured_json")
    if not isinstance(structured, dict):
        return [], [], []

    requirements = _dedupe_keep_order(
        _read_string_list(structured.get("requirements")) + _read_string_list(structured.get("tech_stack"))
    )
    preferred = _dedupe_keep_order(_read_string_list(structured.get("preferred_qualifications")))
    keywords = _dedupe_keep_order(_read_string_list(structured.get("keywords")))

    return requirements, preferred, keywords


@dataclass(frozen=True)
class CoverageSummary:
    matched: int
    total: int
    ratio: float


@dataclass(frozen=True)
class GapItem:
    category: str
    item: str
    severity: str
    reason: str


@dataclass(frozen=True)
class FitAnalysis:
    score: float | None
    coverage: dict[str, CoverageSummary]
    matched_requirements: list[str]
    missing_requirements: list[str]
    matched_preferred: list[str]
    missing_preferred: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    gaps: list[GapItem]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "coverage": {key: asdict(value) for key, value in self.coverage.items()},
            "matched_requirements": self.matched_requirements,
            "missing_requirements": self.missing_requirements,
            "matched_preferred": self.matched_preferred,
            "missing_preferred": self.missing_preferred,
            "matched_keywords": self.matched_keywords,
            "missing_keywords": self.missing_keywords,
            "gaps": [asdict(item) for item in self.gaps],
            "notes": self.notes,
        }


class FitScoringEngine:
    def evaluate(self, *, profile: dict[str, Any] | None, job_posting: dict[str, Any]) -> dict[str, Any]:
        requirements, preferred, keywords = _collect_job_inputs(job_posting)
        profile_tokens = _collect_profile_tokens(profile) if isinstance(profile, dict) else set()
        profile_available = len(profile_tokens) > 0

        matched_requirements, missing_requirements = self._partition(requirements, profile_tokens)
        matched_preferred, missing_preferred = self._partition(preferred, profile_tokens)
        matched_keywords, missing_keywords = self._partition(keywords, profile_tokens)

        coverage = {
            "requirements": CoverageSummary(
                matched=len(matched_requirements),
                total=len(requirements),
                ratio=_ratio(len(matched_requirements), len(requirements)),
            ),
            "preferred": CoverageSummary(
                matched=len(matched_preferred),
                total=len(preferred),
                ratio=_ratio(len(matched_preferred), len(preferred)),
            ),
            "keywords": CoverageSummary(
                matched=len(matched_keywords),
                total=len(keywords),
                ratio=_ratio(len(matched_keywords), len(keywords)),
            ),
        }

        score: float | None
        notes: list[str] = []
        if not profile_available:
            score = None
            notes.append("Profile data is unavailable, so fit score is not computed.")
        else:
            weighted = (
                coverage["requirements"].ratio * 0.6
                + coverage["keywords"].ratio * 0.25
                + coverage["preferred"].ratio * 0.15
            )
            score = round(weighted * 100, 2)

        gaps = self._build_gap_items(
            profile_available=profile_available,
            missing_requirements=missing_requirements,
            missing_preferred=missing_preferred,
            missing_keywords=missing_keywords,
        )

        return FitAnalysis(
            score=score,
            coverage=coverage,
            matched_requirements=matched_requirements,
            missing_requirements=missing_requirements,
            matched_preferred=matched_preferred,
            missing_preferred=missing_preferred,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            gaps=gaps,
            notes=notes,
        ).to_dict()

    def _partition(self, values: list[str], profile_tokens: set[str]) -> tuple[list[str], list[str]]:
        matched: list[str] = []
        missing: list[str] = []
        for value in values:
            if _is_supported_phrase(value, profile_tokens):
                matched.append(value)
            else:
                missing.append(value)
        return matched, missing

    def _build_gap_items(
        self,
        *,
        profile_available: bool,
        missing_requirements: list[str],
        missing_preferred: list[str],
        missing_keywords: list[str],
    ) -> list[GapItem]:
        out: list[GapItem] = []
        if not profile_available:
            out.append(
                GapItem(
                    category="profile",
                    item="Profile evidence",
                    severity="high",
                    reason="Complete profile skills and experience before evaluating fit.",
                )
            )

        out.extend(
            GapItem(
                category="requirement",
                item=item,
                severity="high",
                reason="No direct evidence found in profile experience, projects, or skills.",
            )
            for item in missing_requirements
        )
        out.extend(
            GapItem(
                category="preferred",
                item=item,
                severity="medium",
                reason="Preferred qualification is currently unsupported by profile evidence.",
            )
            for item in missing_preferred
        )
        out.extend(
            GapItem(
                category="keyword",
                item=item,
                severity="medium",
                reason="Keyword appears in the posting but is not reflected in profile evidence.",
            )
            for item in missing_keywords
        )
        return out
