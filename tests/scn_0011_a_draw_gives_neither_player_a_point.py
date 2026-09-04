def scn_0011_a_draw_gives_neither_player_a_point():
    from tictactoe.domain.tournament import Match, RoundResult, round_ended

    match = round_ended(Match(), RoundResult(outcome="draw"))

    assert match.x_points == 0
    assert match.o_points == 0
