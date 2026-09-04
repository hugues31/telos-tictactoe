# 03 — Misère

Change one rule at the heart of the game: three in a row now loses. The
player who completes a line loses the round, the other one wins. Follow
the Telos skills installed in this repository.

Change the existing intent "Three in a row wins" and its three scenarios;
do not add a new intent. `XX.OO....` then cell 3 is now `o-wins`, and so
are the column and the diagonal examples. Run `telos impact` on that
intent first and tell me what else it touches.

The existing tests are sealed with their red and green witnesses: changing
them means new witnesses.

A player who sees "O wins" right after X lined up three must not think the
game is broken. Change the console intent too: the status of a finished
round says who lined up three. `XXXOO....` won by O now reads
`X lined up three: O wins`; a draw still reads `Draw`. With the same
moves as before, the console now prints `X lined up three: O wins`, the
score `X 0 - 1 O`, then `Round 2. X starts.`

Same workflow: change, diff, my approval, red, code, green, bind,
reconcile. Commit as `v0.3: misère` and tag `v0.3.0`.
