from tictactoe.domain.board import Board, PlaceMark


def scn_0005_x_wins_down_the_first_column():
    board = Board(cells="XO.XO....", turn="x", outcome="playing")

    assert board.place_mark(PlaceMark(cell=7)) is True
    assert board.cells == "XO.XO.X.."
    assert board.turn == "o"
    assert board.outcome == "x-wins"
