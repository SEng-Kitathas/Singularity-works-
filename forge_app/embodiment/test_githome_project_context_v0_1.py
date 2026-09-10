from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from forge_app.hud.workbench_model import WorkbenchInteractionState, build_workbench_model
from forge_app.shell.githome_model import (
    GitHomeInteractionState,
    GitHomeModelError,
    apply_githome_command,
    build_githome_model,
    inspect_project,
    render_githome_text,
)
from singularity_works.semantic_field import EvidenceSpan, SemanticFact, SemanticFactBundle, SourceReferent, freeze_bundle


class GitHomeProjectContextV01Tests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
        return result.stdout.strip()

    def git_fixture(self, td: str) -> Path:
        repo = Path(td) / "project"
        repo.mkdir()
        self.git(repo, "init")
        self.git(repo, "config", "user.email", "githome-test@example.invalid")
        self.git(repo, "config", "user.name", "GitHome Test")
        (repo / ".gitignore").write_text("*.tmp\n", encoding="utf-8")
        (repo / "clean.txt").write_text("clean\n", encoding="utf-8")
        (repo / "modified.txt").write_text("before\n", encoding="utf-8")
        (repo / "staged.txt").write_text("before\n", encoding="utf-8")
        (repo / "deleted.txt").write_text("before\n", encoding="utf-8")
        (repo / "nested").mkdir()
        (repo / "nested" / "tracked.py").write_text("value = 1\n", encoding="utf-8")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", "fixture")

        (repo / "modified.txt").write_text("after\n", encoding="utf-8")
        (repo / "staged.txt").write_text("after\n", encoding="utf-8")
        self.git(repo, "add", "staged.txt")
        (repo / "deleted.txt").unlink()
        (repo / "untracked.txt").write_text("new\n", encoding="utf-8")
        (repo / "ignored.tmp").write_text("ignored\n", encoding="utf-8")
        return repo

    def workbench_fixture(self):
        text = "def hello():\n    return 'hi'\n"
        source = SourceReferent.from_text("demo.py", "python", text)
        bundle = SemanticFactBundle(producer="githome-test")
        bundle.add_source(source)
        evidence = EvidenceSpan.from_lines(source, text, 1, 2)
        bundle.add_evidence(evidence)
        entity = bundle.add_entity(kind="function", name="hello", source_id=source.source_id, evidence_id=evidence.evidence_id)
        bundle.add_fact(
            SemanticFact.create(
                subject_id=entity,
                predicate="returns_literal",
                object_value="hi",
                evidence_ids=[evidence.evidence_id],
                evidence_status="parsed",
                producer="githome-test",
                assurance_ceiling="FIXTURE_ONLY",
            )
        )
        frozen = freeze_bundle(bundle, {source.path: text})
        return build_workbench_model(frozen, currentness="MATCH", state=WorkbenchInteractionState(selected_entity_id=entity))

    def test_git_snapshot_keeps_clean_modified_staged_untracked_ignored_and_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self.git_fixture(td)
            snapshot = inspect_project(repo)
            files = {entry.path: entry for entry in snapshot.entries if entry.kind != "directory"}
            self.assertTrue(snapshot.git_available)
            self.assertIsNotNone(snapshot.head)
            self.assertIsNotNone(snapshot.branch)
            self.assertTrue(snapshot.dirty)
            self.assertEqual(files["clean.txt"].git_state, "CLEAN")
            self.assertEqual(files["modified.txt"].git_state, "MODIFIED")
            self.assertEqual(files["staged.txt"].git_state, "STAGED")
            self.assertEqual(files["untracked.txt"].git_state, "UNTRACKED")
            self.assertEqual(files["ignored.tmp"].git_state, "IGNORED")
            self.assertEqual(files["deleted.txt"].git_state, "DELETED")
            self.assertFalse(files["deleted.txt"].exists)
            self.assertTrue(files["deleted.txt"].tracked)
            self.assertEqual(snapshot.ignored_file_count, 1)
            self.assertEqual(snapshot.untracked_file_count, 1)
            self.assertEqual(snapshot.changed_tracked_file_count, 3)

    def test_snapshot_excludes_git_internals_but_keeps_project_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self.git_fixture(td)
            snapshot = inspect_project(repo)
            paths = {entry.path for entry in snapshot.entries}
            self.assertIn(".", paths)
            self.assertIn("nested", paths)
            self.assertIn("nested/tracked.py", paths)
            self.assertFalse(any(path == ".git" or path.startswith(".git/") for path in paths))
            root = next(entry for entry in snapshot.entries if entry.path == ".")
            self.assertEqual(root.descendant_file_count, snapshot.file_count)
            nested = next(entry for entry in snapshot.entries if entry.path == "nested")
            self.assertEqual(nested.descendant_file_count, 1)

    def test_default_model_hides_ignored_only_from_projection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            snapshot = inspect_project(self.git_fixture(td))
            hidden = build_githome_model(snapshot)
            shown = build_githome_model(snapshot, state=GitHomeInteractionState(show_ignored=True))
            self.assertFalse(any(entry.path == "ignored.tmp" for entry in hidden.visible_entries))
            self.assertTrue(any(entry.path == "ignored.tmp" for entry in shown.visible_entries))
            self.assertEqual(hidden.total_entry_count, shown.total_entry_count)
            self.assertEqual(snapshot.ignored_file_count, 1)

    def test_selection_filter_and_breadcrumb_never_mint_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            snapshot = inspect_project(self.git_fixture(td))
            state = GitHomeInteractionState(query="tracked.py", selected_path="nested/tracked.py")
            model = build_githome_model(snapshot, state=state)
            self.assertEqual([entry.path for entry in model.visible_entries], ["nested/tracked.py"])
            self.assertEqual(model.breadcrumb, ("nested", "tracked.py"))
            self.assertEqual(model.selected_entry.path, "nested/tracked.py")
            self.assertEqual(model.total_entry_count, len(snapshot.entries))
            with self.assertRaisesRegex(GitHomeModelError, "unknown project path"):
                build_githome_model(snapshot, state=GitHomeInteractionState(selected_path="invented/path.py"))

    def test_snapshot_and_model_identity_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self.git_fixture(td)
            first = inspect_project(repo)
            second = inspect_project(repo)
            self.assertEqual(first.canonical_json(), second.canonical_json())
            self.assertEqual(first.snapshot_sha256, second.snapshot_sha256)
            m1 = build_githome_model(first, state=GitHomeInteractionState(show_ignored=True))
            m2 = build_githome_model(second, state=GitHomeInteractionState(show_ignored=True))
            self.assertEqual(m1.canonical_json(), m2.canonical_json())
            self.assertEqual(m1.model_sha256, m2.model_sha256)

    def test_non_git_project_remains_visible_without_fabricated_git_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "plain"
            root.mkdir()
            (root / "notes.txt").write_text("hello\n", encoding="utf-8")
            (root / "folder").mkdir()
            (root / "folder" / "data.bin").write_bytes(b"abc")
            snapshot = inspect_project(root)
            self.assertFalse(snapshot.git_available)
            self.assertIsNone(snapshot.head)
            self.assertIsNone(snapshot.branch)
            self.assertIsNone(snapshot.dirty)
            files = [entry for entry in snapshot.entries if entry.kind != "directory"]
            self.assertEqual({entry.git_state for entry in files}, {"NOT_GIT"})
            self.assertEqual(snapshot.file_count, 2)

    def test_workbench_binding_is_hash_only_and_authority_none(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            snapshot = inspect_project(self.git_fixture(td))
            workbench = self.workbench_fixture()
            model = build_githome_model(snapshot, workbench=workbench)
            self.assertIsNotNone(model.workbench)
            assert model.workbench is not None
            self.assertEqual(model.workbench.model_sha256, workbench.model_sha256)
            self.assertEqual(model.workbench.source_bundle_id, workbench.source_bundle_id)
            self.assertEqual(model.workbench.currentness, "MATCH")
            self.assertEqual(model.workbench.projection_authority, "NONE")
            self.assertEqual(model.project_observer_authority, "NONE")
            self.assertEqual(model.projection_authority, "NONE")
            payload = model.as_dict()
            self.assertNotIn("facts", payload)
            self.assertNotIn("unknowns", payload)

    def test_readonly_commands_reject_git_mutation_and_unknown_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            snapshot = inspect_project(self.git_fixture(td))
            state = GitHomeInteractionState()
            for verb in ("add", "commit", "checkout", "reset", "clean", "push", "pull", "fetch", "merge", "rebase"):
                result = apply_githome_command(state, f"{verb} anything", snapshot=snapshot)
                self.assertFalse(result.accepted, verb)
                self.assertEqual(result.consequence_scope, "DISABLED", verb)
            missing = apply_githome_command(state, "select not/there.py", snapshot=snapshot)
            self.assertFalse(missing.accepted)
            selected = apply_githome_command(state, "select nested/tracked.py", snapshot=snapshot)
            self.assertTrue(selected.accepted)
            found = apply_githome_command(selected.state, "find MODIFIED", snapshot=snapshot)
            self.assertTrue(found.accepted)
            shown = apply_githome_command(found.state, "show-ignored", snapshot=snapshot)
            self.assertTrue(shown.accepted)
            self.assertTrue(shown.state.show_ignored)

    def test_text_renderer_keeps_project_and_workbench_authority_visible(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            snapshot = inspect_project(self.git_fixture(td))
            workbench = self.workbench_fixture()
            model = build_githome_model(snapshot, state=GitHomeInteractionState(selected_path="modified.txt"), workbench=workbench)
            text = render_githome_text(model, width=120)
            self.assertIn("SINGULARITY WORKS / GITHOME", text)
            self.assertIn("AUTHORITY NONE/NONE", text)
            self.assertIn("FORGE", text)
            self.assertIn("CURRENTNESS MATCH", text)
            self.assertIn("SELECTED modified.txt", text)


if __name__ == "__main__":
    unittest.main()
