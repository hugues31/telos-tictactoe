def scn_0014_the_screen_shows_a_one_nil_match_score():
    from tictactoe.ui.cli import BoardView, MatchView, ShowBoard, show_board

    screen = show_board(
        BoardView(cells=".........", turn="x", outcome="playing"),
        ShowBoard(),
        match_view=MatchView(x_points=1, o_points=0),
    )

    assert screen.score == "X 1 - 0 O"
