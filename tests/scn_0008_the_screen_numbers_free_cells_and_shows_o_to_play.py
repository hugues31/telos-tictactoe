import pytest


def scn_0008_the_screen_numbers_free_cells_and_shows_o_to_play():
    try:
        from tictactoe.ui.cli import BoardView, ShowBoard, show_board
    except ImportError as error:
        pytest.fail(f"terminal context is unavailable: {error}")

    view = BoardView(cells="....X....", turn="o", outcome="playing")

    screen = show_board(view, ShowBoard())

    assert screen.row1 == " 1 | 2 | 3"
    assert screen.row2 == " 4 | X | 6"
    assert screen.row3 == " 7 | 8 | 9"
    assert screen.status == "O to play"
