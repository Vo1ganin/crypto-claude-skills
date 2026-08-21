#!/usr/bin/env python3
"""Compare checked-out standalone mirrors with deterministic umbrella output."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_mirror.py"
MANIFEST = ROOT / "skills" / "manifest.json"


def digest_tree(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts):
        result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mirrors-root", type=Path, required=True)
    parser.add_argument("--source-commit")
    parser.add_argument("--version")
    parser.add_argument("--public-only", action="store_true")
    return parser.parse_args()


def git_source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> int:
    args = parse_args()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    source_commit = args.source_commit or git_source_commit()
    version = args.version or manifest["collection_version"]
    entries = [
        entry
        for entry in manifest["skills"]
        if not args.public_only or entry.get("visibility") != "private_until_safety_review"
    ]

    with tempfile.TemporaryDirectory() as tmp:
        expected_root = Path(tmp) / "expected"
        command = [
            sys.executable,
            str(BUILDER),
            "--all",
            "--output",
            str(expected_root),
            "--source-commit",
            source_commit,
            "--version",
            version,
        ]
        build = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        if build.returncode:
            print(build.stderr, file=sys.stderr)
            return build.returncode

        drift: dict[str, dict[str, list[str]]] = {}
        for entry in entries:
            repo = entry["mirror_repo"]
            expected = expected_root / repo
            actual = args.mirrors_root.resolve() / repo
            if not actual.is_dir():
                drift[repo] = {"missing_repository": [str(actual)]}
                continue
            expected_hashes = digest_tree(expected)
            actual_hashes = digest_tree(actual)
            missing = sorted(set(expected_hashes) - set(actual_hashes))
            extra = sorted(set(actual_hashes) - set(expected_hashes))
            changed = sorted(
                path
                for path in set(expected_hashes) & set(actual_hashes)
                if expected_hashes[path] != actual_hashes[path]
            )
            if missing or extra or changed:
                drift[repo] = {"missing": missing, "extra": extra, "changed": changed}

    if drift:
        print(json.dumps({"status": "drift", "repositories": drift}, indent=2))
        return 1
    print(json.dumps({"status": "clean", "checked": [entry["mirror_repo"] for entry in entries]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
