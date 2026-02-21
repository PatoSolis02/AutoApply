from __future__ import annotations

import re
from dataclasses import dataclass

from autoapply.contracts import (
    ExperienceEntry,
    JobPosting,
    ProjectEntry,
    RenderBullet,
    RenderModel,
    RenderSectionEntry,
    UserProfile,
)

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.lower().strip()
        if key and key not in seen:
            out.append(value)
            seen.add(key)
    return out


@dataclass(frozen=True)
class TailoringConfig:
    max_experiences: int = 3
    max_projects: int = 2
    max_bullets_per_entry: int = 3
    max_skill_keywords: int = 12


class TailoringEngine:
    def __init__(self, config: TailoringConfig | None = None) -> None:
        self._config = config or TailoringConfig()

    def build_render_model(self, profile: UserProfile, job_posting: JobPosting) -> RenderModel:
        job_terms = self._job_terms(job_posting)

        selected_experience = self._select_experiences(profile.experiences, job_terms)
        selected_projects = self._select_projects(profile.projects, job_terms)

        exp_sections = [
            RenderSectionEntry(
                entry_id=entry.id,
                bullets=self._select_entry_bullets(
                    bullets=entry.bullets,
                    source_type="experience",
                    entry_id=entry.id,
                    job_terms=job_terms,
                ),
            )
            for entry in selected_experience
        ]

        project_sections = [
            RenderSectionEntry(
                entry_id=entry.id,
                bullets=self._select_entry_bullets(
                    bullets=entry.bullets,
                    source_type="project",
                    entry_id=entry.id,
                    job_terms=job_terms,
                ),
            )
            for entry in selected_projects
        ]

        headline = (profile.headline or "").strip()
        if not headline:
            headline = (profile.full_name or "").strip()

        summary = (profile.summary or "").strip()

        return RenderModel(
            headline=headline,
            summary=summary,
            selected_experience_ids=[entry.id for entry in selected_experience],
            selected_project_ids=[entry.id for entry in selected_projects],
            selected_skill_keywords=self._select_skills(profile.skills, job_terms),
            sections={
                "experience": exp_sections,
                "projects": project_sections,
            },
        )

    def _job_terms(self, job_posting: JobPosting) -> set[str]:
        values: list[str] = []
        structured = job_posting.structured_json
        values.extend(structured.keywords)
        values.extend(structured.tech_stack)
        values.extend(structured.requirements)
        values.extend(structured.preferred_qualifications)
        values.extend(structured.responsibilities)
        if structured.summary:
            values.append(structured.summary)

        tokens: set[str] = set()
        for value in values:
            tokens.update(_tokens(value))
        return tokens

    def _score_experience(self, entry: ExperienceEntry, job_terms: set[str]) -> int:
        text_bits = [entry.company, entry.title] + entry.bullets + entry.skills
        score = 0
        for piece in text_bits:
            score += len(_tokens(piece) & job_terms)
        return score

    def _score_project(self, entry: ProjectEntry, job_terms: set[str]) -> int:
        text_bits = [entry.name, entry.description] + entry.bullets + entry.skills
        score = 0
        for piece in text_bits:
            score += len(_tokens(piece) & job_terms)
        return score

    def _select_experiences(self, entries: list[ExperienceEntry], job_terms: set[str]) -> list[ExperienceEntry]:
        scored = [
            (self._score_experience(entry, job_terms), entry.start_date, entry.id, entry)
            for entry in entries
        ]
        scored.sort(key=lambda row: (-row[0], row[1], row[2]))

        selected = [row[3] for row in scored[: self._config.max_experiences]]
        if not selected:
            return []
        return selected

    def _select_projects(self, entries: list[ProjectEntry], job_terms: set[str]) -> list[ProjectEntry]:
        scored = [(self._score_project(entry, job_terms), entry.id, entry) for entry in entries]
        scored.sort(key=lambda row: (-row[0], row[1]))
        return [row[2] for row in scored[: self._config.max_projects]]

    def _select_entry_bullets(
        self,
        bullets: list[str],
        source_type: str,
        entry_id: str,
        job_terms: set[str],
    ) -> list[RenderBullet]:
        scored: list[tuple[int, int, str]] = []
        for idx, bullet in enumerate(bullets):
            score = len(_tokens(bullet) & job_terms)
            scored.append((score, idx, bullet))

        scored.sort(key=lambda row: (-row[0], row[1]))
        chosen = scored[: self._config.max_bullets_per_entry]

        out: list[RenderBullet] = []
        for score, idx, bullet in chosen:
            if score == 0 and len(out) > 0:
                continue
            out.append(RenderBullet(id=f"{source_type}:{entry_id}:{idx}", text=bullet))

        if not out and bullets:
            out.append(RenderBullet(id=f"{source_type}:{entry_id}:0", text=bullets[0]))

        return out

    def _select_skills(self, profile_skills: list[str], job_terms: set[str]) -> list[str]:
        matched: list[str] = []
        for skill in profile_skills:
            if _tokens(skill) & job_terms:
                matched.append(skill)
        if not matched:
            matched = list(profile_skills)
        return _dedupe_keep_order(matched)[: self._config.max_skill_keywords]
