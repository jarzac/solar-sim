"""2D vector helpers for simulation math."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True, slots=True)
class Vector2:
    """A lightweight immutable 2D vector."""

    x: float
    y: float

    def __add__(self, other: Vector2) -> Vector2:
        """Return vector addition."""
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        """Return vector subtraction."""
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2:
        """Return scalar multiplication."""
        return Vector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vector2:
        """Return scalar multiplication."""
        return self * scalar

    def __truediv__(self, scalar: float) -> Vector2:
        """Return scalar division."""
        return Vector2(self.x / scalar, self.y / scalar)

    def magnitude(self) -> float:
        """Return vector length."""
        return sqrt(self.x * self.x + self.y * self.y)

    def normalized(self) -> Vector2:
        """Return unit vector or zero vector if near zero."""
        mag = self.magnitude()
        if mag == 0.0:
            return Vector2(0.0, 0.0)
        return self / mag
