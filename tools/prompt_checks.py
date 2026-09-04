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
        message = proc.stdout.strip()[:200] or proc.stderr.strip()[:200]
        return {"ok": False, "result": None, "error": {"message": message}}


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
    expected: dict[str, int] = {}
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
        failures.append(
            f"proof_evidence is {result.get('proof_evidence')!r}, expected {check.proof_evidence!r}"
        )

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
