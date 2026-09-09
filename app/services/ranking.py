from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class RankedItem:
    key: str
    value: T
    score: float


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[tuple[str, T]]], *, k: int = 60, limit: int = 20
) -> list[RankedItem]:
    scores: dict[str, float] = {}
    values: dict[str, T] = {}

    for ranking in rankings:
        for rank, (key, value) in enumerate(ranking, start=1):
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            values[key] = value

    ordered = sorted(scores, key=scores.__getitem__, reverse=True)[:limit]
    return [RankedItem(key=key, value=values[key], score=scores[key]) for key in ordered]

