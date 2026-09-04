from dataclasses import dataclass


WINNING_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


@dataclass(frozen=True)
class PlaceMark:
    cell: int


@dataclass
class Board:
    cells: str = "........."
    turn: str = "x"
    outcome: str = "playing"

    def place_mark(self, event: PlaceMark) -> bool:
        index = event.cell - 1
        if self.cells[index] != ".":
            return False

        mark = self.turn.upper()
        self.cells = f"{self.cells[:index]}{mark}{self.cells[index + 1:]}"
        self.turn = "o" if self.turn == "x" else "x"
        if any(all(self.cells[cell] == mark for cell in line) for line in WINNING_LINES):
            self.outcome = f"{mark.lower()}-wins"
        elif "." not in self.cells:
            self.outcome = "draw"
        return True
