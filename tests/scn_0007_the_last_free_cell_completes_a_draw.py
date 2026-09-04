from tictactoe.domain.board import Board, PlaceMark


def scn_0007_the_last_free_cell_completes_a_draw():
    board = Board(cells="XOXXOOOX.", turn="x", outcome="playing")

    assert board.place_mark(PlaceMark(cell=9)) is True
    assert board.cells == "XOXXOOOXX"
    assert board.turn == "o"
    assert board.outcome == "draw"
