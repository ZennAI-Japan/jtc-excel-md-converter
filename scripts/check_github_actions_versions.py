#!/usr/bin/env python3
"""Fail when GitHub first-party actions use Node 20-era majors."""

from __future__ import annotations

import re
import sys
from pathlib import Path

WORKFLOW_DIR = Path(".github/workflows")
MIN_MAJOR_BY_ACTION = {
    "actions/checkout": 6,
    "actions/setup-python": 6,
    "actions/setup-node": 6,
}
USES_PATTERN = re.compile(r"uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@v(\d+)\b")


def main() -> int:
    violations: list[str] = []
    for workflow in sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml")):
        for line_no, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), start=1):
            match = USES_PATTERN.search(line)
            if not match:
                continue
            action, major_text = match.groups()
            min_major = MIN_MAJOR_BY_ACTION.get(action)
            if min_major is None:
                continue
            major = int(major_text)
            if major < min_major:
                violations.append(
                    f"{workflow}:{line_no}: {action}@v{major} must be v{min_major}+ for Node 24 runtime"
                )

    if violations:
        print("GitHub Actions runtime audit failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("github_actions_runtime_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
