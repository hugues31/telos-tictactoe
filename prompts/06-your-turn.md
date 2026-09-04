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
