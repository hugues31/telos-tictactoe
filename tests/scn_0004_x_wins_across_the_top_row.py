from tictactoe.domain.board import Board, PlaceMark


def scn_0004_x_wins_across_the_top_row():
    board = Board(cells="XX.OO....", turn="x", outcome="playing")

    assert board.place_mark(PlaceMark(cell=3)) is True
    assert board.cells == "XXXOO...."
    assert board.turn == "o"
    assert board.outcome == "x-wins"
