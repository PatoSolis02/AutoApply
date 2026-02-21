from __future__ import annotations

from dataclasses import dataclass, field

from autoapply.contracts import Application, JobPosting, ResumeVersion, UserProfile


class RepositoryError(Exception):
    """Base repository exception."""


class NotFoundError(RepositoryError):
    """Raised when a referenced entity does not exist."""


class GenerateRepository:
    """WS-C read/write contract needed by generation pipeline."""

    def get_application(self, application_id: str) -> Application:
        raise NotImplementedError

    def get_job_posting_for_application(self, application_id: str) -> JobPosting:
        raise NotImplementedError

    def get_user_profile(self) -> UserProfile:
        raise NotImplementedError

    def get_resume_versions_for_application(self, application_id: str) -> list[ResumeVersion]:
        raise NotImplementedError

    def save_resume_version(self, resume_version: ResumeVersion) -> None:
        raise NotImplementedError


@dataclass
class InMemoryGenerateRepository(GenerateRepository):
    applications: dict[str, Application]
    job_postings_by_app_id: dict[str, JobPosting]
    user_profile: UserProfile
    resume_versions_by_app_id: dict[str, list[ResumeVersion]] = field(default_factory=dict)

    def get_application(self, application_id: str) -> Application:
        app = self.applications.get(application_id)
        if app is None:
            raise NotFoundError(f"application '{application_id}' not found")
        return app

    def get_job_posting_for_application(self, application_id: str) -> JobPosting:
        posting = self.job_postings_by_app_id.get(application_id)
        if posting is None:
            raise NotFoundError(f"job posting for application '{application_id}' not found")
        return posting

    def get_user_profile(self) -> UserProfile:
        return self.user_profile

    def get_resume_versions_for_application(self, application_id: str) -> list[ResumeVersion]:
        return list(self.resume_versions_by_app_id.get(application_id, []))

    def save_resume_version(self, resume_version: ResumeVersion) -> None:
        self.resume_versions_by_app_id.setdefault(resume_version.application_id, []).append(resume_version)
