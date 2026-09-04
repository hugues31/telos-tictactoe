def scn_0015_x_takes_the_centre_and_the_window_shows_o_to_play():
    from tictactoe.domain.board import Board
    from tictactoe.domain.tournament import Match
    from tictactoe.ui.gui import CellClicked, WindowPresenter

    presenter = WindowPresenter(
        board=Board(cells=".........", turn="x", outcome="playing"),
        match=Match(x_points=0, o_points=0),
    )

    window = presenter.cell_clicked(CellClicked(cell=5))

    assert window.labels == "....X...."
    assert window.status == "O to play  X 0 - 0 O"
