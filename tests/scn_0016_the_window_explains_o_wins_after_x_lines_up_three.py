def scn_0016_the_window_explains_o_wins_after_x_lines_up_three():
    from tictactoe.domain.board import Board
    from tictactoe.domain.tournament import Match
    from tictactoe.ui.gui import CellClicked, WindowPresenter

    presenter = WindowPresenter(
        board=Board(cells="XX.OO....", turn="x", outcome="playing"),
        match=Match(x_points=0, o_points=0),
    )

    window = presenter.cell_clicked(CellClicked(cell=3))

    assert window.status == "X lined up three: O wins  X 0 - 1 O"
