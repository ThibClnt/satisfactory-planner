from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Tuple

from collision_detection.vector2 import Vector2
import math


def _is_number(item) -> bool:
    return isinstance(item, int) or isinstance(item, float)


class Collider(metaclass=ABCMeta):

    def __contains__(self, item):
        if isinstance(item, tuple) and len(item) == 2 and _is_number(item[0]) and _is_number(item[1]):
            return self.contains(item)

    @abstractmethod
    def contains(self, position: tuple[float, float]) -> bool:
        pass


class BasicColliderShape(Collider, metaclass=ABCMeta):

    @abstractmethod
    def contains(self, position: tuple[float, float]) -> bool:
        pass


class CircleCollider(BasicColliderShape):

    def __init__(self, x: float, y: float, radius: float):
        self.x: float = x
        self.y: float = y
        self.r: float = radius

    def contains(self, position: tuple[float, float]) -> bool:
        x, y = position

        x, y = position

        if not(self.x - self.r < x < self.x + self.r and self.y - self.r < y < self.y + self.r):
            return False

        return (x - self.x) ** 2 + (y - self.y) ** 2 <= self.r ** 2


class AABBCollider(BasicColliderShape):

    def __init__(self, x: float, y: float, width: float, height: float):
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height

    def contains(self, position: tuple[float, float]) -> bool:
        x, y = position
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height


class RectangleCollider(BasicColliderShape):

    def __init__(self, x: float, y: float, width: float, height: float, angle: float = 0):
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height
        self.angle: float = angle

        cs, sn = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        x0, y0 = x - height * sn, y - height * cs
        x1, y1 = x0 + width * cs, y0 - width * sn
        x3, y3 = x1 + height * sn, y0 + height * cs

        self.min_x = min(x0, x1, x, x3)
        self.max_x = max(x0, x1, x, x3)
        self.min_y = min(y0, y1, y, y3)
        self.max_y = max(y0, y1, y, y3)

    def contains(self, position: tuple[float, float]) -> bool:
        a, b = position

        if not(self.min_x < a < self.max_x and self.min_y < b < self.max_y):
            return False

        p = Vector2(*position)
        q = Vector2(self.x, self.y)
        d1 = Vector2(1, 0).rotate(math.radians(self.angle))
        d2 = Vector2(0, 1).rotate(math.radians(self.angle))

        s = Vector2(p.x - q.x, q.y - p.y)

        r1 = Vector2.dot(s, d1)
        r2 = Vector2.dot(s, d2)

        return 0 <= r1 <= self.width and 0 <= r2 <= self.height


class ArcCollider(BasicColliderShape):

    def __init__(self, x: float, y: float, radius: float, start_angle: float, stop_angle: float):
        self.x: float = x
        self.y: float = y
        self.r: radius = radius
        self.start_angle: float = math.radians(min(max(start_angle, 0.0), 360.0))
        self.stop_angle: float = math.radians(min(max(self.start_angle, stop_angle), self.start_angle + 360.0))

    def contains(self, position: tuple[float, float]) -> bool:
        x, y = position

        if not(self.x - self.r < x < self.x + self.r and self.y - self.r < y < self.y + self.r):
            return False

        p = Vector2(*position)
        q = Vector2(self.x, self.y)
        s = Vector2(p.x - q.x, q.y - p.y)
        u = Vector2(1, 0)

        angle = 2 * math.pi - s.angle(u)
        return (x - self.x) ** 2 + (y - self.y) ** 2 <= self.r ** 2 and self.start_angle < angle < self.stop_angle


class PolygonCollider(BasicColliderShape):

    def __init__(self, points: Tuple[Tuple[float, float], ...]):
        self.points = points
        self.min_x = min(*points, key=lambda p: p[0])[0]
        self.min_y = min(*points, key=lambda p: p[1])[1]
        self.max_x = max(*points, key=lambda p: p[0])[0]
        self.max_y = max(*points, key=lambda p: p[1])[1]

    def contains(self, position: tuple[float, float]) -> bool:
        px, py = position

        if not(self.min_x < px < self.max_x and self.min_y < py < self.max_y):
            return False

        c = False

        for i in range(-1, len(self.points) - 1):
            x0, y0 = self.points[i]
            x1, y1 = self.points[i + 1]

            if y1 == y0:
                continue

            not_same_side = (py > y0) != (py > y1)
            ux = (x1 - x0) * (py - y0) / (y1 - y0) + x0

            if not_same_side and px < ux:
                c = not c

        return c


class CompositeCollider(Collider, metaclass=ABCMeta):

    def __init__(self, *colliders: Collider):
        self.colliders = colliders

    @abstractmethod
    def contains(self, position: tuple[float, float]) -> bool:
        pass


class ColliderUnion(CompositeCollider):

    def contains(self, position: tuple[float, float]) -> bool:
        for collider in self.colliders:
            if collider.contains(position):
                return True

        return False


class ColliderIntersection(CompositeCollider):

    def contains(self, position: tuple[float, float]) -> bool:
        for collider in self.colliders:
            if not collider.contains(position):
                return False

        return True


class XorCollider(CompositeCollider):

    def contains(self, position: tuple[float, float]) -> bool:
        c = False
        for collider in self.colliders:
            if collider.contains(position):
                c = not c

        return c


class SubstractCollider(CompositeCollider):

    def __init__(self, base_collider: Collider, *colliders: Collider):
        super().__init__(*colliders)
        self.base_collider = base_collider

    def contains(self, position: tuple[float, float]) -> bool:
        if not(self.base_collider.contains(position)):
            return False

        for collider in self.colliders:
            if collider.contains(position):
                return False

        return True


class InvertedCollider(Collider):

    def __init__(self, collider: Collider):
        self.collider = collider

    def contains(self, position: tuple[float, float]) -> bool:
        return not self.collider.contains(position)
