#!/usr/bin/env python3
"""Enforce local/runtime tooling versions for CI and local guardrails."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Requirement:
    name: str
    command: list[str]
    version_pattern: str
    expected_description: str
    check: callable


def run_command(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise RuntimeError(f"{command[0]} is not installed or not on PATH.")
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        msg = stderr or f"{command[0]} exited with code {exc.returncode}."
        raise RuntimeError(msg)

    output = (completed.stdout or completed.stderr).strip()
    if not output:
        raise RuntimeError(f"{command[0]} did not return a version string.")
    return output


def parse_version(output: str, pattern: str) -> tuple[int, int, int]:
    match = re.search(pattern, output)
    if not match:
        raise RuntimeError(f"Could not parse version from: {output!r}")
    major, minor, patch = (int(value) for value in match.groups())
    return major, minor, patch


def main() -> int:
    requirements = [
        Requirement(
            name="python3",
            command=["python3", "--version"],
            version_pattern=r"Python\s+(\d+)\.(\d+)\.(\d+)",
            expected_description=">= 3.11.x",
            check=lambda v: v >= (3, 11, 0),
        ),
        Requirement(
            name="node",
            command=["node", "--version"],
            version_pattern=r"v(\d+)\.(\d+)\.(\d+)",
            expected_description="24.x",
            check=lambda v: v[0] == 24,
        ),
        Requirement(
            name="npm",
            command=["npm", "--version"],
            version_pattern=r"(\d+)\.(\d+)\.(\d+)",
            expected_description="11.x",
            check=lambda v: v[0] == 11,
        ),
    ]

    failures: list[str] = []

    print("Runtime baseline check")
    for requirement in requirements:
        try:
            raw = run_command(requirement.command)
            version = parse_version(raw, requirement.version_pattern)
            display = ".".join(str(v) for v in version)
            if requirement.check(version):
                print(f"  [ok] {requirement.name} {display} (expected {requirement.expected_description})")
            else:
                failures.append(
                    f"{requirement.name} {display} does not satisfy {requirement.expected_description}"
                )
                print(
                    f"  [fail] {requirement.name} {display} (expected {requirement.expected_description})"
                )
        except RuntimeError as exc:
            failures.append(f"{requirement.name}: {exc}")
            print(f"  [fail] {requirement.name}: {exc}")

    if failures:
        print("\nVersion baseline enforcement failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("\nAll runtime versions satisfy the baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
