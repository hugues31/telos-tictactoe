from tictactoe.domain.board import Board, PlaceMark
from tictactoe.domain.tournament import Match, RoundResult, round_ended
from tictactoe.ui.cli import BoardView, MatchView, show_board


def print_board(board: Board, match: Match | None = None) -> None:
    screen = show_board(
        BoardView(cells=board.cells, turn=board.turn, outcome=board.outcome),
        match_view=(
            None
            if match is None
            else MatchView(x_points=match.x_points, o_points=match.o_points)
        ),
    )
    print(screen.row1)
    print(screen.row2)
    print(screen.row3)
    print(screen.status)
    if screen.score:
        print(screen.score)


def print_fresh_grid(board: Board) -> None:
    screen = show_board(
        BoardView(cells=board.cells, turn=board.turn, outcome=board.outcome)
    )
    print(screen.row1)
    print(screen.row2)
    print(screen.row3)


def main() -> None:
    match = Match()
    round_number = 1
    print("Best of 3. X starts.")
    board = Board(turn=match.starter)
    print_fresh_grid(board)

    while match.winner == "none":
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

            if board.outcome == "playing":
                print_board(board)
                continue

            match = round_ended(match, RoundResult(outcome=board.outcome))
            print_board(board, match)

        if match.winner != "none":
            print(f"{match.winner.upper()} wins the match")
            return

        round_number += 1
        print(f"Round {round_number}. {match.starter.upper()} starts.")
        board = Board(turn=match.starter)
        print_fresh_grid(board)


if __name__ == "__main__":
    main()
