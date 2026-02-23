#!/usr/bin/env python3
"""Fail when generated/vendor artifacts are tracked by git."""

from __future__ import annotations

import subprocess
import sys


def load_tracked_files() -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    raw = completed.stdout.decode("utf-8", errors="strict")
    return [path for path in raw.split("\x00") if path]


def is_blocked(path: str) -> bool:
    return any(
        [
            path.startswith("node_modules/"),
            path.startswith("artifacts/"),
            path.startswith("backend/data/"),
            path.startswith("dist/"),
            path.startswith("coverage/"),
            path.startswith(".vite/"),
            path.endswith(".tsbuildinfo"),
            path.endswith(".pyc"),
            path.startswith("__pycache__/"),
            "/__pycache__/" in path,
            path in {"vite.config.js", "vite.config.d.ts"},
        ]
    )


def main() -> int:
    files = load_tracked_files()
    blocked = sorted(path for path in files if is_blocked(path))

    if not blocked:
        print("Tracked artifact/vendor check passed: no blocked files are tracked.")
        return 0

    print("Tracked artifact/vendor check failed. Remove these tracked files:")
    for path in blocked:
        print(f"  - {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
