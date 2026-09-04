from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Match:
    x_points: int = 0
    o_points: int = 0
    target: int = 2
    winner: str = "none"
    starter: str = "x"


@dataclass(frozen=True)
class RoundResult:
    outcome: str


def round_ended(match: Match, result: RoundResult) -> Match:
    if result.outcome == "x-wins":
        updated = replace(
            match,
            x_points=match.x_points + 1,
            starter="o",
        )
    elif result.outcome == "o-wins":
        updated = replace(
            match,
            o_points=match.o_points + 1,
            starter="x",
        )
    elif result.outcome == "draw":
        return replace(match, starter="o" if match.starter == "x" else "x")
    else:
        raise ValueError(f"unsupported round outcome: {result.outcome}")

    if updated.x_points >= updated.target:
        return replace(updated, winner="x")
    if updated.o_points >= updated.target:
        return replace(updated, winner="o")
    return updated
