from __future__ import annotations

import re
from collections import Counter

TECH_KEYWORDS = {
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "React",
    "Node.js",
    "FastAPI",
    "Django",
    "Flask",
    "SQL",
    "PostgreSQL",
    "SQLite",
    "AWS",
    "GCP",
    "Azure",
    "Docker",
    "Kubernetes",
}

STOP_WORDS = {
    "and",
    "the",
    "with",
    "for",
    "you",
    "our",
    "your",
    "this",
    "that",
    "from",
    "will",
    "are",
    "job",
    "role",
    "team",
    "work",
    "have",
    "years",
}



def _line_filter(raw_text: str) -> list[str]:
    return [line.strip(" -\t") for line in raw_text.splitlines() if line.strip()]



def _detect_employment_type(raw_text: str) -> str:
    text = raw_text.lower()
    if "full time" in text or "full-time" in text:
        return "full_time"
    if "part time" in text or "part-time" in text:
        return "part_time"
    if "contract" in text or "contractor" in text:
        return "contract"
    if "intern" in text or "internship" in text:
        return "internship"
    return "unknown"



def _detect_seniority(raw_text: str) -> str:
    text = raw_text.lower()
    if "principal" in text:
        return "principal"
    if "staff" in text:
        return "staff"
    if "senior" in text or "sr." in text:
        return "senior"
    if "mid" in text or "intermediate" in text:
        return "mid"
    if "junior" in text or "jr." in text:
        return "junior"
    if "intern" in text:
        return "intern"
    return "unknown"



def _keyword_extract(raw_text: str, max_keywords: int = 20) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{3,}", raw_text)
    counts = Counter(token.lower() for token in tokens if token.lower() not in STOP_WORDS)
    return [word for word, _ in counts.most_common(max_keywords)]



def build_structured_job_posting(raw_text: str) -> dict[str, object]:
    lines = _line_filter(raw_text)
    summary = lines[0] if lines else None

    def pick(matcher: tuple[str, ...], limit: int = 10) -> list[str]:
        matches = [line for line in lines if any(token in line.lower() for token in matcher)]
        return matches[:limit]

    tech_stack = sorted(
        {
            keyword
            for keyword in TECH_KEYWORDS
            if re.search(rf"\b{re.escape(keyword)}\b", raw_text, flags=re.IGNORECASE)
        }
    )

    return {
        "summary": summary,
        "responsibilities": pick(("responsibil", "you will", "what you'll do", "what you will do")),
        "requirements": pick(("requirement", "qualifications", "must", "experience with")),
        "preferred_qualifications": pick(("preferred", "nice to have", "bonus")),
        "tech_stack": tech_stack,
        "employment_type": _detect_employment_type(raw_text),
        "seniority": _detect_seniority(raw_text),
        "keywords": _keyword_extract(raw_text),
    }
