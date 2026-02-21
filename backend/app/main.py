from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional, Union

from .db import CaptureDatabase
from .ingest import build_structured_job_posting
from .schemas import validate_capture_payload

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "autoapply.db"



def _json_response(handler: BaseHTTPRequestHandler, status: int, body: dict[str, Any]) -> None:
    payload = json.dumps(body).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)



def _build_handler(capture_db: CaptureDatabase):
    class CaptureRequestHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/api/v1/jobs/capture":
                _json_response(self, HTTPStatus.NOT_FOUND, {"detail": "not found"})
                return

            content_length = self.headers.get("Content-Length", "0")
            try:
                length = int(content_length)
            except ValueError:
                _json_response(self, HTTPStatus.BAD_REQUEST, {"detail": "invalid request payload"})
                return

            raw_body = self.rfile.read(length)
            try:
                body = json.loads(raw_body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {"detail": "invalid request payload", "errors": [{"field": "body", "message": "invalid JSON"}]},
                )
                return

            capture, errors = validate_capture_payload(body)
            if capture is None:
                _json_response(
                    self,
                    HTTPStatus.BAD_REQUEST,
                    {"detail": "invalid request payload", "errors": errors},
                )
                return

            structured = build_structured_job_posting(capture.description_raw)
            application_id, job_posting_id = capture_db.insert_capture(
                title=capture.title,
                company=capture.company,
                location=capture.location,
                job_url=capture.job_url,
                description_raw=capture.description_raw,
                captured_at=capture.captured_at,
                structured_json=structured,
            )

            _json_response(
                self,
                HTTPStatus.CREATED,
                {
                    "application_id": application_id,
                    "job_posting_id": job_posting_id,
                },
            )

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    return CaptureRequestHandler



def create_server(
    db_path: Optional[Union[str, Path]] = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> ThreadingHTTPServer:
    db = CaptureDatabase(db_path or DEFAULT_DB_PATH)
    db.init_schema()
    return ThreadingHTTPServer((host, port), _build_handler(db))



def run_server(
    db_path: Optional[Union[str, Path]] = None,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    server = create_server(db_path=db_path, host=host, port=port)
    server.serve_forever()


if __name__ == "__main__":
    env_port = int(os.environ.get("AUTOAPPLY_API_PORT", "8000"))
    run_server(port=env_port)
