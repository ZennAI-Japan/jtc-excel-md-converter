from __future__ import annotations

import re
from pathlib import Path

REQUIRED_APPROVALS = [
    "保守者承認",
    "実顧客文書評価",
    "秘密情報確認",
    "ライセンス確認",
]


def check_public_release_approval(path: Path) -> tuple[bool, list[str]]:
    if not path.exists():
        return False, [f"{path} がありません。"]
    text = path.read_text(encoding="utf-8")
    missing = []
    for label in REQUIRED_APPROVALS:
        if not re.search(rf"- \[x\] {re.escape(label)}\b", text):
            missing.append(f"未承認: {label}")
    return not missing, missing


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Fail closed until maintainers approve public release.")
    parser.add_argument("--approval", type=Path, default=Path("docs/public-release-approval.md"))
    args = parser.parse_args()
    ok, issues = check_public_release_approval(args.approval)
    if ok:
        print("public_release_approval=ok")
        raise SystemExit(0)
    for issue in issues:
        print(issue)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
