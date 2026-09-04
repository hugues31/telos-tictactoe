from tictactoe.domain.board import Board, PlaceMark
from tictactoe.ui.cli import BoardView, show_board


def print_board(board: Board) -> None:
    screen = show_board(
        BoardView(cells=board.cells, turn=board.turn, outcome=board.outcome)
    )
    print(screen.row1)
    print(screen.row2)
    print(screen.row3)
    print(screen.status)


def main() -> None:
    board = Board()
    print_board(board)

    while board.outcome == "playing":
        try:
            raw_cell = input("> ")
        except EOFError:
            return

        try:
            cell = int(raw_cell)
        except ValueError:
            continue
        if not 1 <= cell <= 9:
            continue

        if not board.place_mark(PlaceMark(cell=cell)):
            print(f"Cell {cell} is taken")
            continue

        print_board(board)


if __name__ == "__main__":
    main()
