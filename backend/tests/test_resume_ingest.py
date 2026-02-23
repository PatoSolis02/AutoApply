from __future__ import annotations

import io
import unittest
import zipfile

from app.resume_ingest import (
    ResumeParseError,
    ResumeParseValidationError,
    ResumeUnsupportedTypeError,
    parse_resume_upload,
)


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


class ResumeIngestTests(unittest.TestCase):
    def test_parse_docx_maps_to_canonical_profile_shape(self) -> None:
        payload = _build_docx(
            [
                "Taylor Dev",
                "Backend Engineer",
                "taylor@example.com",
                "SUMMARY",
                "Builds reliable backend systems.",
                "SKILLS",
                "Python, FastAPI, SQL, AWS",
                "EXPERIENCE",
                "Senior Backend Engineer | Acme Corp | Jan 2020 - Present",
                "- Built Python APIs for ingestion.",
                "- Reduced SQL latency by 40%.",
                "PROJECTS",
                "AutoApply | Resume tailoring tool",
                "- Built FastAPI backend and React UI.",
                "https://github.com/taylor/autoapply",
                "EDUCATION",
                "RIT | BS Computer Science | Sep 2015 - May 2019",
            ]
        )

        parsed = parse_resume_upload(
            filename="resume.docx",
            payload=payload,
            profile_id="candidate-1",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        self.assertEqual(parsed["contract_version"], "resume_parse.v1")
        self.assertEqual(parsed["source"]["file_type"], "docx")
        self.assertEqual(parsed["profile"]["id"], "candidate-1")
        self.assertEqual(parsed["profile"]["full_name"], "Taylor Dev")
        self.assertEqual(parsed["profile"]["headline"], "Backend Engineer")
        self.assertIn("Python", parsed["profile"]["skills"])
        self.assertEqual(len(parsed["profile"]["experiences"]), 1)
        self.assertEqual(parsed["profile"]["experiences"][0]["company"], "Acme Corp")
        self.assertEqual(parsed["profile"]["experiences"][0]["title"], "Senior Backend Engineer")
        self.assertEqual(parsed["profile"]["experiences"][0]["start_date"], "2020-01-01")
        self.assertIsNone(parsed["profile"]["experiences"][0]["end_date"])
        self.assertEqual(len(parsed["profile"]["education"]), 1)
        self.assertEqual(parsed["profile"]["education"][0]["school"], "RIT")
        self.assertEqual(parsed["profile"]["education"][0]["degree"], "BS Computer Science")

    def test_parse_pdf_maps_multiple_experiences_and_dedupes_skills(self) -> None:
        payload = _build_pdf(
            [
                "Taylor Dev",
                "Platform Engineer",
                "SUMMARY",
                "Delivers reliable systems.",
                "SKILLS",
                "Python, SQL, Python, Docker",
                "EXPERIENCE",
                "Staff Engineer | Data Co | 2021 - Present",
                "- Built Python services.",
                "Software Engineer | App Co | 2018 - 2021",
                "- Owned SQL data pipelines.",
                "EDUCATION",
                "RIT | BS Software Engineering | 2014 - 2018",
            ]
        )

        parsed = parse_resume_upload(
            filename="resume.pdf",
            payload=payload,
            profile_id="primary",
            content_type="application/pdf",
        )

        self.assertEqual(parsed["source"]["file_type"], "pdf")
        self.assertEqual(parsed["profile"]["full_name"], "Taylor Dev")
        self.assertEqual(parsed["profile"]["skills"], ["Python", "SQL", "Docker"])
        self.assertEqual(len(parsed["profile"]["experiences"]), 2)
        self.assertEqual(parsed["profile"]["experiences"][1]["company"], "App Co")
        self.assertEqual(parsed["profile"]["experiences"][1]["end_date"], "2021-01-01")

    def test_parse_rejects_unsupported_extension(self) -> None:
        with self.assertRaises(ResumeUnsupportedTypeError):
            parse_resume_upload(filename="resume.txt", payload=b"text", profile_id="primary")

    def test_parse_rejects_invalid_pdf_payload(self) -> None:
        with self.assertRaises(ResumeParseError):
            parse_resume_upload(
                filename="resume.pdf",
                payload=b"not a pdf",
                profile_id="primary",
                content_type="application/pdf",
            )

    def test_parse_returns_validation_error_for_missing_profile_identity(self) -> None:
        payload = _build_pdf(
            [
                "taylor@example.com",
                "SUMMARY",
                "Works on APIs.",
            ]
        )
        with self.assertRaises(ResumeParseValidationError) as ctx:
            parse_resume_upload(filename="resume.pdf", payload=payload, profile_id="primary")

        fields = {item["field"] for item in ctx.exception.errors}
        self.assertIn("profile.full_name", fields)


if __name__ == "__main__":
    unittest.main()
