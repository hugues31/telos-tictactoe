from tictactoe.ui.cli import BoardView, ShowBoard, show_board


def scn_0009_the_screen_announces_an_x_win():
    view = BoardView(cells="XXXOO....", turn="o", outcome="o-wins")

    screen = show_board(view, ShowBoard())

    assert screen.row1 == " X | X | X"
    assert screen.row2 == " O | O | 6"
    assert screen.row3 == " 7 | 8 | 9"
    assert screen.status == "X lined up three: O wins"
