from __future__ import annotations

from autoapply.contracts import GenerateResumeRequest
from autoapply.repositories import NotFoundError
from autoapply.service import ResumeGenerationService

try:
    from fastapi import FastAPI, HTTPException
except ImportError:  # pragma: no cover - optional runtime dependency.
    FastAPI = None  # type: ignore[assignment]
    HTTPException = None  # type: ignore[assignment]


def create_app(service: ResumeGenerationService):
    if FastAPI is None:
        raise RuntimeError("fastapi is required to run the HTTP endpoint")

    app = FastAPI()

    @app.post("/api/v1/applications/{application_id}/resume-versions/generate", status_code=201)
    def generate_resume_version(application_id: str, request: GenerateResumeRequest):
        try:
            outcome = service.generate_resume_version(application_id, request)
        except NotFoundError as err:
            raise HTTPException(status_code=404, detail=str(err)) from err

        if outcome.status_code == 422:
            raise HTTPException(
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

    return app
