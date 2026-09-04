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

One intent per numbered rule, one scenario per example.

9. A click on a free cell plays it and refreshes the window. From
   `.........` with X to play, clicking 5 gives labels `....X....` and
   status `O to play  X 0 - 0 O`. From `XX.OO....` with X to play,
   clicking 3 gives status `X lined up three: O wins  X 0 - 1 O`.
10. The window plays the whole match, like the console. After a finished
    round, the next click on any cell starts the next round with the
    loser first and plays that click: from `XXXOO....` lost by X with
    the score 0-1, clicking 5 gives labels `....X....` and status
    `O to play  X 0 - 1 O`. When the match is over, the status reads
    `O wins the match  X 0 - 2 O` and clicks change nothing: from
    `XXXOO....` with the score 0-2, clicking 5 leaves the labels
    `XXXOO....`.

## Architecture

The window's logic lives in a presenter that builds `labels` and `status`
without a display; tkinter only draws what the presenter says, and the
tests prove the presenter. Add a project constraint of kind
`architecture`, "The domain never imports an interface", with the
executable check `python3 tools/check_layers.py`: it exits non-zero if
any module under `tictactoe/domain/` imports `tictactoe.ui`, `tkinter`,
`argparse` or `sys`.

## Window

The window is resizable and stays usable at any size: the three rows and
three columns share the space evenly, marks use a large font, the status
line spans the full width, and the window opens at a comfortable size
with a sensible minimum.

## Code

- `tictactoe/ui/gui.py` joins the code globs. `tictactoe/__main__.py`
  gains `--gui`.

Same workflow: change, diff, my approval, red, code, green, bind,
reconcile. Commit as `v0.4: a window` and tag `v0.4.0`.
