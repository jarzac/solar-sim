"""3D vector helpers for simulation math."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(frozen=True, slots=True)
class Vector3:
    """A lightweight immutable 3D vector."""

    x: float
    y: float
    z: float

    def __add__(self, other: Vector3) -> Vector3:
        """Return vector addition."""
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Vector3) -> Vector3:
        """Return vector subtraction."""
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Vector3:
        """Return scalar multiplication."""
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> Vector3:
        """Return scalar multiplication."""
        return self * scalar

    def __truediv__(self, scalar: float) -> Vector3:
        """Return scalar division."""
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def magnitude(self) -> float:
        """Return vector length."""
        return sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

