from dataclasses import dataclass

from tictactoe.domain.board import Board, PlaceMark
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
class Window:
    labels: str
    status: str


@dataclass(frozen=True)
class CellClicked:
    cell: int


class WindowPresenter:
    def __init__(self, board: Board | None = None, match: Match | None = None) -> None:
        self.board = board if board is not None else Board()
        self.match = match if match is not None else Match()

    def cell_clicked(self, event: CellClicked) -> Window:
        if self.match.winner != "none":
            return self.window()
        if self.board.outcome != "playing":
            self.board = Board(turn=self.match.starter)
        played = self.board.place_mark(PlaceMark(cell=event.cell))
        if played and self.board.outcome != "playing":
            self.match = round_ended(
                self.match,
                RoundResult(outcome=self.board.outcome),
            )
        return self.window()

    def window(self) -> Window:
        board = BoardView(
            cells=self.board.cells,
            turn=self.board.turn,
            outcome=self.board.outcome,
        )
        match = MatchView(
            x_points=self.match.x_points,
            o_points=self.match.o_points,
        )
        if self.match.winner != "none":
            round_status = f"{self.match.winner.upper()} wins the match"
        else:
            round_status = {
                "playing": f"{board.turn.upper()} to play",
                "x-wins": "O lined up three: X wins",
                "o-wins": "X lined up three: O wins",
                "draw": "Draw",
            }[board.outcome]
        return Window(
            labels=board.cells,
            status=(
                f"{round_status}  "
                f"X {match.x_points} - {match.o_points} O"
            ),
        )


def run_gui(presenter: WindowPresenter | None = None) -> None:
    import tkinter as tk

    presenter = presenter if presenter is not None else WindowPresenter()
    root = tk.Tk()
    root.title("Tic-tac-toe")
    root.geometry("480x540")
    root.minsize(300, 340)
    root.resizable(True, True)

    for row in range(3):
        root.rowconfigure(row, weight=1, uniform="cells")
    for column in range(3):
        root.columnconfigure(column, weight=1, uniform="cells")

    buttons: list[tk.Button] = []
    status = tk.Label(
        root,
        anchor="center",
        font=("TkDefaultFont", 14),
        padx=8,
        pady=10,
    )

    def draw(window: Window) -> None:
        for button, label in zip(buttons, window.labels, strict=True):
            button.configure(text="" if label == "." else label)
        status.configure(text=window.status)

    def click(cell: int) -> None:
        draw(presenter.cell_clicked(CellClicked(cell=cell)))

    for index in range(9):
        button = tk.Button(
            root,
            font=("TkDefaultFont", 36, "bold"),
            command=lambda cell=index + 1: click(cell),
        )
        button.grid(
            row=index // 3,
            column=index % 3,
            sticky="nsew",
            padx=2,
            pady=2,
        )
        buttons.append(button)

    status.grid(row=3, column=0, columnspan=3, sticky="ew")
    root.bind(
        "<Configure>",
        lambda event: status.configure(wraplength=max(260, event.width - 24)),
    )
    draw(presenter.window())
    root.mainloop()
