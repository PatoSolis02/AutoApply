from __future__ import annotations

import io
import json
import threading
import unittest
import zipfile
from http.client import HTTPConnection
from typing import Any

from app.main import create_server


def _build_docx(lines: list[str]) -> bytes:
    document_lines = "".join(
        f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>"
        for line in lines
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{document_lines}</w:body>"
        "</w:document>"
    ).encode("utf-8")

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    ).encode("utf-8")

    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    ).encode("utf-8")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def _build_pdf(lines: list[str]) -> bytes:
    escaped = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    body = "\n".join(f"({line}) Tj" for line in escaped)
    return f"%PDF-1.4\n{body}\n".encode("latin-1")


def _build_multipart(
    *,
    fields: dict[str, str] | None = None,
    files: list[tuple[str, str, str, bytes]],
) -> tuple[str, bytes]:
    boundary = "----AutoApplyBoundaryS4A"
    chunks: list[bytes] = []

    for name, value in (fields or {}).items():
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(value.encode("utf-8"))
        chunks.append(b"\r\n")

    for field_name, filename, content_type, data in files:
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n"
            ).encode("utf-8")
        )
        chunks.append(data)
        chunks.append(b"\r\n")

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return f"multipart/form-data; boundary={boundary}", b"".join(chunks)


class ResumeUploadApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = self._create_tmpdir()
        self.db_path = self._tmpdir + "/resume-upload-api-test.db"
        self.server = create_server(db_path=self.db_path, host="127.0.0.1", port=0)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def _create_tmpdir(self) -> str:
        import tempfile

        return tempfile.mkdtemp(prefix="resume-upload-api-tests-")

    def _request(self, method: str, path: str, body: bytes = b"", headers: dict[str, str] | None = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        raw = response.read().decode("utf-8")
        conn.close()
        return response.status, (json.loads(raw) if raw else {})

    def test_resume_parse_upload_returns_canonical_profile_contract(self) -> None:
        payload = _build_docx(
            [
                "Taylor Dev",
                "Backend Engineer",
                "SUMMARY",
                "Builds backend systems.",
                "SKILLS",
                "Python, FastAPI, SQL",
                "EXPERIENCE",
                "Senior Backend Engineer | Acme Corp | Jan 2020 - Present",
                "- Built Python APIs.",
                "EDUCATION",
                "RIT | BS Computer Science | Sep 2015 - May 2019",
            ]
        )
        content_type, body = _build_multipart(
            fields={"profile_id": "candidate-123"},
            files=[("file", "resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", payload)],
        )

        status, parsed = self._request(
            "POST",
            "/api/v1/profile/resume-parse",
            body=body,
            headers={"Content-Type": content_type, "Content-Length": str(len(body))},
        )

        self.assertEqual(status, 200)
        self.assertEqual(parsed["contract_version"], "resume_parse.v1")
        self.assertEqual(parsed["source"]["file_type"], "docx")
        self.assertEqual(parsed["profile"]["id"], "candidate-123")
        self.assertEqual(parsed["profile"]["full_name"], "Taylor Dev")
        self.assertEqual(parsed["profile"]["experiences"][0]["company"], "Acme Corp")

    def test_resume_parse_upload_accepts_legacy_endpoint_alias(self) -> None:
        payload = _build_docx(
            [
                "Taylor Dev",
                "Backend Engineer",
                "SUMMARY",
                "Builds backend systems.",
                "SKILLS",
                "Python, FastAPI, SQL",
            ]
        )
        content_type, body = _build_multipart(
            files=[("file", "resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", payload)],
        )

        status, parsed = self._request(
            "POST",
            "/api/v1/profile/ingest",
            body=body,
            headers={"Content-Type": content_type, "Content-Length": str(len(body))},
        )

        self.assertEqual(status, 200)
        self.assertEqual(parsed["contract_version"], "resume_parse.v1")
        self.assertEqual(parsed["profile"]["full_name"], "Taylor Dev")

    def test_resume_parse_upload_accepts_legacy_resume_file_field_alias(self) -> None:
        payload = _build_docx(
            [
                "Taylor Dev",
                "Backend Engineer",
                "SUMMARY",
                "Builds backend systems.",
                "SKILLS",
                "Python, FastAPI, SQL",
            ]
        )
        content_type, body = _build_multipart(
            files=[("resume", "resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", payload)],
        )

        status, parsed = self._request(
            "POST",
            "/api/v1/profile/resume-parse",
            body=body,
            headers={"Content-Type": content_type, "Content-Length": str(len(body))},
        )

        self.assertEqual(status, 200)
        self.assertEqual(parsed["contract_version"], "resume_parse.v1")
        self.assertEqual(parsed["profile"]["full_name"], "Taylor Dev")

    def test_resume_parse_upload_rejects_non_multipart_payload(self) -> None:
        status, body = self._request(
            "POST",
            "/api/v1/profile/resume-parse",
            body=b"{}",
            headers={"Content-Type": "application/json", "Content-Length": "2"},
        )

        self.assertEqual(status, 400)
        self.assertEqual(body["detail"], "invalid request payload")
        self.assertEqual(body["errors"][0]["field"], "content_type")

    def test_resume_parse_upload_rejects_unsupported_file_extension(self) -> None:
        content_type, body = _build_multipart(
            files=[("file", "resume.txt", "text/plain", b"Taylor Dev")],
        )
        status, response = self._request(
            "POST",
            "/api/v1/profile/resume-parse",
            body=body,
            headers={"Content-Type": content_type, "Content-Length": str(len(body))},
        )

        self.assertEqual(status, 415)
        self.assertIn(".pdf and .docx", response["detail"])

    def test_resume_parse_upload_returns_422_on_parse_validation_failure(self) -> None:
        payload = _build_pdf(
            [
                "taylor@example.com",
                "SUMMARY",
                "Builds APIs.",
            ]
        )
        content_type, body = _build_multipart(
            files=[("file", "resume.pdf", "application/pdf", payload)],
        )
        status, response = self._request(
            "POST",
            "/api/v1/profile/resume-parse",
            body=body,
            headers={"Content-Type": content_type, "Content-Length": str(len(body))},
        )

        self.assertEqual(status, 422)
        self.assertEqual(response["detail"], "parsed profile failed validation")
        fields = {item["field"] for item in response["errors"]}
        self.assertIn("profile.full_name", fields)

    def test_resume_parse_upload_requires_file_field(self) -> None:
        content_type, body = _build_multipart(fields={"profile_id": "candidate-1"}, files=[])
        status, response = self._request(
            "POST",
            "/api/v1/profile/resume-parse",
            body=body,
            headers={"Content-Type": content_type, "Content-Length": str(len(body))},
        )

        self.assertEqual(status, 400)
        self.assertEqual(response["detail"], "invalid request payload")
        self.assertEqual(response["errors"][0]["field"], "file")


if __name__ == "__main__":
    unittest.main()
