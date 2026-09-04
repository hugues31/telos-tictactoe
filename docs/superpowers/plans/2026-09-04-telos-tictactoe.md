# Telos Tic-Tac-Toe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild this repository as `telos-tictactoe`: six plain-text prompts, an agent runner that replays them and checks each outcome, a reference build produced by that runner on Telos v0.13.0, and the README, CI and recorder retargeted to it.

**Architecture:** The prompts are the product; the runner (`tools/run_prompts.py` + `tools/prompt_checks.py`, stdlib only) sends them to `claude -p` or `codex exec`, plays the human for approvals and reverts, and checks `prompts/checks.toml`. The reference repository is the runner's output, adopted as the new `main` with one final commit adding the project-level files. Nothing under `telos/` is ever written by hand.

**Tech Stack:** Python 3.11+ stdlib (`tomllib`, `subprocess`, `urllib`), pytest in `.venv`, Telos 0.13.0 release binary, Claude Code CLI (`claude -p`), Codex CLI (best effort), Playwright + ffmpeg for the GIF, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-04-telos-tictactoe-design.md`

## Status on 2026-09-04

Tasks 1 to 8 are done. The Claude spike of Task 4 ran prompt 00 (pass,
0.33 USD) and prompt 01 (all nine scenarios witnessed and bound, then
stopped by the 15 USD cap before reconcile; 8.64 USD); the agent had merged
rules 3 and 4 into one intent, so prompts 01 and 02 now say "one intent per
numbered rule". The user then chose Codex (`gpt-5.6-sol`, their default
model) for the reference build. That build surfaced three runner changes,
all in place: Codex runs with `--sandbox danger-full-access` because
`workspace-write` mounts `.git` read-only and reconcile could not seal
(upstream issue hugues31/telos-sdd#33); the runner adopts a code edit made
outside the change's claims and re-approves the stale digest; every prompt
carries a note that the hooks are trusted, and failed checks are read back
to the agent. A first reference passed prompts 00 to 05, but playing the
window showed three gaps the checks cannot see: the window kept accepting
clicks after a finished round, the misère result read as a wrong winner,
and the layout did not resize. Prompts 03 and 04 were revised (the status
names who lined up three; rule 10 makes the window play whole matches; a
resizable layout), prompts 03 to 05 were replayed from `v0.2.0`, and the
window was checked by screenshot (`docs/window.png`). The final reference
has 10 intents and 18 scenarios and is branch `tictactoe`, with the final
commit of this plan on top. What remains is Task 9, with the user's
explicit go; the `git checkout ... --` command of Task 8 was run against
the first assembly (`tictactoe-v1`), and the target was
`.worktrees/run-codex`.

## Global Constraints

- Telos pin everywhere: `v0.13.0`, assets `telos_0.13.0_<os>_<arch>.tar.gz`, installer `TELOS_VERSION=v0.13.0`.
- Test runner in the reference: `pytest -q --junitxml={report} -k '{filter}'`, `report = "junit.xml"`, `junit.xml` gitignored and outside every glob.
- `agents.hosts = ["claude", "codex"]`; generated files (`.claude/`, `.agents/`, `.codex/`, `AGENTS.md`, `.gitattributes`, `.github/workflows/telos.yml`) are never edited by hand.
- Enum symbols lowercase (`x`, `o`, `x-wins`): Telos 0.13.0 corrupts a change file on an uppercase symbol (upstream issue hugues31/telos-sdd#29).
- Prompts: English, one screen, no CLI commands and no payloads except where the prompt is about Telos itself (05, 06). README under 100 lines. No metaphors, no jokes; Telos terms only.
- The Telos agent guard installed in this session refuses every write outside the repository (including `/tmp` and the scratchpad), pipes, `&&`, redirections and `python3 -c`. Work under `.worktrees/` (gitignored) and run script files. The 0.13.0 binary is at `.worktrees/lab/bin/telos`.
- Never edit `telos/` by hand, in this repository or in any runner target. Never force-push or rename the repository without the user's explicit go (Task 9).
- Claude headless runs are capped at 15 USD in total across Tasks 4 and 7.

---

### Task 1: The prompts and their definition of done

**Files:**
- Create: `prompts/00-setup.md`, `prompts/01-board-and-console.md`, `prompts/02-tournament.md`, `prompts/03-misere.md`, `prompts/04-window.md`, `prompts/05-hotfix.md`, `prompts/06-your-turn.md`, `prompts/checks.toml`
- Delete: `prompts/00-bootstrap.md`, `prompts/01-hatch-and-feed.md`, `prompts/02-play-and-mood.md`, `prompts/03-time-and-sleep.md`, `prompts/04-neglect-and-death.md`, `prompts/05-evolution-and-cli.md`, `prompts/06-the-drift-incident.md`, `prompts/07-your-turn.md`

**Interfaces:**
- Produces: `prompts/checks.toml` with a `[runner]` table (`module = "tictactoe"`) and one table per prompt stem, read by `load_checks` in Task 2.

- [ ] **Step 1: Remove the old prompts**

```bash
git rm -q prompts/00-bootstrap.md prompts/01-hatch-and-feed.md prompts/02-play-and-mood.md prompts/03-time-and-sleep.md prompts/04-neglect-and-death.md prompts/05-evolution-and-cli.md prompts/06-the-drift-incident.md prompts/07-your-turn.md
```

- [ ] **Step 2: Write `prompts/00-setup.md`**

````markdown
# 00 — Set up the project

This directory is an empty git repository. I want to build a tic-tac-toe
game in Python, spec-first, with Telos.

Initialise this repository as a Telos project with the agent skills for
Claude Code and Codex and the GitHub CI gate. Add a `.gitignore` for Python
(`__pycache__/`, `.pytest_cache/`, `.venv/`) that also ignores `junit.xml`,
the test report Telos will read.

Commit everything with the message `v0.0: empty spec` and tag the commit
`v0.0.0`. Nothing else for now.
````

- [ ] **Step 3: Write `prompts/01-board-and-console.md`**

````markdown
# 01 — One round, in the terminal

The Telos project is initialised and sealed, empty. Build the first version
of the game: one round of tic-tac-toe, two players at the same keyboard.
Follow the Telos skills installed in this repository.

## Domain

Two bounded contexts:

- `board` (core), capability `play`: the grid, the turns, the outcome of a
  round. A `Board` has `cells` (a string of nine characters, row by row,
  `.` for a free cell, `X` or `O`), a `turn` (`x` or `o`) and an `outcome`
  (`playing`, `x-wins`, `o-wins`, `draw`). A `PlaceMark` event carries a
  `cell` number from 1 to 9.
- `terminal` (supporting), capability `console`: what the console shows.
  It reads the board through a `BoardView` mapped from `board/Board` in
  the context map. A `Screen` has `row1`, `row2`, `row3` and `status`; a
  `ShowBoard` event asks for it.

Enum symbols are lowercase.

## Rules, with the examples that become the scenarios

1. A mark goes on a free cell and the turn passes. From `.........` with X
   to play, cell 5 gives `....X....` with O to play. From there, cell 1
   gives `O...X....` with X to play.
2. An occupied cell is refused: the board and the turn do not change. From
   `....X....` with O to play, cell 5 changes nothing.
3. Three in a row wins. `XX.OO....` then cell 3 is `x-wins`; `XO.XO....`
   then cell 7 is `x-wins`; `XO.OX....` then cell 9 is `x-wins`.
4. A full board without a line is a draw: `XOXXOOOX.` then cell 9.
5. The console shows the grid with free cells numbered and who plays. For
   `....X....` with O to play, the middle row reads ` 4 | X | 6` and the
   status is `O to play`. For `XXXOO....` won by X, the status is `X wins`.

## Code and tests

- `tictactoe/domain/board.py` for the `board` context and
  `tictactoe/ui/cli.py` for the `terminal` context; these two files are
  the spec's code globs. `tictactoe/__main__.py` is glue outside the spec:
  it runs the console loop.
- Tests under `tests/`, one function per scenario, named after it
  (`scn_0001_...`); configure pytest to collect `scn_*` functions. Keep
  `tests/` to scenario test files only. Runner:
  `pytest -q --junitxml={report} -k '{filter}'` with the report at
  `junit.xml`, strict TDD.
- Console contract: after every move print the three rows, then the
  status, then prompt with `> `. Occupied cell: print `Cell 5 is taken`
  and prompt again. The round ends after `X wins`, `O wins` or `Draw`. If
  the input ends, exit quietly.

Open a change, stage it, show me the diff and wait for my approval before
implementing. Then red witness, code, green witness, bind, reconcile.
Commit as `v0.1: one round in the terminal` and tag `v0.1.0`.
````

- [ ] **Step 4: Write `prompts/02-tournament.md`**

````markdown
# 02 — A match

One round works. Now a match: two players play rounds until one of them
has won two. Follow the Telos skills installed in this repository.

## Domain

A new core context `tournament`, capability `standings`, that depends on
`board` in the context map (`board/Board` mapped to
`tournament/RoundResult`):

- `Match`: `x-points`, `o-points`, `target` (2), `winner` (`none`, `x`,
  `o`) and `starter` (`x` or `o`, who starts the next round).
- `RoundResult`: an `outcome` (`x-wins`, `o-wins`, `draw`).
- `RoundEnded` event.

## Rules and examples

6. A won round gives its winner a point, a draw gives none. From 0-0,
   `x-wins` gives `x-points` 1. From 0-0, a draw leaves 0-0.
7. The first player to reach the target wins the match. From 1-0 with
   target 2, `x-wins` makes X the winner.
8. The loser of a round starts the next one. After `x-wins` with starter
   `x`, the starter is `o`.

The console shows the score. Map `tournament/Match` to
`terminal/MatchView` and give `Screen` a `score`: for 1-0 it reads
`X 1 - 0 O`. Grow the existing console intent with that scenario; do not
add a new intent for it.

## Code

- `tictactoe/domain/tournament.py` joins the code globs.
- Console: start with `Best of 3. X starts.`; after a round print the
  status, the score line, then `Round 2. O starts.` and a fresh grid; end
  with `X wins the match` or `O wins the match`.

Same workflow as before: change, diff, my approval, red, code, green,
bind, reconcile. Commit as `v0.2: a match to two wins` and tag `v0.2.0`.
````

- [ ] **Step 5: Write `prompts/03-misere.md`**

````markdown
# 03 — Misère

Change one rule at the heart of the game: three in a row now loses. The
player who completes a line loses the round, the other one wins. Follow
the Telos skills installed in this repository.

Change the existing intent "Three in a row wins" and its three scenarios;
do not add a new intent. `XX.OO....` then cell 3 is now `o-wins`, and so
are the column and the diagonal examples. Run `telos impact` on that
intent first and tell me what else it touches.

The existing tests are sealed with their red and green witnesses: changing
them means new witnesses. The console messages do not change; with the
same moves, the console now prints `O wins`.

Same workflow: change, diff, my approval, red, code, green, bind,
reconcile. Commit as `v0.3: misère` and tag `v0.3.0`.
````

- [ ] **Step 6: Write `prompts/04-window.md`**

````markdown
# 04 — A window

The game needs a graphical interface with the same logic: a tkinter
window, nine buttons for the cells and one status line, opened with
`python -m tictactoe --gui`. Two players share the mouse. Follow the Telos
skills installed in this repository.

## Domain

A supporting context `desktop`, capability `window`, that depends on
`board` and `tournament` in the context map (`board/Board` mapped to
`desktop/BoardView`, `tournament/Match` mapped to `desktop/MatchView`):

- `Window`: `labels` (nine characters, like the cells) and `status`.
- `CellClicked` event with a `cell`.

9. A click on a free cell plays it and refreshes the window. From
   `.........` with X to play, clicking 5 gives labels `....X....` and
   status `O to play  X 0 - 0 O`. From `XX.OO....` with X to play,
   clicking 3 gives status `O wins  X 0 - 1 O`.

## Architecture

The window's logic lives in a presenter that builds `labels` and `status`
without a display; tkinter only draws what the presenter says, and the
tests prove the presenter. Add a project constraint of kind
`architecture`, "The domain never imports an interface", with the
executable check `python3 tools/check_layers.py`: it exits non-zero if
any module under `tictactoe/domain/` imports `tictactoe.ui`, `tkinter`,
`argparse` or `sys`.

## Code

- `tictactoe/ui/gui.py` joins the code globs. `tictactoe/__main__.py`
  gains `--gui`.

Same workflow: change, diff, my approval, red, code, green, bind,
reconcile. Commit as `v0.4: a window` and tag `v0.4.0`.
````

- [ ] **Step 7: Write `prompts/05-hotfix.md`**

````markdown
# 05 — A hotfix

Do this the wrong way on purpose. Edit `tictactoe/domain/board.py`
directly, without opening a Telos change, so that a player keeps the turn
after playing a mark. Do not touch the tests.

Then run `telos status` and tell me what it reports. Try to open a change
and tell me what happens. Explain the two ways out, `telos adopt` and
`telos revert`, and what each would do with this edit. Take the one that
restores the sealed code; I will confirm it.

Do not commit anything.
````

- [ ] **Step 8: Write `prompts/06-your-turn.md`**

````markdown
# 06 — Your turn

Play a round to the end, then keep typing or clicking: the finished board
still accepts marks. Nothing in the spec says it should not, so the code
does not refuse them. That is a hole in the spec, and the place where
work starts.

State it, prove it, seal it: a finished round ignores every mark.

Suggested path, with the Telos skills installed in this repository:

1. `telos status --json`, always first.
2. `telos change open "a finished round ignores marks" --json`
3. `telos impact NOT:board/Board --json` to see what the change touches.
4. Stage an `unwanted` intent in `board/play` with one scenario per
   outcome, review the diff, approve it with the digest shown.
5. Red witness, minimal code, green witness, bind, reconcile.
6. Commit, and tag `v0.5.0` if you are happy with it.

Further ideas: a computer opponent as a new context that depends on
`board`; undoing the last move; a constraint with an executable check
that no board ever holds two more X than O.
````

- [ ] **Step 9: Write `prompts/checks.toml`**

```toml
# The definition of done for each prompt. tools/run_prompts.py reads it
# after every prompt; a human replaying by hand reads it the same way.
# Counts are what `telos status` reports once the prompt is complete.

[runner]
module = "tictactoe"

["00-setup"]
tag = "v0.0.0"
intents = 0
scenarios = 0

["01-board-and-console"]
tag = "v0.1.0"
intents = 5
scenarios = 9
proof_evidence = "report"
play = { input = "5\n1\n4\n2\n6\n", expect = [" 4 | X | 6", "X wins"] }

["02-tournament"]
tag = "v0.2.0"
intents = 8
scenarios = 14
proof_evidence = "report"
play = { input = "5\n1\n4\n2\n6\n", expect = ["X wins", "X 1 - 0 O", "Round 2. O starts."] }

["03-misere"]
tag = "v0.3.0"
intents = 8
scenarios = 14
proof_evidence = "report"
play = { input = "5\n1\n4\n2\n6\n", expect = ["O wins", "X 0 - 1 O", "Round 2. X starts."] }

["04-window"]
tag = "v0.4.0"
intents = 9
scenarios = 16
constraints = 1
proof_evidence = "report"
play = { input = "5\n1\n4\n2\n6\n", expect = ["O wins", "X 0 - 1 O"] }
help = { args = ["--help"], expect = ["--gui"] }

["05-hotfix"]
human_action = "revert"
intents = 9
scenarios = 16
constraints = 1
```

- [ ] **Step 10: Commit**

```bash
git add prompts
git commit -q -m "feat: six plain-text prompts and their definition of done" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: `tools/prompt_checks.py`

**Files:**
- Create: `tools/prompt_checks.py`
- Test: `tools/test_prompt_checks.py`

**Interfaces:**
- Produces: `load_checks(path: Path) -> Checks` where `Checks(module: str, prompts: dict[str, PromptCheck])`; `PromptCheck(stem, tag, intents, scenarios, constraints, proof_evidence, human_action, play, help)`; `Play(input, args, expect)`; `run_checks(check: PromptCheck, target: Path, env: dict[str, str], module: str, run=run_cmd) -> list[str]` returning the failed checks (empty means pass); `run_cmd(argv, cwd, env, stdin=None) -> subprocess.CompletedProcess`.

- [ ] **Step 1: Write the failing tests**

`tools/test_prompt_checks.py`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m unittest tools.test_prompt_checks`
Expected: `ModuleNotFoundError: No module named 'prompt_checks'`

- [ ] **Step 3: Write `tools/prompt_checks.py`**

```python
"""The definition of done for each prompt, read from prompts/checks.toml.

`run_checks` asks the replayed project the same questions a human would
after finishing a prompt: is Telos coherent with the expected coverage and
proof evidence, does the sealed check pass, is the tree clean and tagged,
do the tests pass, does the console game answer as expected.
"""

from __future__ import annotations

import json
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Play:
    input: str = ""
    args: tuple[str, ...] = ()
    expect: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromptCheck:
    stem: str
    tag: str | None = None
    intents: int | None = None
    scenarios: int | None = None
    constraints: int | None = None
    proof_evidence: str | None = None
    human_action: str | None = None
    play: Play | None = None
    help: Play | None = None


@dataclass(frozen=True)
class Checks:
    module: str
    prompts: dict[str, PromptCheck]


def _play(table: dict | None) -> Play | None:
    if table is None:
        return None
    return Play(
        input=table.get("input", ""),
        args=tuple(table.get("args", ())),
        expect=tuple(table.get("expect", ())),
    )


def load_checks(path: Path) -> Checks:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    runner = data.pop("runner", {})
    prompts = {
        stem: PromptCheck(
            stem=stem,
            tag=table.get("tag"),
            intents=table.get("intents"),
            scenarios=table.get("scenarios"),
            constraints=table.get("constraints"),
            proof_evidence=table.get("proof_evidence"),
            human_action=table.get("human_action"),
            play=_play(table.get("play")),
            help=_play(table.get("help")),
        )
        for stem, table in data.items()
    }
    return Checks(module=runner.get("module", "tictactoe"), prompts=prompts)


Runner = Callable[[list[str], Path, dict, str | None], subprocess.CompletedProcess]


def run_cmd(argv, cwd, env, stdin=None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=cwd, env=env, input=stdin, text=True, capture_output=True)


def _envelope(proc: subprocess.CompletedProcess) -> dict:
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "result": None, "error": {"message": proc.stdout.strip()[:200] or proc.stderr.strip()[:200]}}


def run_checks(check: PromptCheck, target: Path, env: dict, module: str, run: Runner = run_cmd) -> list[str]:
    """Return the failed checks in order; an empty list is a pass."""
    failures: list[str] = []

    status = _envelope(run(["telos", "status", "--json"], target, env, None))
    result = status.get("result") or {}
    if not status.get("ok"):
        failures.append(f"telos status failed: {(status.get('error') or {}).get('message')}")
    if result.get("state") != "coherent":
        failures.append(f"state is {result.get('state')!r}, expected 'coherent'")
    coverage = result.get("coverage") or {}
    expected = {}
    if check.intents is not None:
        expected["intents_active"] = expected["intents_implemented"] = check.intents
    if check.scenarios is not None:
        expected["scenarios_proved"] = expected["scenarios_total"] = check.scenarios
    if check.constraints is not None:
        expected["constraints"] = check.constraints
    for key, value in expected.items():
        if coverage.get(key) != value:
            failures.append(f"{key} is {coverage.get(key)}, expected {value}")
    if check.proof_evidence is not None and result.get("proof_evidence") != check.proof_evidence:
        failures.append(f"proof_evidence is {result.get('proof_evidence')!r}, expected {check.proof_evidence!r}")

    sealed = _envelope(run(["telos", "check", "--sealed", "--json"], target, env, None))
    if not sealed.get("ok"):
        failures.append(f"telos check --sealed failed: {(sealed.get('error') or {}).get('message')}")

    porcelain = run(["git", "status", "--porcelain"], target, env, None).stdout.strip()
    if porcelain:
        failures.append(f"working tree not clean: {porcelain[:200]}")
    if check.tag:
        tags = run(["git", "tag", "--points-at", "HEAD"], target, env, None).stdout.split()
        if check.tag not in tags:
            failures.append(f"tag {check.tag} does not point at HEAD (found {tags})")

    if (target / "tests").is_dir():
        pytest = run(["pytest", "-q"], target, env, None)
        if pytest.returncode != 0:
            last = (pytest.stdout.strip().splitlines() or ["no output"])[-1]
            failures.append(f"pytest -q exited {pytest.returncode}: {last}")

    for name, play in (("play", check.play), ("help", check.help)):
        if play is None:
            continue
        proc = run(["python3", "-m", module, *play.args], target, env, play.input)
        missing = [text for text in play.expect if text not in proc.stdout]
        if missing:
            failures.append(f"{name}: {missing!r} not in the output (exit {proc.returncode})")
    return failures
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m unittest tools.test_prompt_checks`
Expected: `OK` with 8 tests.

- [ ] **Step 5: Commit**

```bash
git add tools/prompt_checks.py tools/test_prompt_checks.py
git commit -q -m "feat: definition-of-done checks for the prompts" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: `tools/run_prompts.py`

**Files:**
- Create: `tools/run_prompts.py`
- Test: `tools/test_run_prompts.py`

**Interfaces:**
- Consumes: `load_checks`, `run_checks`, `PromptCheck`, `Checks` from Task 2.
- Produces: `human_step(target, env, check, telos=telos_json, log=print) -> str | None`; `run_prompt(stem, body, check, target, env, agent, module, max_turns, budget_left, telos=telos_json, checks=run_checks, log=print) -> Outcome`; `select_prompts(prompts_dir, checks, only=None, start=None) -> list[tuple[str, Path]]`; `ClaudeAgent(model).argv(body, session, resume, budget)`; `platform_asset(version, system, machine) -> str`; `ensure_telos(version, cache, log) -> Path`; `main(argv=None) -> int`.

- [ ] **Step 1: Write the failing tests**

`tools/test_run_prompts.py`:

```python
"""Unit tests for the prompt runner, with a fake agent and a fake Telos."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import prompt_checks  # noqa: E402
import run_prompts  # noqa: E402


def status(state, changes=(), drift=None):
    return {"ok": True, "result": {"state": state, "changes": list(changes), "drift": drift}}


class FakeTelos:
    """Answers `telos` calls from a queue of envelopes and records them."""

    def __init__(self, envelopes):
        self.envelopes = list(envelopes)
        self.calls = []

    def __call__(self, argv, cwd, env):
        self.calls.append(list(argv))
        return self.envelopes.pop(0) if self.envelopes else status("coherent")


class FakeAgent:
    name = "fake"

    def __init__(self):
        self.messages = []

    def send(self, body, cwd, env, session, resume, budget):
        self.messages.append((body, resume, budget))
        return run_prompts.AgentResult(True, "done", 1.5)


class HumanStepTest(unittest.TestCase):
    def test_approves_a_drafted_change_with_the_shown_digest(self):
        telos = FakeTelos([
            status("changing", [{"id": "CHG-0001", "status": "drafted", "obligations": []}]),
            {"ok": True, "result": {"digest": "sha256:abc", "id": "CHG-0001"}},
            {"ok": True, "result": {"digest": "sha256:abc", "id": "CHG-0001", "status": "approved"}},
        ])
        check = prompt_checks.PromptCheck(stem="01")
        message = run_prompts.human_step(Path("."), {}, check, telos=telos, log=lambda *_: None)
        self.assertEqual(["change", "approve", "CHG-0001", "--expected-digest", "sha256:abc"], telos.calls[2])
        self.assertEqual("Approved CHG-0001 (digest sha256:abc). Continue.", message)

    def test_reverts_drift_when_the_prompt_allows_it(self):
        telos = FakeTelos([
            status("drifted", drift={"paths": ["tictactoe/domain/board.py"], "token": "sha256:tok"}),
            {"ok": True, "result": {"restored": ["tictactoe/domain/board.py"], "deleted": []}},
        ])
        check = prompt_checks.PromptCheck(stem="05", human_action="revert")
        message = run_prompts.human_step(Path("."), {}, check, telos=telos, log=lambda *_: None)
        self.assertEqual(["revert", "--expected-state", "sha256:tok"], telos.calls[1])
        self.assertEqual("Reverted (drift token sha256:tok). Continue.", message)

    def test_stops_on_unexpected_drift(self):
        telos = FakeTelos([status("drifted", drift={"paths": ["x"], "token": "sha256:tok"})])
        check = prompt_checks.PromptCheck(stem="02")
        self.assertIsNone(run_prompts.human_step(Path("."), {}, check, telos=telos, log=lambda *_: None))
        self.assertEqual(1, len(telos.calls))

    def test_nudges_an_approved_change_and_finishes_when_coherent(self):
        check = prompt_checks.PromptCheck(stem="02")
        telos = FakeTelos([status("changing", [{"id": "CHG-0002", "status": "approved", "obligations": []}])])
        self.assertEqual(run_prompts.CONTINUE, run_prompts.human_step(Path("."), {}, check, telos=telos, log=lambda *_: None))
        telos = FakeTelos([status("coherent")])
        self.assertIsNone(run_prompts.human_step(Path("."), {}, check, telos=telos, log=lambda *_: None))


class RunPromptTest(unittest.TestCase):
    def test_loops_through_approval_then_checks(self):
        telos = FakeTelos([
            status("changing", [{"id": "CHG-0001", "status": "drafted", "obligations": []}]),
            {"ok": True, "result": {"digest": "sha256:abc", "id": "CHG-0001"}},
            {"ok": True, "result": {"digest": "sha256:abc", "id": "CHG-0001", "status": "approved"}},
            status("coherent"),
            status("coherent"),
        ])
        agent = FakeAgent()
        check = prompt_checks.PromptCheck(stem="01", tag="v0.1.0")
        outcome = run_prompts.run_prompt(
            "01", "the prompt", check, Path("."), {}, agent, "tictactoe", 4, 10.0,
            telos=telos, checks=lambda *a, **k: [], log=lambda *_: None,
        )
        self.assertTrue(outcome.passed)
        self.assertEqual(2, outcome.turns)
        self.assertEqual(3.0, outcome.cost_usd)
        self.assertEqual(("the prompt", False, 10.0), agent.messages[0])
        self.assertEqual(("Approved CHG-0001 (digest sha256:abc). Continue.", True, 8.5), agent.messages[1])

    def test_fails_when_never_coherent(self):
        telos = FakeTelos([status("changing", [{"id": "CHG-0001", "status": "open", "obligations": []}])] * 6)
        outcome = run_prompts.run_prompt(
            "01", "p", prompt_checks.PromptCheck(stem="01"), Path("."), {}, FakeAgent(), "tictactoe", 2, None,
            telos=telos, checks=lambda *a, **k: [], log=lambda *_: None,
        )
        self.assertFalse(outcome.passed)
        self.assertEqual(2, outcome.turns)
        self.assertIn("not coherent after 2 turn(s)", outcome.failures)

    def test_reports_failed_checks(self):
        telos = FakeTelos([status("coherent"), status("coherent")])
        outcome = run_prompts.run_prompt(
            "01", "p", prompt_checks.PromptCheck(stem="01"), Path("."), {}, FakeAgent(), "tictactoe", 2, None,
            telos=telos, checks=lambda *a, **k: ["tag v0.1.0 does not point at HEAD"], log=lambda *_: None,
        )
        self.assertFalse(outcome.passed)
        self.assertEqual(["tag v0.1.0 does not point at HEAD"], outcome.failures)


class SelectionAndFlagsTest(unittest.TestCase):
    def test_select_prompts_keeps_only_files_with_a_table_and_honours_ranges(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            for name in ("00-setup", "01-board", "02-match", "06-open"):
                (folder / f"{name}.md").write_text("x")
            checks = prompt_checks.Checks("tictactoe", {
                s: prompt_checks.PromptCheck(stem=s) for s in ("00-setup", "01-board", "02-match")
            })
            stems = [s for s, _ in run_prompts.select_prompts(folder, checks)]
            self.assertEqual(["00-setup", "01-board", "02-match"], stems)
            self.assertEqual(["01-board"], [s for s, _ in run_prompts.select_prompts(folder, checks, only="01")])
            self.assertEqual(["01-board", "02-match"], [s for s, _ in run_prompts.select_prompts(folder, checks, start="01")])

    def test_claude_flags_keep_the_guard_prompt_unanswered(self):
        argv = run_prompts.ClaudeAgent(model="opus").argv("hello", "sid", False, 4.256)
        self.assertEqual(["claude", "-p", "hello"], argv[:3])
        for flag in ("--permission-prompts", "--allowedTools", "--session-id", "--max-budget-usd", "--model"):
            self.assertIn(flag, argv)
        self.assertEqual("none", argv[argv.index("--permission-prompts") + 1])
        self.assertEqual("4.26", argv[argv.index("--max-budget-usd") + 1])
        resumed = run_prompts.ClaudeAgent().argv("again", "sid", True, None)
        self.assertIn("--resume", resumed)
        self.assertNotIn("--max-budget-usd", resumed)

    def test_platform_asset_names(self):
        self.assertEqual("telos_0.13.0_linux_amd64.tar.gz", run_prompts.platform_asset("0.13.0", "Linux", "x86_64"))
        self.assertEqual("telos_0.13.0_darwin_arm64.tar.gz", run_prompts.platform_asset("0.13.0", "Darwin", "arm64"))
        self.assertEqual("telos_0.13.0_windows_amd64.zip", run_prompts.platform_asset("0.13.0", "Windows", "AMD64"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m unittest tools.test_run_prompts`
Expected: `ModuleNotFoundError: No module named 'run_prompts'`

- [ ] **Step 3: Write `tools/run_prompts.py`**

```python
#!/usr/bin/env python3
"""Replay the prompts with a coding agent and check every outcome.

Each ``prompts/NN-*.md`` file is the exact text a human would type to Claude
Code or Codex in an empty repository. This runner sends them in order to a
headless agent, plays the human where Telos requires one (it approves the
digest shown by ``telos change diff`` and confirms the revert of a drift),
then checks the definition of done recorded in ``prompts/checks.toml``.

Requirements on PATH: ``claude`` or ``codex``, ``pytest``, and ``telos``
unless ``--telos`` or ``--telos-version`` is given. Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import uuid
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prompt_checks import Checks, PromptCheck, load_checks, run_checks  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
PROMPTS = REPO / "prompts"
WORKTREES = REPO / ".worktrees"
RELEASES = "https://github.com/hugues31/telos-sdd/releases/download"
DEFAULT_TELOS_VERSION = "0.13.0"
CLAUDE_TOOLS = "Bash,Edit,Write,Read,Glob,Grep,MultiEdit,Skill,TodoWrite"
CONTINUE = "Continue with the request as stated."


@dataclass
class AgentResult:
    ok: bool
    text: str
    cost_usd: float = 0.0


class ClaudeAgent:
    """Claude Code in print mode; the Telos guard's `ask` reaches nobody."""

    name = "claude"

    def __init__(self, model: str | None = None) -> None:
        self.model = model

    def argv(self, body: str, session: str, resume: bool, budget: float | None) -> list[str]:
        argv = [
            "claude", "-p", body, "--output-format", "json",
            "--permission-mode", "acceptEdits", "--allowedTools", CLAUDE_TOOLS,
            "--permission-prompts", "none", "--setting-sources", "project,local",
        ]
        argv += ["--resume", session] if resume else ["--session-id", session]
        if self.model:
            argv += ["--model", self.model]
        if budget is not None:
            argv += ["--max-budget-usd", f"{budget:.2f}"]
        return argv

    def send(self, body, cwd, env, session, resume, budget) -> AgentResult:
        proc = subprocess.run(self.argv(body, session, resume, budget), cwd=cwd, env=env,
                              text=True, capture_output=True)
        try:
            data = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return AgentResult(False, (proc.stdout + proc.stderr).strip()[-2000:])
        ok = proc.returncode == 0 and not data.get("is_error", False)
        return AgentResult(ok, str(data.get("result", "")), float(data.get("total_cost_usd") or 0.0))


class CodexAgent:
    """Codex in exec mode; the generated rules prompt on approve/revert and stop it."""

    name = "codex"

    def __init__(self, model: str | None = None) -> None:
        self.model = model

    def argv(self, body: str, cwd: Path, resume: bool, last_message: Path) -> list[str]:
        # danger-full-access, not workspace-write: that sandbox mounts .git
        # read-only, and `telos change reconcile` seals blobs into the git
        # object store (`git hash-object -w`), which then fails with
        # TELOS_GIT_ERROR. The target is a scratch repository.
        argv = [
            "codex", "exec", "--json", "-C", str(cwd), "--sandbox", "danger-full-access",
            "--skip-git-repo-check", "--dangerously-bypass-hook-trust", "-o", str(last_message),
        ]
        if self.model:
            argv += ["-m", self.model]
        if resume:
            argv += ["resume", "--last"]
        argv.append(body)
        return argv

    def send(self, body, cwd, env, session, resume, budget) -> AgentResult:
        with tempfile.TemporaryDirectory(prefix="codex-") as tmp:
            last = Path(tmp) / "last.md"
            proc = subprocess.run(self.argv(body, cwd, resume, last), cwd=cwd, env=env,
                                  text=True, capture_output=True)
            text = last.read_text(encoding="utf-8") if last.exists() else (proc.stdout + proc.stderr)[-2000:]
        return AgentResult(proc.returncode == 0, text.strip())


def telos_json(argv: list[str], cwd: Path, env: dict[str, str]) -> dict:
    proc = subprocess.run(["telos", *argv, "--json"], cwd=cwd, env=env, text=True, capture_output=True)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        message = (proc.stdout + proc.stderr).strip()[:500]
        return {"ok": False, "result": None, "error": {"code": "NO_ENVELOPE", "message": message}}


def human_step(target: Path, env: dict[str, str], check: PromptCheck, telos=telos_json, log=print) -> str | None:
    """Play the human: approve a drafted change, confirm an allowed revert.

    Returns the message that resumes the agent, or None when the project is
    coherent with nothing open (the prompt is finished) or when the drift is
    not one the prompt allows (the runner must stop).
    """
    status = telos(["status"], target, env)
    result = status.get("result") or {}
    state = result.get("state")
    if state == "drifted":
        if check.human_action != "revert":
            log(f"  unexpected drift: {result.get('drift')}")
            return None
        token = result["drift"]["token"]
        reverted = telos(["revert", "--expected-state", token], target, env)
        if not reverted.get("ok"):
            log(f"  revert refused: {reverted.get('error')}")
            return None
        log(f"  reverted drift {token}")
        return f"Reverted (drift token {token}). Continue."
    for change in result.get("changes", []):
        if change.get("status") == "drafted":
            diff = telos(["change", "diff", change["id"]], target, env)
            digest = (diff.get("result") or {}).get("digest")
            if not digest:
                log(f"  no digest for {change['id']}: {diff.get('error')}")
                return None
            approved = telos(["change", "approve", change["id"], "--expected-digest", digest], target, env)
            if not approved.get("ok"):
                log(f"  approval refused: {approved.get('error')}")
                return None
            log(f"  approved {change['id']} with digest {digest}")
            return f"Approved {change['id']} (digest {digest}). Continue."
        return CONTINUE
    return None if state == "coherent" else CONTINUE


@dataclass
class Outcome:
    stem: str
    passed: bool
    turns: int
    cost_usd: float
    failures: list[str] = field(default_factory=list)


def run_prompt(stem, body, check, target, env, agent, module, max_turns, budget_left,
               telos=telos_json, checks=run_checks, log=print) -> Outcome:
    session = str(uuid.uuid4())
    message, resume, cost, turns, finished = body, False, 0.0, 0, False
    while turns < max_turns:
        turns += 1
        budget = None if budget_left is None else max(budget_left - cost, 0.0)
        log(f"[{stem}] turn {turns} ({agent.name})")
        result = agent.send(message, target, env, session, resume, budget)
        cost += result.cost_usd
        log(f"  agent {'ok' if result.ok else 'error'}, cost so far {cost:.2f} USD")
        if result.text:
            log("  " + result.text.strip().splitlines()[-1][:200])
        next_message = human_step(target, env, check, telos=telos, log=log)
        if next_message is None:
            state = (telos(["status"], target, env).get("result") or {}).get("state")
            finished = state == "coherent"
            break
        message, resume = next_message, True
    failures = checks(check, target, env, module) if finished else [f"not coherent after {turns} turn(s)"]
    for failure in failures:
        log(f"  FAIL {failure}")
    return Outcome(stem, not failures, turns, cost, failures)


def select_prompts(prompts_dir: Path, checks: Checks, only: str | None = None, start: str | None = None):
    selected = []
    for path in sorted(prompts_dir.glob("[0-9][0-9]-*.md")):
        stem, number = path.stem, path.stem[:2]
        if stem not in checks.prompts:
            continue
        if only and number != only:
            continue
        if start and number < start:
            continue
        selected.append((stem, path))
    return selected


def platform_asset(version: str, system: str = platform.system(), machine: str = platform.machine()) -> str:
    os_name = {"Linux": "linux", "Darwin": "darwin", "Windows": "windows"}[system]
    arch = {"x86_64": "amd64", "AMD64": "amd64", "arm64": "arm64", "aarch64": "arm64"}[machine]
    return f"telos_{version}_{os_name}_{arch}.{'zip' if os_name == 'windows' else 'tar.gz'}"


def ensure_telos(version: str, cache: Path = WORKTREES / "telos", log=print) -> Path:
    """Download and verify a Telos release once; return its binary."""
    folder = cache / version
    binary = folder / ("telos.exe" if platform.system() == "Windows" else "telos")
    if binary.exists():
        return binary
    asset = platform_asset(version)
    base = f"{RELEASES}/v{version}"
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / asset
    log(f"downloading {asset}")
    urllib.request.urlretrieve(f"{base}/{asset}", archive)
    with urllib.request.urlopen(f"{base}/checksums.txt") as response:
        checksums = response.read().decode("utf-8")
    expected = next(line.split()[0] for line in checksums.splitlines() if line.strip().endswith(asset))
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != expected:
        archive.unlink()
        raise SystemExit(f"checksum mismatch for {asset}: {actual} != {expected}")
    if asset.endswith(".zip"):
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(folder)
    else:
        with tarfile.open(archive) as bundle:
            bundle.extractall(folder, **({"filter": "data"} if sys.version_info >= (3, 12) else {}))
    archive.unlink()
    binary.chmod(0o755)
    return binary


def build_env(telos_bin: Path | None) -> dict[str, str]:
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)
    paths = [str(telos_bin.parent)] if telos_bin else []
    venv = REPO / ".venv" / "bin"
    if venv.is_dir():
        paths.append(str(venv))
    env["PATH"] = os.pathsep.join(paths + [env.get("PATH", "")])
    return env


def prepare_target(target: Path, fresh: bool) -> None:
    if fresh:
        target.mkdir(parents=True)
        for argv in (["git", "init", "-q"],
                     ["git", "config", "user.name", "Telos prompts runner"],
                     ["git", "config", "user.email", "runner@example.invalid"]):
            subprocess.run(argv, cwd=target, check=True)
    elif not (target / ".git").is_dir():
        raise SystemExit(f"{target} is not a replayed repository")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--agent", choices=["claude", "codex"], default="claude")
    binary = parser.add_mutually_exclusive_group()
    binary.add_argument("--telos", type=Path, help="Telos binary to use")
    binary.add_argument("--telos-version", metavar="X.Y.Z", help="download and use this Telos release")
    parser.add_argument("--target", type=Path, help="replay directory (default: .worktrees/run-<agent>-<time>)")
    parser.add_argument("--only", metavar="NN", help="run one prompt against an existing target")
    parser.add_argument("--from", dest="start", metavar="NN", help="resume an existing target from this prompt")
    parser.add_argument("--keep", action="store_true", help="keep the target after a passing run")
    parser.add_argument("--model", help="agent model name")
    parser.add_argument("--max-budget-usd", type=float, help="cap on the whole run (Claude only)")
    parser.add_argument("--max-turns", type=int, default=4, help="agent turns per prompt (default 4)")
    args = parser.parse_args(argv)

    telos_bin = None
    if args.telos:
        telos_bin = args.telos.resolve()
    elif args.telos_version:
        telos_bin = ensure_telos(args.telos_version)
    env = build_env(telos_bin)
    version = subprocess.run(["telos", "--version"], env=env, text=True, capture_output=True).stdout.strip()
    print(f"using {version or 'no telos on PATH'}")

    checks = load_checks(PROMPTS / "checks.toml")
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = (args.target or WORKTREES / f"run-{args.agent}-{stamp}").resolve()
    if target.exists() and not (args.only or args.start):
        raise SystemExit(f"{target} exists; pass --from or --only to reuse it")
    prepare_target(target, fresh=not target.exists())
    print(f"target {target}")
    agent = ClaudeAgent(args.model) if args.agent == "claude" else CodexAgent(args.model)

    outcomes: list[Outcome] = []
    total = 0.0
    exhausted = False
    for stem, path in select_prompts(PROMPTS, checks, args.only, args.start):
        budget_left = None if args.max_budget_usd is None else args.max_budget_usd - total
        if budget_left is not None and budget_left <= 0:
            print("budget exhausted")
            exhausted = True
            break
        outcome = run_prompt(stem, path.read_text(encoding="utf-8"), checks.prompts[stem], target, env,
                             agent, checks.module, args.max_turns, budget_left)
        total += outcome.cost_usd
        outcomes.append(outcome)
        if not outcome.passed:
            break

    print()
    for outcome in outcomes:
        verdict = "PASS" if outcome.passed else "FAIL"
        detail = f"  {outcome.failures[0]}" if outcome.failures else ""
        print(f"{verdict}  {outcome.stem:<24} turns {outcome.turns}  cost {outcome.cost_usd:.2f} USD{detail}")
    print(f"total cost {total:.2f} USD")
    passed = bool(outcomes) and all(o.passed for o in outcomes) and not exhausted
    if passed and not args.keep:
        shutil.rmtree(target)
    else:
        print(f"target kept at {target}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m unittest tools.test_run_prompts tools.test_prompt_checks`
Expected: `OK` with 18 tests.

- [ ] **Step 5: Smoke the CLI without an agent**

Run: `.venv/bin/python tools/run_prompts.py --help`
Expected: the usage text with `--agent`, `--telos-version`, `--only`, `--from`, `--max-budget-usd`.

- [ ] **Step 6: Commit**

```bash
git add tools/run_prompts.py tools/test_run_prompts.py
git commit -q -m "feat: agent runner that replays the prompts and plays the human" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Spike the real Claude flow on prompts 00 and 01

**Files:**
- Modify: `tools/run_prompts.py` (flags only, if the spike demands it), `prompts/01-board-and-console.md` (wording only, if the agent misreads it)

**Interfaces:**
- Consumes: the runner from Task 3, the 0.13.0 binary at `.worktrees/lab/bin/telos`.
- Produces: a kept target `.worktrees/run-claude-spike/` at `v0.1.0`, reused by Task 7 with `--from 02`.

- [ ] **Step 1: Run prompt 00 alone**

Run: `.venv/bin/python tools/run_prompts.py --telos .worktrees/lab/bin/telos --target .worktrees/run-claude-spike --only 00 --keep --max-budget-usd 3`
(A target that does not exist yet is created and initialised even with `--only`.)
Expected: `PASS  00-setup  turns 1`, and in the target: `.claude/`, `.agents/`, `.codex/`, `AGENTS.md`, `.github/workflows/telos.yml`, `.gitignore`, `telos/`, tag `v0.0.0`, clean tree.

- [ ] **Step 2: Inspect the agent's behaviour**

Run: `git -C .worktrees/run-claude-spike log --oneline` and `cat .worktrees/run-claude-spike/.gitignore`
Expected: one commit `v0.0: empty spec`; the four ignore lines. If the agent prefixed commands with `rtk` or loaded the user-level `CLAUDE.md`, the run still passes; note it.

- [ ] **Step 3: Run prompt 01 against the same target**

Run: `.venv/bin/python tools/run_prompts.py --telos .worktrees/lab/bin/telos --target .worktrees/run-claude-spike --only 01 --keep --max-budget-usd 8`
Expected: turn 1 ends with the change drafted; the runner logs `approved CHG-0001 with digest sha256:...`; turn 2 implements; `PASS  01-board-and-console`. Watch for these failure signatures and their fixes:
  - the agent approved the change itself (no `approved` log line, change already `approved` after turn 1): the guard's `ask` was auto-answered; switch `--permission-mode acceptEdits` to `--permission-mode default` in `ClaudeAgent.argv` and re-run with `--only 01` after `git -C <target> reset --hard v0.0.0` and `telos revert` if needed;
  - `TELOS_TEST_NOT_EXECUTED` loops: the agent wrote tests importing a missing module; add to the prompt's tests bullet: "write a stub of the module first so the failing test executes";
  - `TELOS_ORPHAN_CODE`: a helper file under `tests/` or `tictactoe/__init__.py` inside the globs; the prompt already says globs are the two files; check the agent's config payload;
  - a `pytest.ini` missing `python_functions = scn_*`: the prompt says to configure it; strengthen the wording if ignored.

- [ ] **Step 4: Review the produced v0.1.0**

Run: `cat .worktrees/run-claude-spike/tictactoe/domain/board.py`, `cat .worktrees/run-claude-spike/tictactoe/ui/cli.py`, `cat .worktrees/run-claude-spike/tictactoe/__main__.py`, `ls .worktrees/run-claude-spike/tests`, and `.worktrees/lab/bin/telos show INT-0005 --json` from inside the target (write a two-line script under `.worktrees/lab/` if the guard refuses `cd`).
Expected: readable code, five intents, nine scenarios, the console contract honoured. Fix prompt wording only for things the agent could not have known.

- [ ] **Step 5: Commit any prompt or flag adjustment**

```bash
git add prompts tools/run_prompts.py
git commit -q -m "fix: runner flags and prompt wording after the first live replay" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: README, workflows and ignore rules

**Files:**
- Modify: `README.md` (rewrite), `.github/workflows/demo-gif.yml` (pins), `.gitignore`
- Create: `.github/workflows/ci.yml`, `.github/workflows/prompts.yml`
- Delete: `.github/workflows/demo.yml`

- [ ] **Step 1: Rewrite `README.md`**

````markdown
# Tic-tac-toe, spec-first with Telos

[![Telos seal](https://github.com/hugues31/telos-tictactoe/actions/workflows/telos.yml/badge.svg)](https://github.com/hugues31/telos-tictactoe/actions/workflows/telos.yml)
[![Browse the spec](https://img.shields.io/badge/GitHub_Pages-browse_the_spec-2ea44f?logo=githubpages&logoColor=white)](https://hugues31.github.io/telos-tictactoe/)

A tic-tac-toe game in Python, playable in the terminal and in a window.
Five prompts given to a coding agent built it, and every behaviour it has
is an intent in [`telos/`](telos/), proven by a test and sealed by hash.
[Telos](https://github.com/hugues31/telos-sdd) is a local CLI for
spec-driven development: the specification is the source of truth, the
code is one solution of it.

## Try it

```console
curl -fsSL https://raw.githubusercontent.com/hugues31/telos-sdd/main/install.sh | TELOS_VERSION=v0.13.0 sh
export PATH="$HOME/.local/bin:$PATH"
python3 -m venv .venv && .venv/bin/pip install pytest
export PATH="$PWD/.venv/bin:$PATH"

python -m tictactoe          # two players, one keyboard
python -m tictactoe --gui    # the same game in a window
telos status
```

## How it was built

Each prompt is the text a human typed to a coding agent that had the Telos
skills installed. Each ends with a git tag you can check out.

| Prompt | Tag | The game | What Telos does |
|---|---|---|---|
| [00-setup](prompts/00-setup.md) | `v0.0.0` | nothing yet | `init`, skills for Claude Code and Codex, the CI gate |
| [01-board-and-console](prompts/01-board-and-console.md) | `v0.1.0` | one round, in the terminal | two contexts, five intents, red then green witnesses judged by a JUnit report, the context map |
| [02-tournament](prompts/02-tournament.md) | `v0.2.0` | a match to two wins | a third context, an intent that grows a scenario |
| [03-misere](prompts/03-misere.md) | `v0.3.0` | three in a row loses | `impact`, editing a sealed intent, new witnesses |
| [04-window](prompts/04-window.md) | `v0.4.0` | the same game in a window | a fourth context, an architecture constraint with an executable check |
| [05-hotfix](prompts/05-hotfix.md) | none | nothing | a hand edit of bound code, drift, `revert` |
| [06-your-turn](prompts/06-your-turn.md) | none | up to you | a hole in the spec, yours to seal |

The domain lives in `tictactoe/domain/`, the interfaces in
`tictactoe/ui/`. The domain never imports an interface: constraint
CON-0001 checks it at every reconcile. `tictactoe/__main__.py` is glue
outside the spec.

## Replay it with an agent

```console
python3 tools/run_prompts.py --agent claude --telos-version 0.13.0
```

The runner creates an empty repository under `.worktrees/`, sends each
prompt to `claude -p` (or `codex exec` with `--agent codex`), and plays
the human where Telos requires one: it reads `telos change diff` and
approves the digest it shows, and it confirms the revert of prompt 05.
After each prompt it checks the definition of done in
[`prompts/checks.toml`](prompts/checks.toml): state `coherent`, the
expected numbers of intents and scenarios, `telos check --sealed`, a clean
tree, the tag, `pytest`, and a scripted game on the console. It costs
tokens; `--max-budget-usd` caps a Claude run. Point it at a new Telos
release with `--telos-version`.

## Look at the spec

```console
telos status              # state, coverage, proof evidence
telos show INT-0003       # one intent, its scenarios and bindings
telos map                 # the context map
telos view --open         # the spec as a site
```

The site is published at
[hugues31.github.io/telos-tictactoe](https://hugues31.github.io/telos-tictactoe/).

[![Walkthrough of the specification site](docs/demo.gif)](https://hugues31.github.io/telos-tictactoe/)

Test evidence is report-backed: a green witness is a test named after its
scenario that ran and passed, read from the JUnit report pytest writes. A
run that executes nothing is refused with `TELOS_TEST_NOT_EXECUTED`.

## Repository map

```
telos/            the sealed specification: contexts, notions, intents, constraints, bindings, lock
prompts/          the seven prompts and their definition of done
tictactoe/        the game: domain/ and ui/
tests/            one test per scenario
tools/            run_prompts.py, check_layers.py, record_demo.py
docs/             the demo GIF and the design documents
.github/          telos.yml (sealed check), ci.yml (tests, Pages), demo-gif.yml, prompts.yml
```

## License

[MIT](LICENSE).
````

- [ ] **Step 2: Write `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install "pytest>=7"
      - name: Install Telos v0.13.0
        run: |
          version=0.13.0
          asset="telos_${version}_linux_amd64.tar.gz"
          base="https://github.com/hugues31/telos-sdd/releases/download/v${version}"
          cd "$RUNNER_TEMP"
          curl -fsSLO "${base}/${asset}"
          curl -fsSLO "${base}/checksums.txt"
          sha256sum --check --ignore-missing checksums.txt
          tar -xzf "${asset}"
          install -D -m 0755 telos "$HOME/.local/bin/telos"
          echo "$HOME/.local/bin" >> "$GITHUB_PATH"
      - name: Scenario tests
        run: pytest -q
      - name: Rebuild status
        run: telos rebuild status
      - name: Runner unit tests
        run: python3 -m unittest tools.test_prompt_checks tools.test_run_prompts

  pages:
    if: github.ref == 'refs/heads/main'
    needs: tests
    permissions:
      contents: read
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deploy.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - name: Install Telos v0.13.0
        run: |
          version=0.13.0
          asset="telos_${version}_linux_amd64.tar.gz"
          base="https://github.com/hugues31/telos-sdd/releases/download/v${version}"
          cd "$RUNNER_TEMP"
          curl -fsSLO "${base}/${asset}"
          curl -fsSLO "${base}/checksums.txt"
          sha256sum --check --ignore-missing checksums.txt
          tar -xzf "${asset}"
          install -D -m 0755 telos "$HOME/.local/bin/telos"
          echo "$HOME/.local/bin" >> "$GITHUB_PATH"
      - name: Export the spec as a static site
        run: telos view --export site
      - uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - id: deploy
        uses: actions/deploy-pages@v4
```

- [ ] **Step 3: Write `.github/workflows/prompts.yml`**

```yaml
name: Prompts

# Replays the prompts with a coding agent against a chosen Telos release.
# Manual only: it spends API credits. Needs ANTHROPIC_API_KEY (claude) or
# OPENAI_API_KEY (codex) in the repository secrets.

on:
  workflow_dispatch:
    inputs:
      agent:
        description: "Coding agent"
        type: choice
        options: [claude, codex]
        default: claude
      telos_version:
        description: "Telos release to replay against"
        default: "0.13.0"

permissions:
  contents: read

jobs:
  replay:
    runs-on: ubuntu-latest
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install "pytest>=7"
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - name: Install the agent CLI
        run: |
          if [ "${{ inputs.agent }}" = "claude" ]; then
            npm install -g @anthropic-ai/claude-code
          else
            npm install -g @openai/codex
          fi
      - name: Replay the prompts
        run: |
          git config --global user.name "Telos prompts runner"
          git config --global user.email "runner@example.invalid"
          python3 tools/run_prompts.py --agent "${{ inputs.agent }}" --telos-version "${{ inputs.telos_version }}" --target .worktrees/run --keep
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: replayed-project
          path: .worktrees/run
          include-hidden-files: true
```

- [ ] **Step 4: Bump `.github/workflows/demo-gif.yml` and drop `demo.yml`**

Replace both occurrences of `0.11.0` in `demo-gif.yml` (`Install Telos v0.11.0` and `version=0.11.0`) with `0.13.0`. Then:

```bash
git rm -q .github/workflows/demo.yml
```

- [ ] **Step 5: Extend `.gitignore`**

Append nothing on this branch; the reference's `.gitignore` comes from prompt 00 and receives `.worktrees/`, `site/` and `docs/demo.mp4` in Task 8. On this branch `.gitignore` already has them.

- [ ] **Step 6: Check the README length and pins**

Run: `wc -l README.md` and `grep -n "0\.11\|Momo\|tamagotchi" README.md .github/workflows/ci.yml .github/workflows/prompts.yml .github/workflows/demo-gif.yml`
Expected: under 100 lines; no match.

- [ ] **Step 7: Commit**

```bash
git add README.md .github/workflows
git commit -q -m "docs: README and workflows for the tic-tac-toe story on Telos 0.13" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Retarget the GIF recorder

**Files:**
- Modify: `tools/record_demo.py:1-12` (docstring), `tools/record_demo.py:31-33` (cursor comment), `tools/record_demo.py:162-240` (`tour`)
- Modify: `tools/test_record_demo.py:117-152`

- [ ] **Step 1: Update the tour**

In `tools/record_demo.py`, add `import re` to the imports, change the cursor comment `Colours match the v0.11 Telos identity.` to `Colours match the Telos identity.`, and replace the body of `tour` from the global search down to the `TourResult` with:

```python
def tour(page: Page, base: str) -> TourResult:
    """Walk the exported spec site and return its semantic checkpoints."""
    wait = page.wait_for_timeout
    cursor = Cursor(page)

    # Dashboard: project coherence and the headline coverage metrics.
    page.goto(f"{base}/index.html")
    page.get_by_role("heading", name="Dashboard").wait_for()
    cursor.show()
    wait(1200)

    # Global search: jump from a rule of the game to its owning intent.
    global_search_query = "three in a row"
    search_button = page.get_by_role("button", name="Search all Telos entities")
    cursor.click(search_button)
    dialog = page.get_by_role("dialog", name="Search Telos")
    global_input = dialog.get_by_role(
        "combobox", name="Search all Telos entities"
    )
    cursor.type(global_input, global_search_query)
    global_result = dialog.get_by_role("option").filter(has_text="INT-0003")
    global_result.wait_for()
    wait(700)
    cursor.click(global_result)
    page.wait_for_url("**/index.html#/intent/INT-0003")
    page.get_by_role("heading", name=re.compile(r"^INT-0003 — ")).wait_for()
    statement = page.locator(".statement-card").filter(has_text="event-driven")
    statement.wait_for()
    wait(1100)

    # Intent detail: reveal the canonical statement and its first proved scenario.
    first_scenario = page.locator('[id^="scenario-SCN-"]').first
    first_scenario.wait_for()
    scenario_id = (first_scenario.get_attribute("id") or "").removeprefix("scenario-")
    scroll_to(page, f"#scenario-{scenario_id}", margin=180)
    scenario = page.locator(f"#scenario-{scenario_id}").filter(
        has_text=f"scenario {scenario_id}"
    )
    scenario.wait_for()
    wait(1200)

    # Graph finder: locate the same intent and focus its dependency node.
    cursor.click(page.get_by_role("link", name="Graph", exact=True))
    page.wait_for_url("**/index.html#/graph")
    page.get_by_role("heading", name="Graph", exact=True).wait_for()
    page.locator(".cyto-graph__canvas").wait_for()
    wait(900)
    graph_query = "INT-0003"
    graph_input = page.get_by_label("Find node")
    cursor.type(graph_input, graph_query)
    graph_result = page.get_by_role("option").filter(has_text="INT-0003")
    graph_result.wait_for()
    wait(700)
    cursor.click(graph_result)
    selected = page.locator(".selection-panel__id").filter(has_text="INT-0003")
    selected.wait_for()
    wait(1300)

    # Glossary: the Board notion and the three contexts that consume it.
    cursor.click(page.get_by_role("link", name="Glossary", exact=True))
    page.wait_for_url("**/index.html#/glossary")
    page.get_by_role("heading", name="Glossary", exact=True).wait_for()
    glossary_query = "Board"
    glossary_input = page.get_by_label("Search glossary")
    cursor.type(glossary_input, glossary_query)
    wait(500)
    board_card_selector = '[id="notion-board/Board"]'
    scroll_to(page, board_card_selector, margin=150)
    board_card = page.locator(board_card_selector)
    board_card.get_by_label("Used by entities").wait_for()
    consumer_count = board_card.locator("tbody tr").count()
    wait(1500)

    return TourResult(
        global_search_query=global_search_query,
        intent_id="INT-0003",
        scenario_id=scenario_id,
        graph_query=graph_query,
        selected_node="INT-0003",
        glossary_query=glossary_query,
        glossary_consumers=consumer_count,
    )
```

Also change the module docstring's first line to `Record the \`telos view\` demo GIF for the README.` and drop `of telos-sdd`.

- [ ] **Step 2: Update the recorder test**

In `tools/test_record_demo.py`, rename `test_tour_showcases_the_telos_v011_preview` to `test_tour_showcases_the_spec_site`, change the failure message to `f"the Telos tour did not complete: {error}"`, and replace the assertions with:

```python
                        self.assertEqual("three in a row", result.global_search_query)
                        self.assertEqual("INT-0003", result.intent_id)
                        self.assertTrue(result.scenario_id.startswith("SCN-"), result.scenario_id)
                        self.assertEqual("INT-0003", result.graph_query)
                        self.assertEqual("INT-0003", result.selected_node)
                        self.assertEqual("Board", result.glossary_query)
                        self.assertGreaterEqual(result.glossary_consumers, 3)
                        self.assertEqual(
                            ["/", "/intent/INT-0003", "/graph", "/glossary"],
                            [route for route in dict.fromkeys(visited) if route],
                        )
```

- [ ] **Step 3: Run the tests that do not need the new spec**

Run: `.venv/bin/python -m unittest tools.test_record_demo.DemoGifTest.test_gif_uses_readable_width tools.test_record_demo.DemoGifTest.test_gif_keeps_a_full_palette tools.test_record_demo.DemoGifTest.test_gif_size_limit_is_strict`
(Adjust the class name to the one in the file; list it with `grep -n "class " tools/test_record_demo.py`.)
Expected: `OK`. The tour test runs in Task 8 on the new spec.

- [ ] **Step 4: Commit**

```bash
git add tools/record_demo.py tools/test_record_demo.py
git commit -q -m "feat: retarget the demo tour to the tic-tac-toe spec" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: Build the reference with the runner

**Files:**
- Produces: `.worktrees/run-claude-spike/` at `v0.4.0`, coherent after prompt 05.
- Modify: `prompts/*.md`, `prompts/checks.toml` (only when a check reveals a wording the agent could not follow)

- [ ] **Step 1: Resume from prompt 02 on the spike target**

Run: `.venv/bin/python tools/run_prompts.py --telos .worktrees/lab/bin/telos --target .worktrees/run-claude-spike --from 02 --keep --max-budget-usd 12`
Expected: `PASS` for `02-tournament`, `03-misere`, `04-window`, `05-hotfix`; total cost printed; total across Tasks 4 and 7 under 15 USD.

- [ ] **Step 2: On a failure, fix and re-run one prompt**

If a prompt fails: read the runner log, fix the prompt text (never the check), restore the target to its last tag (`git -C .worktrees/run-claude-spike reset -q --hard v0.N.0` then `git -C .worktrees/run-claude-spike clean -qfd`, then `telos status` must be `coherent`; if a change is left open, run `telos change abandon CHG-NNNN` from a script under `.worktrees/lab/`), and re-run with `--only NN`. Commit each prompt fix:

```bash
git add prompts
git commit -q -m "fix: prompt wording after the live replay" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

- [ ] **Step 3: Review the reference**

Run from a script under `.worktrees/lab/` (cwd the target): `telos status --json`, `telos map --json`, `telos show INT-0003 --json`, `telos rebuild status --json`, `git log --oneline --decorate`, plus `cat` of `tictactoe/domain/board.py`, `tictactoe/domain/tournament.py`, `tictactoe/ui/cli.py`, `tictactoe/ui/gui.py`, `tools/check_layers.py`.
Expected: 9 intents, 16 scenarios, 1 constraint, `proof_evidence = report`, four dependencies in the map, five tags `v0.0.0` to `v0.4.0` on five commits, readable code with the domain free of interface imports.

- [ ] **Step 4: Play the game by hand once**

Run: `.venv/bin/python -m tictactoe` from the target with the moves `5 1 4 2 6`, then `.venv/bin/python -m tictactoe --gui` (close the window).
Expected: the console prints `O wins` and `X 0 - 1 O`; a window with nine buttons opens.

---

### Task 8: Assemble the new history and verify it

**Files:**
- Create: branch `tictactoe` from the target's `main`, with one final commit adding the project-level files and `docs/demo.gif`.

- [ ] **Step 1: Fetch the target's history**

```bash
git fetch -q .worktrees/run-claude-spike main:tictactoe
git tag legacy-v0.11 42600cd
git checkout -q tictactoe
```

Expected: `git log --oneline --decorate` shows five commits with tags `v0.0.0` to `v0.4.0` (the fetch brings commits, not tags: re-create them with `git tag v0.N.0 <sha>` from `git -C .worktrees/run-claude-spike show-ref --tags`).

- [ ] **Step 2: Bring the project-level files from `main`**

```bash
git checkout main -- README.md LICENSE prompts tools/run_prompts.py tools/prompt_checks.py tools/test_prompt_checks.py tools/test_run_prompts.py tools/record_demo.py tools/test_record_demo.py .github/workflows/ci.yml .github/workflows/demo-gif.yml .github/workflows/prompts.yml docs/superpowers/specs/2026-09-04-telos-tictactoe-design.md docs/superpowers/plans/2026-09-04-telos-tictactoe.md
```

Then append to `.gitignore` the lines `.worktrees/`, `site/`, `docs/demo.mp4` (Edit tool, not a redirection).

- [ ] **Step 3: Regenerate the GIF and run the recorder test**

Run: `.venv/bin/python tools/record_demo.py --telos .worktrees/lab/bin/telos`
Expected: `docs/demo.gif  N.N MB` under 10 MB and `docs/demo.mp4`.
Run: `.venv/bin/python -m unittest tools.test_record_demo` with `.worktrees/lab/bin` first on `PATH` (write a three-line script under `.worktrees/lab/` that sets `PATH` and calls unittest, since the guard refuses `env`/`export` chains).
Expected: `OK`.

- [ ] **Step 4: Verify the sealed state and the code**

Run, with `.worktrees/lab/bin/telos`: `telos status --json`, `telos check --sealed --json`, `telos rebuild status --json`, `telos map --json`, `.venv/bin/python -m pytest -q`, `.venv/bin/python tools/check_layers.py`, `.venv/bin/python -m unittest tools.test_prompt_checks tools.test_run_prompts`.
Expected: `coherent`, `proof_evidence = "report"`, `intents_active = 9`, `scenarios_proved = 16`, `constraints = 1`; no diagnostic; all scenarios green; four dependencies; pytest green; check exits 0; unit tests OK.

- [ ] **Step 5: Verify the constraint bites**

Add the line `import tictactoe.ui.cli  # temporary` at the top of `tictactoe/domain/board.py`, run `.venv/bin/python tools/check_layers.py`, expect exit 1 with a message naming the import, then restore the file with `git checkout -- tictactoe/domain/board.py` and confirm `telos status --json` is `coherent` again.

- [ ] **Step 6: Export the site and grep for leftovers**

Run: `.worktrees/lab/bin/telos view --export .worktrees/site-check` then `grep -rn "0\.11\|0\.12\|Momo\|tamagotchi" --exclude-dir=.git --exclude-dir=.worktrees --exclude-dir=docs .` and `grep -rln "Momo\|tamagotchi" docs`.
Expected: the export succeeds; no match outside `docs/superpowers/`, and inside it only the design and plan's history notes.

- [ ] **Step 7: Commit the final assembly**

```bash
git add -A
git commit -q -m "docs: prompts, runner, README, CI and demo for the tic-tac-toe story" -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

Then `git status` must be clean and `telos check --sealed --json` must still answer ok (the commit touched nothing under `telos/`).

- [ ] **Step 8: Codex smoke, best effort**

Run: `.venv/bin/python tools/run_prompts.py --agent codex --telos .worktrees/lab/bin/telos --target .worktrees/run-codex-smoke --only 00 --keep` after creating the target as in Task 4 step 1.
Expected: `PASS 00-setup`, or a clear login/auth error to report. Do not block on it.

---

### Task 9: Publish, with the user's explicit go

**Files:**
- Remote: tags, `main`, repository name and description.

- [ ] **Step 1: Stop and ask**

Present the user the verification results of Task 8 and the exact commands below. Do not run any of them without a "go".

- [ ] **Step 2: Rewrite the remote**

```bash
git push -q origin legacy-v0.11
git push -q origin --delete v0.0.0 v0.1.0 v0.2.0 v0.3.0 v0.4.0 v0.5.0
git tag -d v0.5.0
git branch -M main old-main
git branch -M tictactoe main
git push -q --force origin main
git push -q origin v0.0.0 v0.1.0 v0.2.0 v0.3.0 v0.4.0
```

(Delete the remote tags before the local re-tagging in Task 8 step 1 collides; if `git tag v0.N.0` failed there because the old tag existed, run `git tag -d v0.N.0` first and re-create it on the new commit.)

- [ ] **Step 3: Rename and describe**

```bash
gh repo rename telos-tictactoe -R hugues31/telos-tamagotchi --yes
gh repo edit hugues31/telos-tictactoe --description "Tic-tac-toe built from six prompts with Telos: a replayable demo and end-to-end test of spec-driven development"
git remote set-url origin git@github.com:hugues31/telos-tictactoe.git
```

(Use the URL scheme `git remote get-url origin` currently shows.)

- [ ] **Step 4: Watch CI**

Run: `gh run list -R hugues31/telos-tictactoe --limit 5` after a minute, then `gh run watch` on the `Telos` and `CI` runs.
Expected: both green; Pages deployed at `https://hugues31.github.io/telos-tictactoe/`. The `Demo GIF` workflow re-records on the next push touching `telos/` only.

- [ ] **Step 5: Remind the user of what is left to them**

Tell the user: install Telos 0.13.0 locally (`TELOS_VERSION=v0.13.0` installer), add `ANTHROPIC_API_KEY` if they want `prompts.yml`, review issue hugues31/telos-sdd#29, and that `old-main` can be deleted once they are satisfied.
