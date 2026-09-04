def scn_0017_the_losing_x_starts_the_next_round_with_the_clicked_cell():
    from tictactoe.domain.board import Board
    from tictactoe.domain.tournament import Match
    from tictactoe.ui.gui import CellClicked, WindowPresenter

    presenter = WindowPresenter(
        board=Board(cells="XXXOO....", turn="o", outcome="o-wins"),
        match=Match(
            x_points=0,
            o_points=1,
            target=2,
            winner="none",
            starter="x",
        ),
    )

    window = presenter.cell_clicked(CellClicked(cell=5))

    assert window.labels == "....X...."
    assert window.status == "O to play  X 0 - 1 O"
