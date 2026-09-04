import pytest


def scn_0001_x_takes_the_centre_and_o_plays_next():
    try:
        from tictactoe.domain.board import Board, PlaceMark
    except ImportError as error:
        pytest.fail(f"board context is unavailable: {error}")

    board = Board(cells=".........", turn="x", outcome="playing")

    assert board.place_mark(PlaceMark(cell=5)) is True
    assert board.cells == "....X...."
    assert board.turn == "o"
    assert board.outcome == "playing"
