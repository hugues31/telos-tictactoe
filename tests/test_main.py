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
            "X lined up three: O wins",
            "X 0 - 1 O",
            "Round 2. X starts.",
            " 1 | 2 | 3",
            " 4 | 5 | 6",
            " 7 | 8 | 9",
        ],
    )
    assert lines[-3:] == [
        "X lined up three: O wins",
        "X 0 - 2 O",
        "O wins the match",
    ]


def _contains_sequence(lines: list[str], expected: list[str]) -> bool:
    width = len(expected)
    return any(lines[index : index + width] == expected for index in range(len(lines)))


def scn_0018_clicks_leave_a_completed_match_unchanged_in_main_suite() -> None:
    from tictactoe.domain.board import Board
    from tictactoe.domain.tournament import Match
    from tictactoe.ui.gui import CellClicked, WindowPresenter

    presenter = WindowPresenter(
        board=Board(cells="XXXOO....", turn="o", outcome="o-wins"),
        match=Match(
            x_points=0,
            o_points=2,
            target=2,
            winner="o",
            starter="x",
        ),
    )

    window = presenter.cell_clicked(CellClicked(cell=5))

    assert window.labels == "XXXOO...."
    assert window.status == "O wins the match  X 0 - 2 O"
