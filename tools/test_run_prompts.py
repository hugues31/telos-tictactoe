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

    def test_stops_on_spec_drift_or_drift_without_an_open_change(self):
        check = prompt_checks.PromptCheck(stem="02")
        telos = FakeTelos([status("drifted", drift={"paths": ["tictactoe/ui/cli.py"], "token": "sha256:tok"})])
        self.assertIsNone(run_prompts.human_step(Path("."), {}, check, telos=telos, log=lambda *_: None))
        self.assertEqual(1, len(telos.calls))
        telos = FakeTelos([status(
            "drifted", [{"id": "CHG-0002", "status": "implementing", "obligations": []}],
            drift={"paths": ["telos/contexts/board/notions/Board.tel"], "token": "sha256:tok"},
        )])
        self.assertIsNone(run_prompts.human_step(Path("."), {}, check, telos=telos, log=lambda *_: None))
        self.assertEqual(1, len(telos.calls))

    def test_adopts_a_code_edit_into_the_open_change_and_reapproves(self):
        check = prompt_checks.PromptCheck(stem="02")
        telos = FakeTelos([
            status("drifted", [{"id": "CHG-0002", "status": "implementing", "obligations": []}],
                   drift={"paths": ["tictactoe/ui/cli.py"], "token": "sha256:tok"}),
            {"ok": True, "result": {"change": "CHG-0002", "ops": 1, "paths": ["tictactoe/ui/cli.py"]}},
            {"ok": True, "result": {"digest": "sha256:new", "approved_digest": "sha256:old", "stale": True, "id": "CHG-0002"}},
            {"ok": True, "result": {"digest": "sha256:new", "id": "CHG-0002", "status": "approved"}},
        ])
        message = run_prompts.human_step(Path("."), {}, check, telos=telos, log=lambda *_: None)
        self.assertEqual(["adopt", "--into", "CHG-0002", "--expected-state", "sha256:tok"], telos.calls[1])
        self.assertEqual(["change", "approve", "CHG-0002", "--expected-digest", "sha256:new"], telos.calls[3])
        self.assertEqual(
            "Adopted your edit of tictactoe/ui/cli.py into CHG-0002. Approved CHG-0002 (digest sha256:new). Continue.",
            message,
        )

    def test_reapproves_a_stale_change(self):
        check = prompt_checks.PromptCheck(stem="02")
        telos = FakeTelos([
            status("changing", [{"id": "CHG-0002", "status": "approved", "obligations": []}]),
            {"ok": True, "result": {"digest": "sha256:new", "approved_digest": "sha256:old", "stale": True, "id": "CHG-0002"}},
            {"ok": True, "result": {"digest": "sha256:new", "id": "CHG-0002", "status": "approved"}},
        ])
        message = run_prompts.human_step(Path("."), {}, check, telos=telos, log=lambda *_: None)
        self.assertEqual("Approved CHG-0002 (digest sha256:new). Continue.", message)

    def test_nudges_an_approved_change_and_finishes_when_coherent(self):
        check = prompt_checks.PromptCheck(stem="02")
        telos = FakeTelos([
            status("changing", [{"id": "CHG-0002", "status": "approved", "obligations": []}]),
            {"ok": True, "result": {"digest": "sha256:abc", "approved_digest": "sha256:abc", "stale": False, "id": "CHG-0002"}},
        ])
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
        heads = iter(["aaa", "bbb"])
        outcome = run_prompts.run_prompt(
            "01", "the prompt", check, Path("."), {}, agent, "tictactoe", 4, 10.0,
            telos=telos, checks=lambda *a, **k: [], head=lambda target, env: next(heads),
            log=lambda *_: None,
        )
        self.assertTrue(outcome.passed)
        self.assertEqual(2, outcome.turns)
        self.assertEqual(3.0, outcome.cost_usd)
        self.assertEqual(("the prompt" + run_prompts.RUNNER_NOTE, False, 10.0), agent.messages[0])
        self.assertEqual(("Approved CHG-0001 (digest sha256:abc). Continue.", True, 8.5), agent.messages[1])

    def test_nudges_an_agent_that_only_asked_when_a_tag_is_expected(self):
        telos = FakeTelos([status("coherent")] * 6)
        heads = iter(["aaa", "aaa", "bbb"])
        agent = FakeAgent()
        outcome = run_prompts.run_prompt(
            "02", "p", prompt_checks.PromptCheck(stem="02", tag="v0.2.0"), Path("."), {}, agent,
            "tictactoe", 4, None, telos=telos, checks=lambda *a, **k: [],
            head=lambda target, env: next(heads), log=lambda *_: None,
        )
        self.assertTrue(outcome.passed)
        self.assertEqual(2, outcome.turns)
        self.assertEqual((run_prompts.CONTINUE, True, None), agent.messages[1])

    def test_feeds_failed_checks_back_to_the_agent_then_passes(self):
        telos = FakeTelos([status("coherent")] * 8)
        verdicts = iter([["play: ['X 1 - 0 O'] not in the output (exit 0)"], []])
        heads = iter(["aaa", "bbb", "ccc"])
        agent = FakeAgent()
        check = prompt_checks.PromptCheck(
            stem="02", tag="v0.2.0", play=prompt_checks.Play(input="5\n1\n", expect=("X 1 - 0 O",)),
        )
        outcome = run_prompts.run_prompt(
            "02", "p", check, Path("."), {}, agent, "tictactoe", 4, None,
            telos=telos, checks=lambda *a, **k: next(verdicts),
            head=lambda target, env: next(heads), log=lambda *_: None,
        )
        self.assertTrue(outcome.passed)
        self.assertEqual(2, outcome.turns)
        message = agent.messages[1][0]
        self.assertIn("does not meet the definition of done", message)
        self.assertIn("- play: ['X 1 - 0 O'] not in the output (exit 0)", message)
        self.assertIn("move the tag v0.2.0", message)
        self.assertIn('feeds "5\\n1\\n"', message)

    def test_does_not_nudge_a_prompt_without_a_tag(self):
        telos = FakeTelos([status("coherent")] * 4)
        agent = FakeAgent()
        outcome = run_prompts.run_prompt(
            "05", "p", prompt_checks.PromptCheck(stem="05", human_action="revert"), Path("."), {}, agent,
            "tictactoe", 4, None, telos=telos, checks=lambda *a, **k: [],
            head=lambda target, env: "aaa", log=lambda *_: None,
        )
        self.assertTrue(outcome.passed)
        self.assertEqual(1, outcome.turns)

    def test_fails_when_never_coherent(self):
        telos = FakeTelos([status("changing", [{"id": "CHG-0001", "status": "open", "obligations": []}])] * 6)
        outcome = run_prompts.run_prompt(
            "01", "p", prompt_checks.PromptCheck(stem="01"), Path("."), {}, FakeAgent(), "tictactoe", 2, None,
            telos=telos, checks=lambda *a, **k: [], head=lambda target, env: "", log=lambda *_: None,
        )
        self.assertFalse(outcome.passed)
        self.assertEqual(2, outcome.turns)
        self.assertIn("not coherent after 2 turn(s)", outcome.failures)

    def test_stops_before_a_turn_it_cannot_afford(self):
        telos = FakeTelos([status("changing", [{"id": "CHG-0001", "status": "approved", "obligations": []}])] * 4)
        agent = FakeAgent()
        outcome = run_prompts.run_prompt(
            "01", "p", prompt_checks.PromptCheck(stem="01"), Path("."), {}, agent, "tictactoe", 4, 2.0,
            telos=telos, checks=lambda *a, **k: [], log=lambda *_: None,
        )
        self.assertFalse(outcome.passed)
        self.assertEqual(1, outcome.turns)
        self.assertEqual(1, len(agent.messages))
        self.assertIn("budget exhausted after 1 turn(s)", outcome.failures)

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
