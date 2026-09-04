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
MIN_TURN_BUDGET_USD = 1.0
RUNNER_NOTE = (
    "\n\n---\nNote from the person running this session: the repository's agent hooks "
    "and rules are reviewed, trusted and active; do not stop to ask about them. "
    "When the request leaves a detail open, choose a sensible option, say which, "
    "and continue. Stop only where Telos requires a human decision (approve, "
    "adopt, revert): I answer those.\n"
)


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
            if last.exists():
                text = last.read_text(encoding="utf-8")
            else:
                text = (proc.stdout + proc.stderr)[-2000:]
        return AgentResult(proc.returncode == 0, text.strip())


def git_head(cwd: Path, env: dict[str, str]) -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=cwd, env=env, text=True, capture_output=True)
    return proc.stdout.strip() if proc.returncode == 0 else ""


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
    changes = result.get("changes", [])
    prefix = ""
    if state == "drifted":
        drift = result.get("drift") or {}
        token = drift.get("token", "")
        paths = drift.get("paths", [])
        if check.human_action == "revert":
            reverted = telos(["revert", "--expected-state", token], target, env)
            if not reverted.get("ok"):
                log(f"  revert refused: {reverted.get('error')}")
                return None
            log(f"  reverted drift {token}")
            return f"Reverted (drift token {token}). Continue."
        if changes and paths and not any(path.startswith("telos/") for path in paths):
            # A code edit outside the change's claims: the human keeps it.
            change_id = changes[0]["id"]
            adopted = telos(["adopt", "--into", change_id, "--expected-state", token], target, env)
            if not adopted.get("ok"):
                log(f"  adopt refused: {adopted.get('error')}")
                return None
            log(f"  adopted {paths} into {change_id}")
            prefix = f"Adopted your edit of {', '.join(paths)} into {change_id}. "
        else:
            log(f"  unexpected drift: {drift}")
            return None
    for change in changes:
        diff = telos(["change", "diff", change["id"]], target, env)
        diff_result = diff.get("result") or {}
        digest = diff_result.get("digest")
        needs_approval = change.get("status") == "drafted" or diff_result.get("stale") \
            or (prefix and diff_result.get("approved_digest") != digest)
        if needs_approval:
            if not digest:
                log(f"  no digest for {change['id']}: {diff.get('error')}")
                return None
            approved = telos(["change", "approve", change["id"], "--expected-digest", digest], target, env)
            if not approved.get("ok"):
                log(f"  approval refused: {approved.get('error')}")
                return None
            log(f"  approved {change['id']} with digest {digest}")
            return f"{prefix}Approved {change['id']} (digest {digest}). Continue."
        return prefix + CONTINUE
    return None if state == "coherent" else CONTINUE


@dataclass
class Outcome:
    stem: str
    passed: bool
    turns: int
    cost_usd: float
    failures: list[str] = field(default_factory=list)


def run_prompt(stem, body, check, target, env, agent, module, max_turns, budget_left,
               telos=telos_json, checks=run_checks, head=git_head, log=print) -> Outcome:
    session = str(uuid.uuid4())
    message, resume, cost, turns, finished = body + RUNNER_NOTE, False, 0.0, 0, False
    start_head = head(target, env)
    while turns < max_turns:
        budget = None if budget_left is None else budget_left - cost
        if budget is not None and budget < MIN_TURN_BUDGET_USD:
            log(f"  budget exhausted: {budget:.2f} USD left, {MIN_TURN_BUDGET_USD:.2f} needed for a turn")
            return Outcome(stem, False, turns, cost, [f"budget exhausted after {turns} turn(s)"])
        turns += 1
        log(f"[{stem}] turn {turns} ({agent.name})")
        result = agent.send(message, target, env, session, resume, budget)
        cost += result.cost_usd
        log(f"  agent {'ok' if result.ok else 'error'}, cost so far {cost:.2f} USD")
        if result.text:
            log("  " + result.text.strip().splitlines()[-1][:200])
        next_message = human_step(target, env, check, telos=telos, log=log)
        if next_message is not None:
            message, resume = next_message, True
            continue
        state = (telos(["status"], target, env).get("result") or {}).get("state")
        if state != "coherent":
            break
        if check.tag and head(target, env) == start_head and turns < max_turns:
            # Coherent but nothing committed: the agent only asked or explained.
            log("  nothing committed yet; asking the agent to go ahead")
            message, resume = CONTINUE, True
            continue
        finished = True
        failures = checks(check, target, env, module)
        if not failures or turns >= max_turns:
            break
        # The human reads the definition of done back to the agent, once per turn left.
        log("  definition of done not met; sending the failures back to the agent")
        message, resume = feedback(failures, check), True
    if not finished:
        failures = [f"not coherent after {turns} turn(s)"]
    for failure in failures:
        log(f"  FAIL {failure}")
    return Outcome(stem, not failures, turns, cost, failures)


def feedback(failures: list[str], check: PromptCheck) -> str:
    lines = ["The result does not meet the definition of done for this prompt:"]
    lines += [f"- {failure}" for failure in failures]
    lines.append("Fix it through the Telos workflow.")
    if check.tag:
        lines.append(f"Commit the fix and move the tag {check.tag} to the fixed commit.")
    if check.play:
        moves = check.play.input.replace("\n", "\\n")
        args = " ".join(check.play.args)
        lines.append(f"The console check feeds \"{moves}\" to `python -m tictactoe {args}`.".replace("  ", " "))
    return "\n".join(lines)


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
