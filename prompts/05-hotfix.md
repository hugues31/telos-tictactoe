# 05 — A hotfix

Do this the wrong way on purpose. Edit `tictactoe/domain/board.py`
directly, without opening a Telos change, so that a player keeps the turn
after playing a mark. Do not touch the tests.

Then run `telos status` and tell me what it reports. Try to open a change
and tell me what happens. Explain the two ways out, `telos adopt` and
`telos revert`, and what each would do with this edit. Take the one that
restores the sealed code; I will confirm it.

Do not commit anything.
