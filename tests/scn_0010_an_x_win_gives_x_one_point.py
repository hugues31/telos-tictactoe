def scn_0010_an_x_win_gives_x_one_point():
    from tictactoe.domain.tournament import Match, RoundResult, round_ended

    match = round_ended(Match(), RoundResult(outcome="x-wins"))

    assert match.x_points == 1
    assert match.o_points == 0
