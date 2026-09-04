def scn_0012_x_reaches_the_target_and_wins_the_match():
    from tictactoe.domain.tournament import Match, RoundResult, round_ended

    match = round_ended(
        Match(x_points=1, o_points=0, target=2, winner="none", starter="x"),
        RoundResult(outcome="x-wins"),
    )

    assert match.winner == "x"
