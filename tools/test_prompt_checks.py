"""Unit tests for the definition-of-done checks."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import prompt_checks  # noqa: E402

REPO = Path(__file__).resolve().parent.parent

STATUS_OK = (
    '{"ok":true,"command":"status","result":{"changes":[],"coverage":{"constraints":0,'
    '"intents_active":5,"intents_implemented":5,"intents_total":5,"notions":5,'
    '"scenarios_proved":9,"scenarios_total":9},"drift":null,"proof_evidence":"report",'
    '"state":"coherent"},"error":null,"next_actions":[]}'
)
SEALED_OK = '{"ok":true,"command":"check","result":{"diagnostics":[]},"error":null,"next_actions":[]}'
GAME = " 1 | 2 | 3\n 4 | X | 6\n 7 | 8 | 9\nO to play\n> X wins\n"


class FakeRun:
    """Answers commands from a table keyed by their first three words."""

    def __init__(self, table: dict[str, tuple[str, int]]) -> None:
        self.table = table
        self.calls: list[tuple[list[str], str | None]] = []

    def __call__(self, argv, cwd, env, stdin=None):
        self.calls.append((list(argv), stdin))
        stdout, code = self.table.get(" ".join(argv[:3]), ("", 0))
        return subprocess.CompletedProcess(argv, code, stdout=stdout, stderr="")


def green_table() -> dict[str, tuple[str, int]]:
    return {
        "telos status --json": (STATUS_OK, 0),
        "telos check --sealed": (SEALED_OK, 0),
        "git status --porcelain": ("", 0),
        "git tag --points-at": ("v0.1.0\n", 0),
        "pytest -q": ("9 passed\n", 0),
        "python3 -m tictactoe": (GAME, 0),
    }


class LoadChecksTest(unittest.TestCase):
    def test_reads_the_repository_checks(self) -> None:
        checks = prompt_checks.load_checks(REPO / "prompts" / "checks.toml")
        self.assertEqual("tictactoe", checks.module)
        first = checks.prompts["01-board-and-console"]
        self.assertEqual("v0.1.0", first.tag)
        self.assertEqual(5, first.intents)
        self.assertEqual(9, first.scenarios)
        self.assertEqual("report", first.proof_evidence)
        self.assertEqual("5\n1\n4\n2\n6\n", first.play.input)
        self.assertEqual((" 4 | X | 6", "X wins"), first.play.expect)
        self.assertEqual("revert", checks.prompts["05-hotfix"].human_action)
        self.assertEqual(("--help",), checks.prompts["04-window"].help.args)

    def test_every_prompt_with_a_table_exists_and_the_open_prompt_has_none(self) -> None:
        checks = prompt_checks.load_checks(REPO / "prompts" / "checks.toml")
        stems = {p.stem for p in (REPO / "prompts").glob("[0-9][0-9]-*.md")}
        self.assertTrue(set(checks.prompts) <= stems, set(checks.prompts) - stems)
        self.assertEqual({"06-your-turn"}, stems - set(checks.prompts))


class RunChecksTest(unittest.TestCase):
    def setUp(self) -> None:
        self.check = prompt_checks.PromptCheck(
            stem="01-board-and-console", tag="v0.1.0", intents=5, scenarios=9,
            proof_evidence="report",
            play=prompt_checks.Play(input="5\n", expect=(" 4 | X | 6", "X wins")),
        )
        self.tmp = tempfile.TemporaryDirectory()
        self.target = Path(self.tmp.name)
        (self.target / "tests").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_with(self, table):
        run = FakeRun(table)
        failures = prompt_checks.run_checks(self.check, self.target, {}, "tictactoe", run=run)
        return failures, run

    def test_all_green_passes_and_feeds_the_game(self) -> None:
        failures, run = self.run_with(green_table())
        self.assertEqual([], failures)
        play = [call for call in run.calls if call[0][:3] == ["python3", "-m", "tictactoe"]]
        self.assertEqual("5\n", play[0][1])

    def test_a_wrong_count_names_the_key(self) -> None:
        table = green_table()
        table["telos status --json"] = (STATUS_OK.replace('"intents_active":5', '"intents_active":4'), 0)
        failures, _ = self.run_with(table)
        self.assertIn("intents_active is 4, expected 5", failures)

    def test_drift_fails_the_state_check(self) -> None:
        table = green_table()
        table["telos status --json"] = (STATUS_OK.replace('"coherent"', '"drifted"'), 0)
        failures, _ = self.run_with(table)
        self.assertTrue(any("expected 'coherent'" in f for f in failures), failures)

    def test_missing_tag_and_dirty_tree_are_reported(self) -> None:
        table = green_table()
        table["git tag --points-at"] = ("", 0)
        table["git status --porcelain"] = (" M tictactoe/domain/board.py\n", 0)
        failures, _ = self.run_with(table)
        self.assertTrue(any("v0.1.0" in f for f in failures), failures)
        self.assertTrue(any("not clean" in f for f in failures), failures)

    def test_missing_console_text_is_reported(self) -> None:
        table = green_table()
        table["python3 -m tictactoe"] = ("nothing here\n", 0)
        failures, _ = self.run_with(table)
        self.assertTrue(any("play:" in f and "X wins" in f for f in failures), failures)

    def test_pytest_is_skipped_without_a_tests_directory(self) -> None:
        (self.target / "tests").rmdir()
        failures, run = self.run_with(green_table())
        self.assertEqual([], failures)
        self.assertFalse(any(call[0][:2] == ["pytest", "-q"] for call in run.calls))


if __name__ == "__main__":
    unittest.main()
