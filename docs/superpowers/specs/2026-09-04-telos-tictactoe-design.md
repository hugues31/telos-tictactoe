# Telos Tic-Tac-Toe Design

**Date:** 2026-09-04
**Status:** Approved in conversation, pending written review
**Replaces:** the Momo Tamagotchi story and its Telos v0.11 migration

## Objective

Turn this repository into a first contact with
[Telos](https://github.com/hugues31/telos-sdd) that a newcomer can follow
and that the maintainer can replay at every Telos release: a tic-tac-toe
game in Python, playable in the terminal and in a window, built entirely
from a handful of prompts given to a coding agent on Telos v0.13.0. The
prompts are the end-to-end test of the framework: a human can type them, an
agent can run them, and a runner replays them to check that the framework
still behaves and that the project can be rebuilt prompt by prompt.

Two problems drive the redesign:

- The repository is not compatible with Telos v0.13.0 (lock version 3,
  report-backed test evidence, updated skills, Codex host).
- A newcomer gets lost: eight prompts totalling 67 KB, every prompt mixing a
  mission statement with dozens of exact CLI commands and JSON payloads,
  whimsical vocabulary ("Momo's soul", "the nest before the egg", "the
  eleven gates").

## Decisions taken with the user

| Question | Decision |
|---|---|
| Subject | Tic-tac-toe: a game everyone knows, with enough substance for several bounded contexts. Repository renamed `telos-tictactoe`. |
| Shape of the story | First version with a terminal interface, then add a feature, then change a deep rule, then add a graphical interface that reuses the same logic, then edit a code file by hand. |
| Architecture | Clean architecture: the domain never imports an interface; both interfaces consume the domain through the context map; a Telos constraint with an executable check enforces it. |
| Prompts | Plain text a human would type. No CLI commands, no payloads. |
| Execution | An agent runner (`claude -p` or `codex exec`) replays the prompts; the deterministic replay driver is removed. |
| Tooling kept | GitHub Pages export of the spec, the GIF recorder, Codex support next to Claude. |
| Language | English, technical vocabulary, no jokes. |
| History | A new git history built by the runner replaces `main` after explicit approval of the force push. The old `main` is kept under the tag `legacy-v0.11`. |
| Reference build | First planned as a Claude run capped at 15 USD; after a live spike that spent 8.97 USD on prompts 00 and 01, the user chose Codex (`gpt-5.6-sol`) instead. The reference was built by `tools/run_prompts.py --agent codex` in this session, on their ChatGPT plan. |

## The product

Two players share one keyboard (or one window). X starts. A mark goes on a
free cell, the turn passes, three in a row ends the round. From v0.2 a
match is played to two round wins. From v0.3 the rules are the misère
variant: three in a row loses. From v0.4 the same game opens in a window
with `--gui`.

### Bounded contexts

| Context | Kind | Capability | Owns |
|---|---|---|---|
| `board` | core | `play` | the grid, the turns, the outcome of one round |
| `terminal` | supporting | `console` | what the text console shows |
| `tournament` (v0.2) | core | `standings` | points, the match winner, who starts the next round |
| `desktop` (v0.4) | supporting | `window` | what the window shows and what a click does |

Context map, final state: `terminal` depends on `board` and `tournament`;
`tournament` depends on `board`; `desktop` depends on `board` and
`tournament`. Each dependency publishes one mapping:
`board/Board -> terminal/BoardView`, `tournament/Match -> terminal/MatchView`,
`board/Board -> tournament/RoundResult`, `board/Board -> desktop/BoardView`,
`tournament/Match -> desktop/MatchView`.

### Notions

Enum symbols are lowercase (`x`, `o`, `x-wins`): Telos 0.13.0 accepts an
uppercase symbol at staging and then fails to parse its own change file.

| Notion | Kind | Owner | Attributes |
|---|---|---|---|
| `Board` | entity | `board` | `cells` string of nine characters, `.` for free, `X`, `O`; `turn` enum `x, o`; `outcome` enum `playing, x-wins, o-wins, draw` |
| `PlaceMark` | event | `board/play` | `cell` int, 1 to 9, row by row |
| `BoardView` | value | `terminal` | `cells`, `turn`, `outcome` as above (mapped from `board/Board`) |
| `Screen` | value | `terminal` | `row1`, `row2`, `row3`, `status` strings; from v0.2 `score` string |
| `ShowBoard` | event | `terminal/console` | none |
| `Match` | entity | `tournament` | `x-points` int, `o-points` int, `target` int, `winner` enum `none, x, o`, `starter` enum `x, o` |
| `RoundResult` | value | `tournament` | `outcome` enum `x-wins, o-wins, draw` (mapped from `board/Board`) |
| `RoundEnded` | event | `tournament/standings` | none |
| `MatchView` | value | `terminal`, then `desktop` | `x-points`, `o-points`, `winner` (mapped from `tournament/Match`) |
| `Window` | value | `desktop` | `labels` string of nine characters, `status` string |
| `CellClicked` | event | `desktop/window` | `cell` int |

### Intents and scenarios

Ids below are the ones a fresh replay allocates in staging order; prompts
never mention ids.

| Version | Id | Owner | Title | Template | Scenarios |
|---|---|---|---|---|---|
| v0.1 | INT-0001 | board/play | A mark goes on a free cell and the turn passes | event-driven | the first mark: `.........` turn `x`, cell 5 gives `....X....` turn `o`; O answers: `....X....` turn `o`, cell 1 gives `O...X....` turn `x` |
| v0.1 | INT-0002 | board/play | An occupied cell is refused | unwanted | `....X....` turn `o`, cell 5: cells and turn unchanged |
| v0.1 | INT-0003 | board/play | Three in a row wins | event-driven | a row: `XX.OO....` turn `x`, cell 3 gives `x-wins`; a column: `XO.XO....`, cell 7; a diagonal: `XO.OX....`, cell 9 |
| v0.1 | INT-0004 | board/play | A full board without a line is a draw | event-driven | `XOXXOOOX.` turn `x`, cell 9 gives `draw` |
| v0.1 | INT-0005 | terminal/console | The console shows the grid, free cells by number, and who plays | event-driven on `ShowBoard` | `....X....` turn `o` gives `row2 == " 4 | X | 6"` and `status == "O to play"`; `XXXOO....` outcome `x-wins` gives `status == "X wins"` |
| v0.2 | INT-0006 | tournament/standings | A won round gives its winner a point, a draw gives none | event-driven on `RoundEnded` | `x-wins` from 0-0 gives `x-points == 1`; `draw` leaves 0-0 |
| v0.2 | INT-0007 | tournament/standings | The first player to reach the target wins the match | event-driven on `RoundEnded` | `x-wins` from 1-0 with target 2 gives `winner == x` |
| v0.2 | INT-0008 | tournament/standings | The loser of a round starts the next one | event-driven on `RoundEnded` | `x-wins` with starter `x` gives `starter == o` |
| v0.2 | INT-0005 grows | terminal/console | (same intent) | | `MatchView` 1-0 gives `score == "X 1 - 0 O"` |
| v0.3 | INT-0003 edited | board/play | Three in a row loses | event-driven | the same three scenarios now give `o-wins` |
| v0.3 | INT-0005 edited | terminal/console | (same intent) | | the finished-round status names who lined up three: `XXXOO....` won by O gives `status == "X lined up three: O wins"`, so a player does not read the misère result as a bug |
| v0.4 | INT-0009 | desktop/window | A click on a free cell plays it and refreshes the window | event-driven on `CellClicked` | `.........` turn `x`, click 5 gives `labels == "....X...."` and `status == "O to play  X 0 - 0 O"`; `XX.OO....` turn `x`, click 3 gives `status == "X lined up three: O wins  X 0 - 1 O"` |
| v0.4 | INT-0010 | desktop/window | The window plays the whole match | event-driven on `CellClicked` | after a finished round the next click starts the next round, loser first, and plays it: `XXXOO....` lost by X at 0-1, click 5 gives `labels == "....X...."` and `status == "O to play  X 0 - 1 O"`; when the match is over the status reads `O wins the match  X 0 - 2 O` and a click leaves the labels unchanged |
| v0.4 | CON-0001 | project | The domain never imports an interface | architecture, check `python3 tools/check_layers.py` | |

The window is resizable: rows and columns share the space evenly, marks
use a large font, the status line spans the width, and the window opens
at a comfortable size with a minimum. Layout is checked by hand, not by a
scenario.

Final counts: 4 contexts, 4 capabilities, 13 notions, 10 intents,
18 scenarios, 1 constraint, 5 mappings. Today: 2 contexts, 10 notions,
12 intents, 17 scenarios, 2 constraints, 1 mapping.

### Code layout

```
tictactoe/__main__.py            python -m tictactoe [--gui]; glue, outside the spec
tictactoe/domain/board.py        board context
tictactoe/domain/tournament.py   tournament context (v0.2)
tictactoe/ui/cli.py              terminal context: render + input loop
tictactoe/ui/gui.py              desktop context: presenter (pure) + tkinter window (v0.4)
tests/                           one test per scenario, functions named scn_NNNN_...
tools/check_layers.py            the constraint's check: an AST import guard on tictactoe/domain/
```

`[code] globs` list the four module files explicitly and never the
`__init__.py` or `__main__.py` files. Every listed file is bound to the
intents of its context. The tkinter layer is exercised by hand; the desktop
scenarios are proven through the presenter, which builds the window's
labels and status without a display.

### Terminal contract

The console prints the grid after every move, then a status line, then a
`> ` prompt. Free cells show their number.

```console
$ python -m tictactoe
 1 | 2 | 3
 4 | 5 | 6
 7 | 8 | 9
X to play
> 5
 1 | 2 | 3
 4 | X | 6
 7 | 8 | 9
O to play
> 5
Cell 5 is taken
> 1
```

A round ends with the status `X wins`, `O wins` or `Draw`. From v0.2 the
console starts with `Best of 3. X starts.`, prints the score after every
round as `X 1 - 0 O`, announces `Round 2. O starts.`, and ends the match
with `X wins the match`. From v0.3 (misère) a finished round names who
lined up three, `X lined up three: O wins`, so the result never reads as
a bug; that edit of a sealed console scenario is part of the deep change.
From v0.4 the window shows nine buttons and one status line such as
`O to play  X 0 - 0 O`, plays whole matches like the console, and resizes
with its window.

## The story: prompts and tags

| File | Tag | The game learns | What Telos shows |
|---|---|---|---|
| `prompts/00-setup.md` | `v0.0.0` | nothing yet | `init --agents claude,codex --ci github`, an empty spec already sealed |
| `prompts/01-board-and-console.md` | `v0.1.0` | the rules of one round, in the terminal | change, two contexts, notions, five intents, pytest with a JUnit report, red then green witnesses, bind, the first context-map dependency, reconcile |
| `prompts/02-tournament.md` | `v0.2.0` | a match to two round wins (**adding** a feature) | a new core context, two more mappings, an intent that grows a scenario, existing proofs untouched |
| `prompts/03-misere.md` | `v0.3.0` | three in a row loses (**changing** a deep rule) | `impact` across contexts, `edit intent` on a sealed intent, rewritten scenarios, new red witnesses |
| `prompts/04-window.md` | `v0.4.0` | the same game in a window (**adding** an interface) | a new supporting context that consumes the domain, an architecture constraint with an executable check, the domain untouched |
| `prompts/05-hotfix.md` | none | nothing | a hand edit of bound code, state `drifted`, mutations refused, `revert --expected-state`, and what `adopt` would do |
| `prompts/06-your-turn.md` | none | up to the reader | the loose thread: a finished round still accepts marks |

### Prompt contents

Each prompt is at most one screen. It says what a human would say: the
situation in one or two lines, the request, the examples that become
scenarios, the conventions that keep the result checkable, and the tag to
create. Conventions repeated where relevant: the code layout above, test
functions named after their scenario (`scn_0001_...`), strict TDD through
the Telos skills, the terminal contract, commit and tag at the end.

- **00-setup**: empty git repository; initialise Telos with the Claude Code
  and Codex skills and the GitHub CI gate; add a Python `.gitignore` that
  also ignores `junit.xml`; commit as `v0.0: empty spec`, tag `v0.0.0`.
- **01-board-and-console**: the `board` and `terminal` contexts, the
  notions and the five intents of v0.1 with their examples, the terminal
  contract, the test runner
  `pytest -q --junitxml={report} -k '{filter}'` with the report at
  `junit.xml`, the code globs. Tag `v0.1.0`.
- **02-tournament**: the `tournament` context with its three intents and
  examples, the mappings, the console additions and the grown scenario.
  Tag `v0.2.0`.
- **03-misere**: "three in a row now loses", explicitly "change the
  existing intent and its scenarios, do not add a new one"; the console
  status of a finished round now names who lined up three. Tag `v0.3.0`.
- **04-window**: the `desktop` context, tkinter, the presenter proven
  without a display, `--gui`, whole matches in the window (rule 10), a
  resizable layout, the constraint and its check. Tag `v0.4.0`.
- **05-hotfix**: "Edit `tictactoe/domain/board.py` directly, without opening
  a change, so that a player keeps the turn after playing. Then run
  `telos status` and tell me what you see, try to open a change, explain
  the two ways out, and take the one that restores the sealed code; I will
  confirm." Nothing is committed.
- **06-your-turn**: the loose thread and a suggested path (`telos status`,
  `change open`, `impact`, an `unwanted` intent, `diff`, approve, red,
  code, green, bind, reconcile, tag `v0.5.0`), plus two further ideas: a
  computer opponent as a new context, undoing a move.

### `prompts/checks.toml`

One table per prompt, keyed by the file stem. The runner reads it; a human
replaying by hand reads it as the definition of done.

```toml
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

Checks applied after every prompt that has a table, in this order:

1. `telos status --json` answers `ok` with `result.state == "coherent"`,
   the given `intents` (`coverage.intents_active`, equal to
   `intents_implemented`), `scenarios` (`coverage.scenarios_proved`, equal
   to `scenarios_total`), `constraints` when given, and `proof_evidence`
   when given.
2. `telos check --sealed --json` answers `ok` with no diagnostic.
3. `git status --porcelain` is empty.
4. When `tag` is given, the tag exists and points at `HEAD`.
5. When tests exist, `pytest -q` exits zero.
6. When `play` is given, `python -m tictactoe` fed with `input` exits and
   every `expect` string appears in its stdout. When `help` is given, the
   same with `args`.

A prompt without a table (`06-your-turn`) is not sent.

## The runner: `tools/run_prompts.py`

Standard library only, Python 3.11 or newer (`tomllib`).

### Command line

```console
python3 tools/run_prompts.py [--agent claude|codex] [--telos PATH | --telos-version X.Y.Z]
                             [--target DIR] [--only NN] [--from NN] [--keep]
                             [--model NAME] [--max-budget-usd N] [--max-turns N]
```

- `--agent` defaults to `claude`.
- `--telos-version` downloads the release asset for the current platform
  into `.worktrees/telos/<version>/`, verifies it against `checksums.txt`,
  and puts that binary first on the `PATH` of every subprocess. `--telos`
  uses a binary directly. Without either, the `telos` on `PATH` is used and
  its version is printed.
- `--target` defaults to `.worktrees/run-<agent>-<timestamp>/`, inside the
  repository so agent guards and CI sandboxes see one tree. It must not
  exist unless `--from` or `--only` reuses it.
- `--only NN` runs one prompt against an existing target; `--from NN`
  resumes from that prompt.
- `--max-turns` caps the agent turns per prompt (default 4).
- `--max-budget-usd` is a cap on the whole run: the runner sums the
  `total_cost_usd` of every Claude result, passes the remaining budget to
  each Claude call, prints the total, and aborts the run when the cap is
  reached.

### Loop, per prompt

1. Send the prompt body to the agent, cwd `target`.
   - Claude: `claude -p <body> --output-format json --permission-mode
     acceptEdits --allowedTools <tool list> --permission-prompts none
     --session-id <uuid>`, with `CLAUDECODE` removed from the environment.
     The tool list allows Bash, the file tools, search tools and Skill.
     The exact flags are settled by the first implementation task: the
     requirement is that ordinary tool calls never prompt, while the Telos
     guard's `ask` on `telos change approve`, `telos adopt` and
     `telos revert` is not answered by the agent, so the run stops there.
     The guard allows source-code edits, so prompt 05's hand edit is the
     agent's own.
   - Codex: `codex exec -C <target> --sandbox danger-full-access
     --skip-git-repo-check --dangerously-bypass-hook-trust --json <body>`;
     the static rules prompt on approve/adopt/revert and non-interactive
     Codex cannot answer, so the run stops there too. The sandbox is
     `danger-full-access` because `workspace-write` mounts `.git` read-only
     and `telos change reconcile` writes sealed blobs into the git object
     store; the target is a scratch repository.
2. Read the state: `telos status --json`.
   - A change with status `drafted`, or whose approval is stale: the runner
     runs `telos change diff` and `telos change approve --expected-digest
     <digest>`, prints the digest, and resumes the session with
     `Approved CHG-NNNN (digest <digest>). Continue.`
   - State `drifted` and `human_action = "revert"`: the runner runs
     `telos revert --expected-state <drift.token>`, prints the token, and
     resumes with `Reverted. Continue.`
   - State `drifted` on code paths only while a change is open: the agent
     edited sealed code without claiming it; the runner runs
     `telos adopt --into CHG-NNNN --expected-state <token>`, re-approves
     the new digest, and resumes. Drift under `telos/` stops the run.
   - A change `approved` or `implementing`, or an agent result that is an
     error: resume with `Continue with the request as stated.`
   - State `coherent` with no open change and, when a tag is expected,
     a commit since the prompt started: the prompt is finished. Without a
     new commit the agent only asked or explained; the runner resumes
     with `Continue with the request as stated.`
   The first message of every prompt carries a short note from the runner:
   the hooks and rules are trusted and active, open details are the
   agent's call, and only approve, adopt and revert wait for the human.
   Resume: Claude with `--resume <session-id>`, Codex with `codex exec
   resume --last`.
3. Run the checks once the project is coherent. When they fail and turns
   remain, the runner reads the failures back to the agent, as a human
   would ("the console does not print the score"), asks it to fix them
   through the Telos workflow and to move the tag, then checks again.
4. Stop after `--max-turns` turns. Print one line per prompt:
   `PASS`/`FAIL`, turns, Claude cost, and the first failing check.

Exit code is zero only when every prompt passes. The target is kept on
failure, and with `--keep`; otherwise it is deleted at the end.

## Telos v0.13.0 conformance

- Every install snippet pins `v0.13.0` and the `telos_0.13.0_<platform>`
  assets: README, `prompts/00-setup.md`, `.github/workflows/*.yml`, the
  runner's default `--telos-version`.
- `[test]` is `cmd = "pytest -q --junitxml={report} -k '{filter}'"` and
  `report = "junit.xml"`; `junit.xml` is in `.gitignore` and outside every
  glob. The sealed lock is version 3 with `proof_evidence = "report"`.
- `agents.hosts` is `["claude", "codex"]`. The skills under
  `.claude/skills/` and `.agents/skills/`, the guard hooks in
  `.claude/settings.json` and `.codex/hooks.json`, the rules in
  `.codex/rules/telos.rules`, the Telos block in `AGENTS.md`, the
  `.gitattributes` and the workflow `telos.yml` are exactly what
  `telos init` 0.13.0 writes; nothing generated is edited by hand.
- The README explains, in two sentences, what report-backed evidence means:
  a green is a test named after the scenario that ran and passed; a run
  that executes nothing is refused with `TELOS_TEST_NOT_EXECUTED`. A
  collection error is such a refusal, which is why the implementer writes a
  stub before the first red.
- Bound code is sealed too: the lock's `[code]` table holds the blob id of
  every bound module and test, so a hand edit of `board.py` is drift with
  the same token-bound `adopt`/`revert` exits as a hand edit under
  `telos/`. Prompt 05 rests on this.

## README

Under 100 lines, in this order:

1. Title `Tic-tac-toe, spec-first with Telos`, one paragraph: what the
   game is, that five prompts built it, what Telos is in one sentence.
2. Try it: install Telos 0.13.0, create the venv with pytest, run
   `python -m tictactoe` and `python -m tictactoe --gui`.
3. How it was built: the prompt table above, one row per prompt, with a
   link to each file.
4. Replay it with an agent: the runner command, what it checks, that it
   plays the human for approvals, that it costs tokens.
5. Look at the spec: `telos status`, `telos show NOT:board/Board` (intent
   ids depend on the agent's staging order, notion names do not),
   `telos map`, `telos view --open`, the GitHub Pages link, the GIF.
6. Repository map, eight lines.
7. License.

Two badges: the sealed check and the Pages link. Vocabulary rules for the
README and the prompts: name things by their Telos term (context, notion,
intent, scenario, witness, seal, drift, mapping); no pet names for
concepts, no metaphors, no jokes. The game's own words (board, cell, mark,
round, match) are the only domain vocabulary.

## Tooling kept and retargeted

- `tools/record_demo.py` and `tools/test_record_demo.py`: the same tour
  (dashboard, global search, intent detail with its scenario, graph finder,
  glossary) retargeted: search `three in a row`, land on `INT-0003`,
  scroll to its first scenario, graph query `INT-0003`, glossary `Board`
  (consumed by three contexts). The recorder test asserts those values.
  Output contract unchanged: 1280×800 MP4 and a 960-pixel-wide GIF under
  10 MB.
- `.github/workflows/telos.yml`: generated by `init`, sealed check on every
  push and pull request.
- `.github/workflows/ci.yml`: replaces `demo.yml`. Job `tests`: install
  Telos 0.13.0 and pytest, run `pytest -q` and `telos rebuild status`. Job
  `pages` on `main`: `telos view --export site` and deploy.
- `.github/workflows/demo-gif.yml`: unchanged trigger and pipeline, Telos
  pin bumped to 0.13.0.
- `.github/workflows/prompts.yml`: new, `workflow_dispatch` only, inputs
  `agent` (`claude` or `codex`) and `telos_version` (default `0.13.0`).
  Installs the chosen agent CLI, reads `ANTHROPIC_API_KEY` or
  `OPENAI_API_KEY` from repository secrets, runs the runner, uploads the
  target directory as an artifact. It is never triggered by a push.

## Repository rebuild and history

1. On the current `main`, add this design, the plan, the prompts,
   `checks.toml`, the runner, the retargeted recorder, the README, and the
   workflows. Nothing under `telos/` changes at this step.
2. Run `tools/run_prompts.py --agent claude --telos-version 0.13.0
   --keep --max-budget-usd 15` from the repository. Review the produced
   target: spec, code, tests, commits, tags.
3. Build the new history: fetch the target's `main` into this repository as
   `tictactoe`, then add one final commit on top with the project-level
   files listed in step 1 (`README.md`, `LICENSE`, `docs/`, `prompts/`,
   `tools/`, the three project-owned workflows, `.gitignore` additions for
   `.worktrees/`, `site/`, `docs/demo.mp4`). Regenerate `docs/demo.gif` in
   that commit.
4. Tag the old `main` as `legacy-v0.11`.
5. With the user's explicit go: delete tags `v0.0.0` to `v0.5.0` locally and
   on `origin`, push `legacy-v0.11`, force-push `tictactoe` as `main`, push
   the new tags `v0.0.0` to `v0.4.0`, rename the repository to
   `telos-tictactoe` with `gh repo rename`, update its description.

The final commit is the only commit on the new `main` not produced by the
agent, and it touches nothing under `telos/`.

## Removed

`tamagotchi/`, the old `tests/`, `tools/replay.py`, `tools/check_vitals.py`,
`tools/check_imports.py`, the eight old prompts, `demo.yml`, the two
Tamagotchi design documents under `docs/superpowers/`, the empty `.agents/`
and `.codex/` leftovers, every mention of Momo, and the Telos 0.11 pins.

## Failure handling

- A failed check is read back to the agent while turns remain; when the
  turns run out the runner stops and keeps the target. The prompt text is
  then corrected and the prompt re-run with `--only`, never by weakening
  a check.
- An agent that self-approves under the chosen flags is a design failure of
  the runner flags, not of the prompt; the implementation task adjusts the
  flags until the guard's `ask` reaches nobody.
- An agent-produced reference that does not pass the checks is re-run
  before any manual polish. Manual polish, if any, edits only code and prose
  and is followed by `telos check --sealed`; it never edits `telos/`.
- A recorder checkpoint that no longer matches the view is fixed by
  updating the selector after confirming the 0.13 view, never by removing
  the checkpoint.
- A GIF at or above 10 MB fails; timing is tightened, checkpoints stay.
- The uppercase enum symbol defect is reported upstream to `telos-sdd`;
  the prompts avoid it by spelling symbols in lowercase.

## Verification

Fresh and layered, before the force push:

1. The runner passes end to end with Claude on Telos 0.13.0 in a clean
   target: prompts 00 to 05, every check green, cost printed.
2. On the produced reference: `telos status --json` is `coherent` with
   `proof_evidence = "report"`, 10 active and implemented intents, 18
   proved scenarios, 1 constraint; `telos check --sealed --json` has no
   diagnostic; `telos rebuild status --json` is all green; `pytest -q`
   passes; `telos map --json` lists the four dependencies.
3. `python -m tictactoe` plays the five-move game to
   `X lined up three: O wins` and `X 0 - 1 O`; `python -m tictactoe --gui`
   opens a window on this machine that resizes evenly and plays a whole
   match, checked by screenshot.
4. `python3 tools/check_layers.py` exits zero, and exits one when a
   temporary import of `tictactoe.ui` is added to `board.py`.
5. `python -m unittest tools.test_record_demo` passes; `record_demo.py`
   produces a GIF under 10 MB.
6. `telos view --export` into a directory under `.worktrees/` succeeds.
7. `grep -rn "0\.11\|0\.12\|Momo\|tamagotchi" --exclude-dir=.git
   --exclude-dir=.worktrees` on the new tree returns nothing outside
   `docs/superpowers/` history notes.
8. Codex: prompt 00 alone passes with `--agent codex` on a local run.
