#!/usr/bin/env python3
"""Safely preview, apply, commit, and optionally push generated mirrors."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "skills" / "manifest.json"
BUILDER = ROOT / "scripts" / "build_mirror.py"


def run(command: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=check)


def load_manifest() -> dict:
    from build_mirror import load_manifest as load_validated_manifest

    return load_validated_manifest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--skill", action="append")
    parser.add_argument("--mirrors-root", type=Path, default=ROOT / "standalone-builds")
    parser.add_argument("--source-commit")
    parser.add_argument("--version")
    parser.add_argument("--no-fetch", action="store_true", help="Use existing directories without Git network operations")
    parser.add_argument("--apply", action="store_true", help="Replace mirror worktrees with generated output")
    parser.add_argument("--push", action="store_true", help="Commit and push applied changes (requires --apply)")
    parser.add_argument("--metadata", action="store_true", help="Update GitHub description/topics after a successful push")
    parser.add_argument("--metadata-only", action="store_true", help="Update GitHub descriptions/topics without touching mirror worktrees")
    parser.add_argument("--allow-dirty-source", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def git_head() -> str:
    return run(["git", "rev-parse", "HEAD"], cwd=ROOT).stdout.strip()


def reject_existing_symlink_components(path: Path) -> Path:
    candidate = path.expanduser().absolute()
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current = current / part
        if current.exists() and current.is_symlink():
            raise RuntimeError(f"mirrors path contains a symlink component: {current}")
    return candidate


def selected_entries(manifest: dict, args: argparse.Namespace) -> list[dict]:
    wanted = {entry["id"] for entry in manifest["skills"]} if args.all else set(args.skill or [])
    unknown = wanted - {entry["id"] for entry in manifest["skills"]}
    if unknown:
        raise ValueError(f"unknown skill IDs: {', '.join(sorted(unknown))}")
    return [entry for entry in manifest["skills"] if entry["id"] in wanted]


def ensure_checkout(entry: dict, root: Path, no_fetch: bool) -> Path:
    if root.is_symlink():
        raise RuntimeError(f"mirrors root must not be a symlink: {root}")
    root_resolved = root.resolve()
    repo = root / entry["mirror_repo"]
    if repo.is_symlink():
        raise RuntimeError(f"mirror checkout must not be a symlink: {repo}")
    repo_resolved = repo.resolve()
    if not repo_resolved.is_relative_to(root_resolved):
        raise RuntimeError(f"mirror checkout escapes mirrors root: {repo}")
    if no_fetch:
        if not repo.is_dir():
            raise FileNotFoundError(repo)
    elif not (repo / ".git").exists():
        repo.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", f"https://github.com/Vo1ganin/{entry['mirror_repo']}.git", str(repo)])

    inside = run(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo, check=False)
    if inside.returncode or inside.stdout.strip() != "true":
        raise RuntimeError(f"not a valid Git worktree: {repo}")
    top = Path(run(["git", "rev-parse", "--show-toplevel"], cwd=repo).stdout.strip()).resolve()
    if top != repo_resolved:
        raise RuntimeError(f"checkout root mismatch: expected {repo_resolved}, got {top}")
    branch = run(["git", "branch", "--show-current"], cwd=repo).stdout.strip()
    if branch != "main":
        raise RuntimeError(f"mirror checkout must be on main: {repo} ({branch or 'detached'})")
    origin = run(["git", "remote", "get-url", "origin"], cwd=repo).stdout.strip()
    accepted_origins = {
        f"https://github.com/Vo1ganin/{entry['mirror_repo']}.git",
        f"git@github.com:Vo1ganin/{entry['mirror_repo']}.git",
    }
    if origin not in accepted_origins:
        raise RuntimeError(f"unexpected origin for {repo}: {origin}")
    if not (repo / ".git").is_dir():
        raise RuntimeError(f"mirror checkout must use an in-tree .git directory: {repo}")
    status = run(["git", "status", "--porcelain"], cwd=repo).stdout.strip()
    if status:
        raise RuntimeError(f"mirror checkout is dirty: {repo}")
    if not no_fetch:
        run(["git", "fetch", "origin", "main"], cwd=repo)
        run(["git", "merge", "--ff-only", "origin/main"], cwd=repo)
    return repo


def comparable_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and ".git" not in path.parts
    }


def replace_worktree(repo: Path, expected: Path) -> None:
    if repo.is_symlink() or not (repo / ".git").is_dir():
        raise RuntimeError(f"refusing destructive replacement of unsafe checkout: {repo}")
    for child in list(repo.iterdir()):
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in expected.iterdir():
        target = repo / child.name
        if child.is_dir():
            shutil.copytree(child, target)
        else:
            shutil.copy2(child, target)


def update_metadata(entry: dict) -> None:
    topics = json.dumps({"names": entry["topics"]})
    run(
        [
            "gh",
            "api",
            "--method",
            "PATCH",
            f"repos/Vo1ganin/{entry['mirror_repo']}",
            "-f",
            f"description={entry['description']}",
        ]
    )
    topic_command = [
        "gh",
        "api",
        "--method",
        "PUT",
        f"repos/Vo1ganin/{entry['mirror_repo']}/topics",
    ]
    for topic in entry["topics"]:
        topic_command.extend(["-f", f"names[]={topic}"])
    run(topic_command)


def main() -> int:
    args = parse_args()
    if args.push and not args.apply:
        raise ValueError("--push requires --apply")
    if args.metadata and not args.push:
        raise ValueError("--metadata requires --push")
    if args.metadata_only and any([args.apply, args.push, args.metadata, args.no_fetch]):
        raise ValueError("--metadata-only cannot be combined with apply/push/metadata/no-fetch")
    if args.no_fetch and args.push:
        raise ValueError("--push cannot be combined with --no-fetch")
    if args.allow_dirty_source and args.metadata_only:
        raise ValueError("--allow-dirty-source cannot be used for metadata publication")
    if args.allow_dirty_source and not (args.no_fetch and not args.push):
        raise ValueError("--allow-dirty-source is test/development-only")

    manifest = load_manifest()
    entries = selected_entries(manifest, args)
    source_commit = args.source_commit or git_head()
    version = args.version or manifest["collection_version"]
    if not args.allow_dirty_source:
        source_status = run(["git", "status", "--porcelain"], cwd=ROOT).stdout.strip()
        if source_status:
            raise RuntimeError("canonical source worktree must be clean before apply/publish")
        run(["git", "cat-file", "-e", f"{source_commit}^{{commit}}"], cwd=ROOT)
        if source_commit != git_head():
            raise RuntimeError("source commit must equal canonical HEAD")
    if args.push or (args.metadata_only and not args.allow_dirty_source):
        source_branch = run(["git", "branch", "--show-current"], cwd=ROOT).stdout.strip()
        if source_branch != "main":
            raise RuntimeError("publishing mirror content/metadata is allowed only from canonical main")

    if args.metadata_only:
        for entry in entries:
            update_metadata(entry)
        print(json.dumps({"mode": "metadata-only", "updated": [entry["mirror_repo"] for entry in entries]}, indent=2))
        return 0

    mirrors_root_input = reject_existing_symlink_components(args.mirrors_root)
    mirrors_root_input.mkdir(parents=True, exist_ok=True)
    mirrors_root = mirrors_root_input.resolve()

    with tempfile.TemporaryDirectory() as tmp:
        expected_root = Path(tmp) / "expected"
        build = run(
            [
                sys.executable,
                str(BUILDER),
                "--all",
                "--output",
                str(expected_root),
                "--source-commit",
                source_commit,
                "--version",
                version,
            ],
            cwd=ROOT,
            check=False,
        )
        if build.returncode:
            print(build.stderr, file=sys.stderr)
            return build.returncode

        changed: list[str] = []
        unchanged: list[str] = []
        checkouts: dict[str, Path] = {}
        for entry in entries:
            repo = ensure_checkout(entry, mirrors_root, args.no_fetch)
            checkouts[entry["id"]] = repo
            expected = expected_root / entry["mirror_repo"]
            if comparable_files(repo) == comparable_files(expected):
                unchanged.append(entry["mirror_repo"])
            else:
                changed.append(entry["mirror_repo"])
                if args.apply:
                    replace_worktree(repo, expected)

        if not args.apply:
            print(json.dumps({"mode": "dry-run", "changed": changed, "unchanged": unchanged}, indent=2))
            return 1 if changed else 0

        committed: list[str] = []
        pushed: list[str] = []
        if args.push:
            for entry in entries:
                repo = checkouts[entry["id"]]
                run(["git", "add", "-A"], cwd=repo)
                staged = run(["git", "diff", "--cached", "--quiet"], cwd=repo, check=False)
                if staged.returncode != 0:
                    run(["git", "commit", "-m", f"chore: sync generated mirror from umbrella {version}"], cwd=repo)
                    committed.append(entry["mirror_repo"])
                run(["git", "push", "origin", "main"], cwd=repo)
                pushed.append(entry["mirror_repo"])
            if args.metadata:
                for entry in entries:
                    update_metadata(entry)

    print(
        json.dumps(
            {
                "mode": "apply",
                "changed": changed,
                "unchanged": unchanged,
                "committed": committed,
                "pushed": pushed,
                "source_commit": source_commit,
                "version": version,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"mirror sync failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
