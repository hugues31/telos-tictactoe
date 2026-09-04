from dataclasses import dataclass
from collections.abc import Callable, Iterable

from tictactoe.domain.tournament import Match, RoundResult, round_ended


@dataclass(frozen=True)
class BoardView:
    cells: str
    turn: str
    outcome: str


@dataclass(frozen=True)
class MatchView:
    x_points: int
    o_points: int


@dataclass(frozen=True)
class Screen:
    row1: str
    row2: str
    row3: str
    status: str
    score: str = ""


@dataclass(frozen=True)
class ShowBoard:
    pass


def show_board(
    view: BoardView,
    event: ShowBoard | None = None,
    match_view: MatchView | None = None,
) -> Screen:
    visible = [cell if cell != "." else str(index) for index, cell in enumerate(view.cells, 1)]
    rows = [f" {visible[start]} | {visible[start + 1]} | {visible[start + 2]}" for start in (0, 3, 6)]
    statuses = {
        "playing": f"{view.turn.upper()} to play",
        "x-wins": "O lined up three: X wins",
        "o-wins": "X lined up three: O wins",
        "draw": "Draw",
    }
    score = "" if match_view is None else f"X {match_view.x_points} - {match_view.o_points} O"
    return Screen(*rows, status=statuses[view.outcome], score=score)


def play_match(
    completed_rounds: Iterable[BoardView],
    write: Callable[[str], None] = print,
) -> Match:
    match = Match()
    write("Best of 3. X starts.")
    _write_fresh_grid(match.starter, write)

    for round_number, round_view in enumerate(completed_rounds, 1):
        if round_view.outcome == "playing":
            raise ValueError("a completed round must have a final outcome")

        match = round_ended(match, RoundResult(outcome=round_view.outcome))
        screen = show_board(
            round_view,
            match_view=MatchView(
                x_points=match.x_points,
                o_points=match.o_points,
            ),
        )
        write(screen.row1)
        write(screen.row2)
        write(screen.row3)
        write(screen.status)
        write(screen.score)

        if match.winner != "none":
            write(f"{match.winner.upper()} wins the match")
            return match

        write(f"Round {round_number + 1}. {match.starter.upper()} starts.")
        _write_fresh_grid(match.starter, write)

    raise ValueError("completed rounds ended before the match had a winner")


def _write_fresh_grid(starter: str, write: Callable[[str], None]) -> None:
    screen = show_board(BoardView(cells=".........", turn=starter, outcome="playing"))
    write(screen.row1)
    write(screen.row2)
    write(screen.row3)
