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

One intent per numbered rule, one scenario per example.

6. A won round gives its winner a point, a draw gives none. From 0-0,
   `x-wins` gives `x-points` 1. From 0-0, a draw leaves 0-0.
7. The first player to reach the target wins the match. From 1-0 with
   target 2, `x-wins` makes X the winner.
8. The loser of a round starts the next one; after a draw, the other
   player starts. After `x-wins` with starter `x`, the starter is `o`.

The console shows the score. Map `tournament/Match` to
`terminal/MatchView` and give `Screen` a `score`: for 1-0 it reads
`X 1 - 0 O`. Grow the existing console intent with that scenario; do not
add a new intent for it.

## Code

- `tictactoe/domain/tournament.py` joins the code globs.
- `tictactoe/__main__.py`, the glue outside the spec, now runs a whole
  match: start with `Best of 3. X starts.`; after a round print the
  status, the score line, then `Round 2. O starts.` and a fresh grid; end
  with `X wins the match` or `O wins the match`.

Same workflow as before: change, diff, my approval, red, code, green,
bind, reconcile. Commit as `v0.2: a match to two wins` and tag `v0.2.0`.
