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

![The window after a few moves](docs/window.png)

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
prompt to `claude -p` (or `codex exec` with `--agent codex`) with a short
note saying the hooks are trusted and open details are the agent's call,
and plays the human where Telos requires one: it reads `telos change diff`
and approves the digest it shows, it adopts a code edit the agent made
outside its change, and it confirms the revert of prompt 05.
After each prompt it checks the definition of done in
[`prompts/checks.toml`](prompts/checks.toml): state `coherent`, the
expected numbers of intents and scenarios, `telos check --sealed`, a clean
tree, the tag, `pytest`, and a scripted game on the console. A failed
check is read back to the agent while turns remain. It costs tokens;
`--max-budget-usd` caps a Claude run. Point it at a new Telos release
with `--telos-version`.

## Look at the spec

```console
telos status                 # state, coverage, proof evidence
telos show NOT:board/Board   # one notion, its attributes and who uses it
telos map                    # the context map
telos view --open            # the spec as a site
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
