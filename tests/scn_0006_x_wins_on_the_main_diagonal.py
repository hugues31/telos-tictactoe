from tictactoe.domain.board import Board, PlaceMark


def scn_0006_x_wins_on_the_main_diagonal():
    board = Board(cells="XO.OX....", turn="x", outcome="playing")

    assert board.place_mark(PlaceMark(cell=9)) is True
    assert board.cells == "XO.OX...X"
    assert board.turn == "o"
    assert board.outcome == "x-wins"
