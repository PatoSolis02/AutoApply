from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
from uuid import uuid4


class CaptureDatabase:
    def __init__(self, db_path: Union[str, Path]):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_schema(self) -> None:
        migration_path = Path(__file__).resolve().parent.parent / "migrations" / "0001_capture_tables.sql"
        sql = migration_path.read_text(encoding="utf-8")
        with self.connect() as conn:
            conn.executescript(sql)
            conn.commit()

    def insert_capture(
        self,
        *,
        title: str,
        company: str,
        location: Optional[str],
        job_url: str,
        description_raw: str,
        captured_at: str,
        structured_json: Dict[str, object],
    ) -> Tuple[str, str]:
        now = datetime.now(timezone.utc).isoformat()
        application_id = str(uuid4())
        job_posting_id = str(uuid4())

        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO applications (
                    id, company, role_title, job_url, job_source, location,
                    status, notes, fit_score, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    application_id,
                    company,
                    title,
                    job_url,
                    "linkedin",
                    location,
                    "captured",
                    "",
                    None,
                    now,
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO job_postings (
                    id, application_id, raw_text, structured_json, captured_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    job_posting_id,
                    application_id,
                    description_raw,
                    json.dumps(structured_json),
                    captured_at,
                ),
            )
            conn.commit()

        return application_id, job_posting_id
