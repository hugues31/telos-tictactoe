from dataclasses import dataclass


@dataclass(frozen=True)
class BoardView:
    cells: str
    turn: str
    outcome: str


@dataclass(frozen=True)
class Screen:
    row1: str
    row2: str
    row3: str
    status: str


@dataclass(frozen=True)
class ShowBoard:
    pass


def show_board(view: BoardView, event: ShowBoard | None = None) -> Screen:
    visible = [cell if cell != "." else str(index) for index, cell in enumerate(view.cells, 1)]
    rows = [f" {visible[start]} | {visible[start + 1]} | {visible[start + 2]}" for start in (0, 3, 6)]
    statuses = {
        "playing": f"{view.turn.upper()} to play",
        "x-wins": "X wins",
        "o-wins": "O wins",
        "draw": "Draw",
    }
    return Screen(*rows, status=statuses[view.outcome])
