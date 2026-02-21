from __future__ import annotations

from autoapply.contracts import (
    Application,
    EducationEntry,
    ExperienceEntry,
    JobPosting,
    JobStructured,
    ProjectEntry,
    UserProfile,
)


def sample_application() -> Application:
    return Application(
        id="app-1",
        company="Acme Corp",
        role_title="Backend Engineer",
        job_url="https://example.com/job/1",
        job_source="linkedin",
        location="Remote",
        status="drafting",
        notes="",
        fit_score=None,
        created_at="2026-02-20T00:00:00Z",
        updated_at="2026-02-20T00:00:00Z",
    )


def sample_job_posting(application_id: str = "app-1") -> JobPosting:
    return JobPosting(
        id="job-1",
        application_id=application_id,
        raw_text="Build APIs with Python and SQLite for reporting and automation.",
        structured_json=JobStructured(
            summary="Backend engineering role with Python and SQL.",
            responsibilities=[
                "Build and maintain API services",
                "Improve observability and data pipelines",
            ],
            requirements=[
                "3+ years Python",
                "Experience with SQL databases",
                "REST API design",
            ],
            preferred_qualifications=["FastAPI", "CI/CD"],
            tech_stack=["Python", "SQLite", "FastAPI", "GitHub Actions"],
            employment_type="full_time",
            seniority="mid",
            keywords=["python", "api", "sql", "fastapi", "observability"],
        ),
        captured_at="2026-02-20T00:00:00Z",
    )


def sample_user_profile() -> UserProfile:
    return UserProfile(
        id="profile-1",
        full_name="Taylor Dev",
        headline="Backend Software Engineer",
        summary="Engineer focused on Python APIs and data reliability.",
        experiences=[
            ExperienceEntry(
                id="exp-1",
                company="DataCo",
                title="Software Engineer",
                start_date="2021-01-01",
                end_date=None,
                bullets=[
                    "Built Python APIs for internal analytics workloads.",
                    "Designed SQL data models for reporting.",
                    "Led incident response and observability improvements.",
                ],
                skills=["Python", "SQL", "API", "Observability"],
            ),
            ExperienceEntry(
                id="exp-2",
                company="Legacy Inc",
                title="Developer",
                start_date="2018-01-01",
                end_date="2020-12-31",
                bullets=[
                    "Maintained Java desktop tooling.",
                    "Authored internal documentation.",
                ],
                skills=["Java", "Docs"],
            ),
        ],
        projects=[
            ProjectEntry(
                id="proj-1",
                name="Resume Pipeline",
                description="A Python project that renders documents.",
                bullets=[
                    "Implemented a deterministic rendering pipeline.",
                    "Generated PDFs from structured resume data.",
                ],
                skills=["Python", "PDF", "Rendering"],
                url=None,
            ),
            ProjectEntry(
                id="proj-2",
                name="Game Mod",
                description="Weekend project in Lua.",
                bullets=["Implemented scripting hooks in Lua."],
                skills=["Lua"],
                url=None,
            ),
        ],
        skills=["Python", "SQL", "FastAPI", "Docker", "Observability", "Lua"],
        education=[
            EducationEntry(
                id="edu-1",
                school="RIT",
                degree="BS",
                field="Computer Science",
                start_date="2014-09-01",
                end_date="2018-05-01",
            )
        ],
        updated_at="2026-02-20T00:00:00Z",
    )
