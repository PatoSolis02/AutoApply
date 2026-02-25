from __future__ import annotations

from autoapply.contracts import RenderModel

GENERATED_RESUME_FORMAT_CONTRACT_VERSION = "resume_format.v1"
GENERATED_RESUME_FORMAT_BASELINE = "artifacts/resume_samples/Redacted Resume.pdf"

_MODEL_SECTION_ORDER = ("education", "experience", "projects")
_OUTPUT_SECTION_ORDER = ("education", "experience", "projects", "skills")
_SECTION_LABELS = {
    "education": "Education",
    "experience": "Work Experience",
    "projects": "Projects",
    "skills": "Skills",
}


def output_section_order() -> tuple[str, ...]:
    return _OUTPUT_SECTION_ORDER


def section_heading(section_key: str) -> str:
    return _SECTION_LABELS.get(section_key, section_key.title())


def ordered_output_sections(model: RenderModel) -> list[str]:
    sections: list[str] = []
    for section_key in _MODEL_SECTION_ORDER:
        if model.sections.get(section_key):
            sections.append(section_key)
    if model.selected_skill_keywords:
        sections.append("skills")
    return sections


def collect_contract_violations(model: RenderModel) -> list[str]:
    errors: list[str] = []

    unknown_section_keys = sorted(set(model.sections.keys()) - set(_MODEL_SECTION_ORDER))
    if unknown_section_keys:
        errors.append(f"unsupported section keys: {', '.join(unknown_section_keys)}")

    present_sections_in_model_order = [
        section_key
        for section_key in model.sections.keys()
        if section_key in _MODEL_SECTION_ORDER and model.sections.get(section_key)
    ]
    expected_present_sections = [key for key in _MODEL_SECTION_ORDER if key in present_sections_in_model_order]
    if present_sections_in_model_order != expected_present_sections:
        errors.append(
            "section order must follow contract order "
            f"{list(_MODEL_SECTION_ORDER)} for present sections"
        )

    for section_key in _MODEL_SECTION_ORDER:
        entries = model.sections.get(section_key, [])
        if not isinstance(entries, list):
            errors.append(f"section '{section_key}' must be a list")
            continue

        for entry_index, entry in enumerate(entries):
            if not entry.entry_id.strip():
                errors.append(f"section '{section_key}' entry[{entry_index}] has empty entry_id")
            if len(entry.bullets) == 0:
                errors.append(f"section '{section_key}' entry[{entry_index}] has no bullets")
            for bullet_index, bullet in enumerate(entry.bullets):
                if not bullet.id.strip():
                    errors.append(
                        f"section '{section_key}' entry[{entry_index}] bullet[{bullet_index}] has empty id"
                    )
                if not bullet.text.strip():
                    errors.append(
                        f"section '{section_key}' entry[{entry_index}] bullet[{bullet_index}] has empty text"
                    )

    for index, skill in enumerate(model.selected_skill_keywords):
        if not skill.strip():
            errors.append(f"selected_skill_keywords[{index}] is empty")

    return errors


def assert_render_model_conforms(model: RenderModel) -> None:
    errors = collect_contract_violations(model)
    if errors:
        raise ValueError("generated resume format contract violation: " + "; ".join(errors))
