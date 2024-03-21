from typing import TypedDict


class Rating(TypedDict):
    """A `TypedDict` representing a rating."""

    value: int
    description: str


class Criterion(TypedDict):
    """A `TypedDict` representing a criterion."""

    question: str
    ratings: list[Rating]
