from __future__ import annotations

import html
import textwrap
from pathlib import Path

from autoapply.contracts import RenderModel


class ArtifactWriter:
    def __init__(self, workspace_root: Path, artifacts_root: str = "artifacts/resumes") -> None:
        self._workspace_root = workspace_root.resolve()
        self._artifacts_root = artifacts_root

    def write_resume_artifacts(
        self,
        application_id: str,
        resume_version_id: str,
        render_model: RenderModel,
    ) -> tuple[str, str]:
        relative_dir = Path(self._artifacts_root) / application_id
        absolute_dir = self._workspace_root / relative_dir
        absolute_dir.mkdir(parents=True, exist_ok=True)

        html_relative = relative_dir / f"{resume_version_id}.html"
        pdf_relative = relative_dir / f"{resume_version_id}.pdf"
        html_absolute = self._workspace_root / html_relative
        pdf_absolute = self._workspace_root / pdf_relative

        html_output = self._render_html(render_model)
        html_absolute.write_text(html_output, encoding="utf-8")

        pdf_lines = self._render_text_lines(render_model)
        pdf_absolute.write_bytes(self._build_deterministic_pdf(pdf_lines))

        return html_relative.as_posix(), pdf_relative.as_posix()

    def _render_html(self, model: RenderModel) -> str:
        exp_html = "\n".join(
            [
                "<li><ul>"
                + "".join([f"<li>{html.escape(bullet.text)}</li>" for bullet in section.bullets])
                + "</ul></li>"
                for section in model.sections.get("experience", [])
            ]
        )
        proj_html = "\n".join(
            [
                "<li><ul>"
                + "".join([f"<li>{html.escape(bullet.text)}</li>" for bullet in section.bullets])
                + "</ul></li>"
                for section in model.sections.get("projects", [])
            ]
        )
        skills_html = "".join([f"<li>{html.escape(skill)}</li>" for skill in model.selected_skill_keywords])

        return "\n".join(
            [
                "<!doctype html>",
                "<html lang=\"en\">",
                "<head>",
                "  <meta charset=\"utf-8\">",
                "  <title>AutoApply Resume</title>",
                "</head>",
                "<body>",
                f"  <h1>{html.escape(model.headline)}</h1>",
                f"  <p>{html.escape(model.summary)}</p>",
                "  <h2>Experience</h2>",
                f"  <ul>{exp_html}</ul>",
                "  <h2>Projects</h2>",
                f"  <ul>{proj_html}</ul>",
                "  <h2>Skills</h2>",
                f"  <ul>{skills_html}</ul>",
                "</body>",
                "</html>",
            ]
        )

    def _render_text_lines(self, model: RenderModel) -> list[str]:
        lines: list[str] = []
        lines.append(model.headline)
        if model.summary:
            lines.append(model.summary)
        lines.append("Experience")
        for section in model.sections.get("experience", []):
            lines.append(f"- {section.entry_id}")
            for bullet in section.bullets:
                lines.append(f"  * {bullet.text}")
        lines.append("Projects")
        for section in model.sections.get("projects", []):
            lines.append(f"- {section.entry_id}")
            for bullet in section.bullets:
                lines.append(f"  * {bullet.text}")
        lines.append("Skills")
        for skill in model.selected_skill_keywords:
            lines.append(f"- {skill}")

        wrapped: list[str] = []
        for line in lines:
            parts = textwrap.wrap(line, width=88) or [""]
            wrapped.extend(parts)
        return wrapped

    def _build_deterministic_pdf(self, lines: list[str]) -> bytes:
        content = ["BT", "/F1 11 Tf", "50 760 Td"]
        first = True
        for line in lines:
            escaped = self._escape_pdf_text(line)
            if first:
                content.append(f"({escaped}) Tj")
                first = False
            else:
                content.append("0 -14 Td")
                content.append(f"({escaped}) Tj")
        content.append("ET")

        stream = "\n".join(content).encode("latin-1", errors="replace")

        objects: list[bytes] = []
        objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        objects.append(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
        objects.append(
            b"3 0 obj\n"
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>\n"
            b"endobj\n"
        )
        objects.append(
            b"4 0 obj\n"
            + f"<< /Length {len(stream)} >>\n".encode("ascii")
            + b"stream\n"
            + stream
            + b"\nendstream\nendobj\n"
        )
        objects.append(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

        output = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for obj in objects:
            offsets.append(len(output))
            output.extend(obj)

        xref_start = len(output)
        output.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
        output.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

        output.extend(
            (
                "trailer\n"
                f"<< /Size {len(offsets)} /Root 1 0 R >>\n"
                "startxref\n"
                f"{xref_start}\n"
                "%%EOF\n"
            ).encode("ascii")
        )
        return bytes(output)

    def _escape_pdf_text(self, value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        return escaped.encode("latin-1", errors="replace").decode("latin-1")
