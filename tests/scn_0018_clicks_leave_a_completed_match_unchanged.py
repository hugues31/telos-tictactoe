def scn_0018_clicks_leave_a_completed_match_unchanged():
    from tictactoe.domain.board import Board
    from tictactoe.domain.tournament import Match
    from tictactoe.ui.gui import CellClicked, WindowPresenter

    presenter = WindowPresenter(
        board=Board(cells="XXXOO....", turn="o", outcome="o-wins"),
        match=Match(
            x_points=0,
            o_points=2,
            target=2,
            winner="o",
            starter="x",
        ),
    )

    window = presenter.cell_clicked(CellClicked(cell=5))

    assert window.labels == "XXXOO...."
    assert window.status == "O wins the match  X 0 - 2 O"
