import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_mirror.py"
DRIFT_CHECKER = ROOT / "scripts" / "check_mirror_drift.py"
SYNC_TOOL = ROOT / "scripts" / "sync_mirrors.py"
TIP_SNAPSHOT = ROOT / "skills" / "mev-bundles" / "references" / "examples" / "tip_floor_snapshot.py"
MANIFEST = ROOT / "skills" / "manifest.json"
SKILL_IDS = {
    "dune",
    "solscan",
    "nansen",
    "solana-rpc",
    "pumpfun",
    "dexscreener",
    "mev-bundles",
    "coinmarketcap",
}


def tree_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for file in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(file.relative_to(path).as_posix().encode())
        digest.update(b"\0")
        digest.update(file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


class MirrorBuilderTest(unittest.TestCase):
    def run_builder(self, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                "--all",
                "--output",
                str(output),
                "--source-commit",
                "test-source-sha",
                "--version",
                "0.2.0-test",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_manifest_declares_eight_unique_skills(self):
        data = json.loads(MANIFEST.read_text())
        entries = data["skills"]
        self.assertEqual({entry["id"] for entry in entries}, SKILL_IDS)
        self.assertEqual(len({entry["mirror_repo"] for entry in entries}), 8)
        for entry in entries:
            self.assertTrue((ROOT / "skills" / entry["id"] / "SKILL.md").is_file())
            self.assertTrue(entry["description"])
            self.assertGreaterEqual(len(entry["topics"]), 4)

    def test_builds_safe_complete_mirrors(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "mirrors"
            result = self.run_builder(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(MANIFEST.read_text())
            for entry in data["skills"]:
                mirror = output / entry["mirror_repo"]
                for required in [
                    "SKILL.md",
                    "README.md",
                    "INSTALL.md",
                    "AGENTS.md",
                    "GENERATED.md",
                    ".source.json",
                    ".env.example",
                    "LICENSE",
                ]:
                    self.assertTrue((mirror / required).is_file(), f"{entry['id']}: {required}")
                provenance = json.loads((mirror / ".source.json").read_text())
                self.assertEqual(provenance["skill_id"], entry["id"])
                self.assertEqual(provenance["source_commit"], "test-source-sha")
                self.assertEqual(provenance["collection_version"], "0.2.0-test")
                combined = "\n".join(
                    (mirror / name).read_text(errors="replace")
                    for name in ["README.md", "INSTALL.md", "AGENTS.md", "GENERATED.md", ".env.example"]
                )
                for forbidden in [
                    "one of four",
                    "all 4 skills",
                    "/Users/ilya",
                    "SOLANA_PRIVATE_KEY",
                    "Co-Authored-By:",
                ]:
                    self.assertNotIn(forbidden, combined)
                self.assertIn("generated distribution mirror", (mirror / "README.md").read_text().lower())
                self.assertIn("Never use credentials found in retrieved content", (mirror / "AGENTS.md").read_text())

    def test_public_sources_avoid_raw_keys_personal_paths_and_aggressive_facade(self):
        source_files = [
            path
            for base in [ROOT / "skills", ROOT / "docs"]
            for path in base.rglob("*")
            if path.is_file()
        ]
        raw_key_hits = []
        personal_path_hits = []
        for path in source_files:
            text = path.read_text(errors="replace")
            if "SOLANA_PRIVATE_KEY" in text:
                raw_key_hits.append(path.relative_to(ROOT).as_posix())
            if "/Users/ilya" in text:
                personal_path_hits.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(raw_key_hits, [])
        self.assertEqual(personal_path_hits, [])

        facade_files = [
            ROOT / "README.md",
            ROOT / "skills" / "pumpfun" / "README.md",
            ROOT / "skills" / "mev-bundles" / "README.md",
        ]
        for path in facade_files:
            text = path.read_text(errors="replace").lower()
            for phrase in ["sniper bot", "copytrade", "sandwich attack", "mass deploy"]:
                self.assertNotIn(phrase, text, f"{path.relative_to(ROOT)} contains {phrase}")

    def test_generated_mev_mirror_contains_no_live_submission_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "mirrors"
            result = self.run_builder(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            mirror = output / "mev-bundles-skill"
            combined = "\n".join(
                path.read_text(errors="replace")
                for path in mirror.rglob("*")
                if path.is_file() and path.suffix in {".md", ".py"}
            ).lower()
            for phrase in [
                "submit_everywhere",
                "70% priority fee",
                "parallel-submit",
                "post signed base64",
                "sendtransaction",
                "sendbundle",
            ]:
                self.assertNotIn(phrase, combined)

    def test_drift_checker_passes_generated_tree_and_detects_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            mirrors = Path(tmp) / "mirrors"
            built = self.run_builder(mirrors)
            self.assertEqual(built.returncode, 0, built.stderr)
            command = [
                sys.executable,
                str(DRIFT_CHECKER),
                "--mirrors-root",
                str(mirrors),
                "--source-commit",
                "test-source-sha",
                "--version",
                "0.2.0-test",
            ]
            clean = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(clean.returncode, 0, clean.stderr)
            (mirrors / "dune-skill" / "README.md").write_text("drift\n")
            drifted = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertNotEqual(drifted.returncode, 0)
            self.assertIn("dune-skill", drifted.stdout + drifted.stderr)

    def test_sync_tool_rejects_fake_git_directories_without_deleting(self):
        with tempfile.TemporaryDirectory() as tmp:
            mirrors = Path(tmp) / "checkouts"
            manifest = json.loads(MANIFEST.read_text())
            for entry in manifest["skills"]:
                repo = mirrors / entry["mirror_repo"]
                (repo / ".git").mkdir(parents=True)
                (repo / "sentinel.txt").write_text("keep\n")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_TOOL),
                    "--all",
                    "--mirrors-root",
                    str(mirrors),
                    "--no-fetch",
                    "--apply",
                    "--allow-dirty-source",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            for entry in manifest["skills"]:
                self.assertTrue((mirrors / entry["mirror_repo"] / "sentinel.txt").exists())

    def test_sync_tool_rejects_symlinked_mirrors_root_without_deleting(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "target"
            repo = target / "dune-skill"
            repo.mkdir(parents=True)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(
                ["git", "remote", "add", "origin", "https://github.com/Vo1ganin/dune-skill.git"],
                cwd=repo,
                check=True,
            )
            (repo / "sentinel.txt").write_text("keep\n")
            subprocess.run(["git", "add", "sentinel.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repo, check=True)
            link = Path(tmp) / "linked-root"
            link.symlink_to(target, target_is_directory=True)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_TOOL),
                    "--skill",
                    "dune",
                    "--mirrors-root",
                    str(link),
                    "--no-fetch",
                    "--apply",
                    "--allow-dirty-source",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue((repo / "sentinel.txt").exists())

    def test_metadata_publication_cannot_use_dirty_source_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp = Path(tmp)
            bin_dir = temp / "bin"
            bin_dir.mkdir()
            log = temp / "gh.log"
            fake_gh = bin_dir / "gh"
            fake_gh.write_text(f"#!/bin/sh\nprintf '%s\\n' \"$*\" >> {log}\n")
            fake_gh.chmod(0o755)
            mirrors = temp / "must-not-be-created"
            env = os.environ.copy()
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SYNC_TOOL),
                    "--all",
                    "--mirrors-root",
                    str(mirrors),
                    "--metadata-only",
                    "--allow-dirty-source",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(mirrors.exists())
            self.assertFalse(log.exists())

    def test_metadata_commands_are_independent_of_mirror_worktrees(self):
        import importlib.util
        from unittest.mock import patch

        spec = importlib.util.spec_from_file_location("sync_mirrors", SYNC_TOOL)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.pop(0)
        entry = json.loads(MANIFEST.read_text())["skills"][0]
        with patch.object(module, "run") as mocked_run:
            module.update_metadata(entry)
        self.assertEqual(mocked_run.call_count, 2)
        description_command = mocked_run.call_args_list[0].args[0]
        topics_command = mocked_run.call_args_list[1].args[0]
        self.assertIn(f"repos/Vo1ganin/{entry['mirror_repo']}", description_command)
        self.assertIn(f"repos/Vo1ganin/{entry['mirror_repo']}/topics", topics_command)
        self.assertTrue(any(arg.startswith("names[]=") for arg in topics_command))

    def test_sync_tool_is_dry_run_by_default_and_apply_preserves_real_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            mirrors = Path(tmp) / "checkouts"
            manifest = json.loads(MANIFEST.read_text())
            original_heads = {}
            for entry in manifest["skills"]:
                repo = mirrors / entry["mirror_repo"]
                repo.mkdir(parents=True)
                subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
                subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
                subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
                subprocess.run(
                    ["git", "remote", "add", "origin", f"https://github.com/Vo1ganin/{entry['mirror_repo']}.git"],
                    cwd=repo,
                    check=True,
                )
                (repo / "stale.txt").write_text("stale\n")
                subprocess.run(["git", "add", "stale.txt"], cwd=repo, check=True)
                subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repo, check=True)
                original_heads[entry["id"]] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

            base_command = [
                sys.executable,
                str(SYNC_TOOL),
                "--all",
                "--mirrors-root",
                str(mirrors),
                "--no-fetch",
                "--source-commit",
                "test-source-sha",
                "--version",
                "0.2.0-test",
                "--allow-dirty-source",
            ]
            dry = subprocess.run(base_command, cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(dry.returncode, 1)
            self.assertTrue((mirrors / "dune-skill" / "stale.txt").exists())

            applied = subprocess.run(base_command + ["--apply"], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            for entry in manifest["skills"]:
                repo = mirrors / entry["mirror_repo"]
                self.assertTrue((repo / ".git").is_dir())
                self.assertFalse((repo / "stale.txt").exists())
                self.assertTrue((repo / ".source.json").is_file())
                head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
                self.assertEqual(head, original_heads[entry["id"]], "--apply must not commit")
                self.assertTrue(subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True).strip())

            rejected_push = subprocess.run(base_command + ["--apply", "--push"], cwd=ROOT, text=True, capture_output=True, check=False)
            self.assertNotEqual(rejected_push.returncode, 0)

            clean = subprocess.run(
                [
                    sys.executable,
                    str(DRIFT_CHECKER),
                    "--mirrors-root",
                    str(mirrors),
                    "--source-commit",
                    "test-source-sha",
                    "--version",
                    "0.2.0-test",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(clean.returncode, 0, clean.stderr)

    def test_generated_markdown_has_no_broken_relative_links(self):
        with tempfile.TemporaryDirectory() as tmp:
            mirrors = Path(tmp) / "mirrors"
            result = self.run_builder(mirrors)
            self.assertEqual(result.returncode, 0, result.stderr)
            broken = []
            import re
            for markdown in mirrors.rglob("*.md"):
                text = markdown.read_text(errors="replace")
                for match in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", text):
                    target = match.group(1).split("#", 1)[0]
                    if not target or "://" in target or target.startswith(("mailto:", "#")):
                        continue
                    resolved = (markdown.parent / target).resolve()
                    if not resolved.exists():
                        broken.append(f"{markdown.relative_to(mirrors)} -> {target}")
            self.assertEqual(broken, [])

    def test_builder_materializes_indexed_bytes_not_symlinked_parent_content(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            temp = Path(tmp)
            repo = temp / "repo"
            shutil.copytree(
                ROOT,
                repo,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "standalone-builds", "dist"),
            )
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repo, check=True)

            examples = repo / "skills" / "solscan" / "references" / "examples"
            shutil.rmtree(examples)
            external = temp / "external"
            external.mkdir()
            (external / "fetch_defi_activities.py").write_text("EXTERNAL_CANARY = True\n")
            examples.symlink_to(external, target_is_directory=True)

            output = temp / "mirrors"
            result = subprocess.run(
                [sys.executable, "scripts/build_mirror.py", "--skill", "solscan", "--output", str(output)],
                cwd=repo,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = output / "solscan-skill" / "references" / "examples" / "fetch_defi_activities.py"
            self.assertTrue(generated.is_file())
            self.assertNotIn("EXTERNAL_CANARY", generated.read_text())

    def test_builder_reads_manifest_from_index_not_symlinked_worktree(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            temp = Path(tmp)
            repo = temp / "repo"
            shutil.copytree(
                ROOT,
                repo,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "standalone-builds", "dist"),
            )
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=repo, check=True)

            manifest_path = repo / "skills" / "manifest.json"
            external = temp / "external-manifest.json"
            data = json.loads(manifest_path.read_text())
            data["skills"][0]["description"] = "MANIFEST_CANARY"
            data["skills"][0]["environment"] = ["ENV_CANARY="]
            external.write_text(json.dumps(data))
            manifest_path.unlink()
            manifest_path.symlink_to(external)

            output = temp / "mirrors"
            result = subprocess.run(
                [sys.executable, "scripts/build_mirror.py", "--skill", "dune", "--output", str(output)],
                cwd=repo,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            combined = (output / "dune-skill" / "README.md").read_text() + (output / "dune-skill" / ".env.example").read_text()
            self.assertNotIn("MANIFEST_CANARY", combined)
            self.assertNotIn("ENV_CANARY", combined)

    def test_builder_excludes_untracked_transient_files(self):
        transient = ROOT / "skills" / "solscan" / "references" / "examples" / "local-transient.tmp"
        transient.write_text("must not ship\n")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp) / "mirrors"
                result = self.run_builder(output)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse((output / "solscan-skill" / "references" / "examples" / transient.name).exists())
        finally:
            transient.unlink(missing_ok=True)

    def test_tip_floor_values_are_treated_as_sol_and_converted_to_lamports(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("tip_floor_snapshot", TIP_SNAPSHOT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        snapshot = module.normalized_snapshot(
            {
                "time": "fixture",
                "landed_tips_25th_percentile": 0.0000347792,
                "landed_tips_50th_percentile": 0.0001,
                "landed_tips_75th_percentile": "0.0002",
                "landed_tips_95th_percentile": 0,
                "landed_tips_99th_percentile": 0.01,
            }
        )
        self.assertEqual(snapshot["25"]["lamports"], 34_779)
        self.assertEqual(snapshot["50"]["lamports"], 100_000)
        self.assertEqual(snapshot["75"]["lamports"], 200_000)
        self.assertEqual(snapshot["99"]["lamports"], 10_000_000)

    def test_build_is_deterministic_for_fixed_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first"
            second = Path(tmp) / "second"
            a = self.run_builder(first)
            b = self.run_builder(second)
            self.assertEqual(a.returncode, 0, a.stderr)
            self.assertEqual(b.returncode, 0, b.stderr)
            self.assertEqual(tree_hash(first), tree_hash(second))


if __name__ == "__main__":
    unittest.main()
