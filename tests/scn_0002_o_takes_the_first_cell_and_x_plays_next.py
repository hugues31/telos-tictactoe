from tictactoe.domain.board import Board, PlaceMark


def scn_0002_o_takes_the_first_cell_and_x_plays_next():
    board = Board(cells="....X....", turn="o", outcome="playing")

    assert board.place_mark(PlaceMark(cell=1)) is True
    assert board.cells == "O...X...."
    assert board.turn == "x"
    assert board.outcome == "playing"
