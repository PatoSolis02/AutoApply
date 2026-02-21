from __future__ import annotations

from dataclasses import dataclass

from autoapply.contracts import GenerateResumeRequest
from autoapply.repositories import NotFoundError
from autoapply.service import ResumeGenerationService

try:
    from fastapi import FastAPI, HTTPException
except ImportError:  # pragma: no cover - optional runtime dependency.
    FastAPI = None  # type: ignore[assignment]
    HTTPException = None  # type: ignore[assignment]


@dataclass(frozen=True)
class ApiError(Exception):
    status_code: int
    detail: object


def handle_generate_resume_version(
    service: ResumeGenerationService,
    application_id: str,
    request: GenerateResumeRequest,
) -> dict:
    try:
        outcome = service.generate_resume_version(application_id, request)
    except NotFoundError as err:
        raise ApiError(status_code=404, detail=str(err)) from err

    if outcome.status_code == 422:
        raise ApiError(
            status_code=422,
            detail={
                "warnings": outcome.result.warnings,
                "blocked_reasons": outcome.result.blocked_reasons,
            },
        )

    return {
        "resume_version_id": outcome.result.resume_version_id,
        "warnings": outcome.result.warnings,
        "blocked_reasons": outcome.result.blocked_reasons,
    }


def create_app(service: ResumeGenerationService):
    if FastAPI is None:
        raise RuntimeError("fastapi is required to run the HTTP endpoint")

    app = FastAPI()

    @app.post("/api/v1/applications/{application_id}/resume-versions/generate", status_code=201)
    def generate_resume_version(application_id: str, request: GenerateResumeRequest):
        try:
            return handle_generate_resume_version(service, application_id, request)
        except ApiError as err:
            raise HTTPException(status_code=err.status_code, detail=err.detail) from err

    return app
