from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from tictactoe import __main__ as app


def test_main_plays_rounds_until_a_player_wins_the_match() -> None:
    moves = iter(
        [
            "1",
            "4",
            "2",
            "5",
            "3",
            "1",
            "4",
            "2",
            "5",
            "3",
            "1",
            "4",
            "2",
            "5",
            "3",
        ]
    )
    output = StringIO()

    with (
        patch("builtins.input", side_effect=lambda _prompt: next(moves)),
        redirect_stdout(output),
    ):
        app.main()

    lines = output.getvalue().splitlines()
    assert lines[:4] == [
        "Best of 3. X starts.",
        " 1 | 2 | 3",
        " 4 | 5 | 6",
        " 7 | 8 | 9",
    ]
    assert _contains_sequence(
        lines,
        [
            "X wins",
            "X 1 - 0 O",
            "Round 2. O starts.",
            " 1 | 2 | 3",
            " 4 | 5 | 6",
            " 7 | 8 | 9",
        ],
    )
    assert _contains_sequence(
        lines,
        [
            "O wins",
            "X 1 - 1 O",
            "Round 3. X starts.",
            " 1 | 2 | 3",
            " 4 | 5 | 6",
            " 7 | 8 | 9",
        ],
    )
    assert lines[-3:] == ["X wins", "X 2 - 1 O", "X wins the match"]


def _contains_sequence(lines: list[str], expected: list[str]) -> bool:
    width = len(expected)
    return any(lines[index : index + width] == expected for index in range(len(lines)))
