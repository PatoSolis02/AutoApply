from __future__ import annotations

import base64
import io
import unittest
import zipfile
import zlib

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


def _build_compressed_hex_pdf(lines: list[str]) -> bytes:
    chars: list[str] = []
    seen: set[str] = set()
    for line in lines:
        for char in line:
            if char in seen:
                continue
            seen.add(char)
            chars.append(char)

    code_by_char = {char: idx + 1 for idx, char in enumerate(chars)}
    max_code = len(chars)
    cmap_entries = "\n".join(
        f"<{code_by_char[char]:04X}> <{ord(char):04X}>"
        for char in chars
    )
    cmap = (
        "/CIDInit /ProcSet findresource begin\n"
        "12 dict begin\n"
        "begincmap\n"
        "/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def\n"
        "/CMapName /Adobe-Identity-UCS def\n"
        "/CMapType 2 def\n"
        "1 begincodespacerange\n"
        f"<0001> <{max_code:04X}>\n"
        "endcodespacerange\n"
        f"{len(chars)} beginbfchar\n"
        f"{cmap_entries}\n"
        "endbfchar\n"
        "endcmap\n"
        "CMapName currentdict /CMap defineresource pop\n"
        "end\n"
        "end\n"
    ).encode("latin-1")

    content_lines = []
    for line in lines:
        encoded_line = "".join(f"{code_by_char[char]:04X}" for char in line)
        content_lines.append(f"BT /F1 12 Tf 72 720 Td <{encoded_line}> Tj ET")
    content = "\n".join(content_lines).encode("latin-1")

    compressed_content = zlib.compress(content)
    compressed_cmap = zlib.compress(cmap)
    parts = [
        b"%PDF-1.4\n",
        b"1 0 obj << /Length ",
        str(len(compressed_content)).encode("ascii"),
        b" /Filter /FlateDecode >>\nstream\n",
        compressed_content,
        b"\nendstream\nendobj\n",
        b"2 0 obj << /Length ",
        str(len(compressed_cmap)).encode("ascii"),
        b" /Filter /FlateDecode >>\nstream\n",
        compressed_cmap,
        b"\nendstream\nendobj\n%%EOF\n",
    ]
    return b"".join(parts)


def _build_filtered_literal_pdf(lines: list[str], *, filters: list[str], operator: str = "Tj") -> bytes:
    escaped = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    if operator == "'":
        body = "BT\n" + "\n".join(f"({line}) '" for line in escaped) + "\nET"
    else:
        body = "\n".join(f"BT ({line}) {operator} ET" for line in escaped)
    content = body.encode("latin-1")

    encoded = content
    for filter_name in reversed(filters):
        if filter_name == "FlateDecode":
            encoded = zlib.compress(encoded)
        elif filter_name == "ASCII85Decode":
            encoded = base64.a85encode(encoded, adobe=True)
        elif filter_name == "ASCIIHexDecode":
            encoded = encoded.hex().upper().encode("ascii") + b">"
        else:
            raise ValueError(f"unsupported test filter: {filter_name}")

    if len(filters) == 1:
        filter_expr = f"/Filter /{filters[0]}"
    else:
        filter_expr = "/Filter [" + " ".join(f"/{name}" for name in filters) + "]"

    parts = [
        b"%PDF-1.4\n",
        b"1 0 obj << /Length ",
        str(len(encoded)).encode("ascii"),
        b" ",
        filter_expr.encode("latin-1"),
        b" >>\nstream\n",
        encoded,
        b"\nendstream\nendobj\n%%EOF\n",
    ]
    return b"".join(parts)


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

    def test_parse_pdf_decodes_compressed_hex_stream_using_tounicode_map(self) -> None:
        payload = _build_compressed_hex_pdf(
            [
                "Taylor Dev",
                "Platform Engineer",
                "SUMMARY",
                "Builds reliable systems.",
                "SKILLS",
                "Python, SQL, Docker",
                "EXPERIENCE",
                "Senior Backend Engineer | Acme Corp | May 2024 – Aug 2024",
                "- Built Python services.",
                "EDUCATION",
                "RIT | BS Software Engineering | 2020 - 2024",
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
        self.assertEqual(parsed["profile"]["headline"], "Platform Engineer")
        self.assertEqual(parsed["profile"]["experiences"][0]["company"], "Acme Corp")
        self.assertEqual(parsed["profile"]["experiences"][0]["start_date"], "2024-05-01")
        self.assertEqual(parsed["profile"]["experiences"][0]["end_date"], "2024-08-01")
        self.assertIn("Python", parsed["profile"]["experiences"][0]["skills"])

    def test_parse_docx_prefers_labeled_name_and_skips_location_headline_noise(self) -> None:
        payload = _build_docx(
            [
                "Name: Jordan Example",
                "Location: Seattle, WA",
                "Email: jordan@example.com",
                "Principal Platform Engineer",
                "SUMMARY",
                "Builds resilient backend systems.",
                "SKILLS",
                "Python, SQL, AWS",
            ]
        )

        parsed = parse_resume_upload(
            filename="resume.docx",
            payload=payload,
            profile_id="candidate-2",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

        self.assertEqual(parsed["profile"]["full_name"], "Jordan Example")
        self.assertEqual(parsed["profile"]["headline"], "Principal Platform Engineer")

    def test_parse_docx_parses_experience_headings_with_dash_and_split_date_line(self) -> None:
        payload = _build_docx(
            [
                "Taylor Dev",
                "Backend Engineer",
                "SUMMARY",
                "Builds resilient data systems.",
                "EXPERIENCE",
                "Acme Corp - Senior Data Engineer",
                "Jan 2020 - Present",
                "- Built Python ingestion services.",
                "Software Engineer, Beta Labs 2017 - 2019",
                "- Delivered SQL analytics APIs.",
                "EDUCATION",
                "RIT | BS Software Engineering | 2013 - 2017",
            ]
        )

        parsed = parse_resume_upload(filename="resume.docx", payload=payload, profile_id="primary")
        experiences = parsed["profile"]["experiences"]
        self.assertEqual(len(experiences), 2)
        self.assertEqual(experiences[0]["company"], "Acme Corp")
        self.assertEqual(experiences[0]["title"], "Senior Data Engineer")
        self.assertEqual(experiences[0]["start_date"], "2020-01-01")
        self.assertIsNone(experiences[0]["end_date"])
        self.assertEqual(experiences[1]["company"], "Beta Labs")
        self.assertEqual(experiences[1]["title"], "Software Engineer")
        self.assertEqual(experiences[1]["start_date"], "2017-01-01")
        self.assertEqual(experiences[1]["end_date"], "2019-01-01")

    def test_parse_docx_falls_back_to_inferred_skills_without_skills_section(self) -> None:
        payload = _build_docx(
            [
                "Taylor Dev",
                "Platform Engineer",
                "SUMMARY",
                "Builds backend tooling.",
                "EXPERIENCE",
                "Senior Engineer | Acme Corp | 2020 - Present",
                "- Built Python services deployed on AWS with Docker.",
                "PROJECTS",
                "Analytics Portal | Internal dashboard",
                "- Built React + TypeScript UI.",
                "EDUCATION",
                "RIT | BS Software Engineering | 2015 - 2019",
            ]
        )

        parsed = parse_resume_upload(filename="resume.docx", payload=payload, profile_id="primary")
        self.assertIn("Python", parsed["profile"]["skills"])
        self.assertIn("AWS", parsed["profile"]["skills"])
        self.assertIn("Docker", parsed["profile"]["skills"])
        self.assertIn("React", parsed["profile"]["skills"])

    def test_parse_pdf_decodes_ascii85_flate_stream(self) -> None:
        payload = _build_filtered_literal_pdf(
            [
                "Taylor Dev",
                "Platform Engineer",
                "SUMMARY",
                "Builds reliable systems.",
                "SKILLS",
                "Python, SQL, Docker",
                "EXPERIENCE",
                "Senior Backend Engineer | Acme Corp | 05/2024 - 08/2024",
                "- Built Python services.",
                "EDUCATION",
                "RIT | BS Software Engineering | 2020 - 2024",
            ],
            filters=["ASCII85Decode", "FlateDecode"],
            operator="Tj",
        )

        parsed = parse_resume_upload(
            filename="resume.pdf",
            payload=payload,
            profile_id="primary",
            content_type="application/pdf",
        )

        self.assertEqual(parsed["profile"]["full_name"], "Taylor Dev")
        self.assertEqual(parsed["profile"]["experiences"][0]["start_date"], "2024-05-01")
        self.assertEqual(parsed["profile"]["experiences"][0]["end_date"], "2024-08-01")

    def test_parse_pdf_supports_single_quote_text_show_operator(self) -> None:
        payload = _build_filtered_literal_pdf(
            [
                "Taylor Dev",
                "Platform Engineer",
                "SUMMARY",
                "Builds reliable systems.",
                "SKILLS",
                "Python, SQL, Docker",
            ],
            filters=["ASCIIHexDecode"],
            operator="'",
        )

        parsed = parse_resume_upload(
            filename="resume.pdf",
            payload=payload,
            profile_id="primary",
            content_type="application/pdf",
        )

        self.assertEqual(parsed["profile"]["full_name"], "Taylor Dev")
        self.assertEqual(parsed["profile"]["headline"], "Platform Engineer")
        self.assertIn("Python", parsed["profile"]["skills"])

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
