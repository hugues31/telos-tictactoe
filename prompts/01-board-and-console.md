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

One intent per numbered rule, one scenario per example.

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
