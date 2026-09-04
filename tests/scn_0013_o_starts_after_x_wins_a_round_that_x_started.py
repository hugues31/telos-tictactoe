def scn_0013_o_starts_after_x_wins_a_round_that_x_started():
    from tictactoe.domain.tournament import Match, RoundResult, round_ended

    match = round_ended(
        Match(x_points=0, o_points=0, target=2, winner="none", starter="x"),
        RoundResult(outcome="x-wins"),
    )

    assert match.starter == "o"
