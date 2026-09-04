from tictactoe.domain.board import Board, PlaceMark


def scn_0003_an_occupied_cell_leaves_the_board_and_turn_unchanged():
    board = Board(cells="....X....", turn="o", outcome="playing")

    assert board.place_mark(PlaceMark(cell=5)) is False
    assert board.cells == "....X...."
    assert board.turn == "o"
    assert board.outcome == "playing"
