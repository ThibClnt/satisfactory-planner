from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Tuple
import pygame
import math

from collision_detection.hitboxes import Collider, ArcCollider, CircleCollider, AABBCollider, RectangleCollider, PolygonCollider


class Shape(metaclass=ABCMeta):

    def __init__(self):
        self._collider: Collider | None = None

    @abstractmethod
    def draw(self, surface: pygame.Surface):
        pass

    @property
    def collider(self) -> Collider:
        return self._collider


class Circle(Shape):

    def __init__(self, x: float, y: float, r: float, fillcolor=None, bordercolor=(255, 255, 255), borderwidth: int = 1):
        super().__init__()
        self.__x, self.__y, self.__r = x, y, r
        self.fillcolor, self.bordercolor = fillcolor, bordercolor
        self.borderwidth = borderwidth
        self._collider = CircleCollider(x, y, r)

    def draw(self, surface: pygame.Surface):
        if self.borderwidth != 0:
            pygame.draw.circle(surface, self.bordercolor, (self.__x, self.__y), self.__r, self.borderwidth)
        if self.bordercolor is not None:
            pygame.draw.circle(surface, self.fillcolor, (self.__x, self.__y), self.__r)

    @property
    def x(self) -> float:
        return self.__x

    @x.setter
    def x(self, value: float):
        self.__x = value

    @property
    def y(self) -> float:
        return self.__y

    @y.setter
    def y(self, value: float):
        self.__y = value

    @property
    def r(self) -> float:
        return self.__r

    @r.setter
    def r(self, value: float):
        self.__r = value


class Arc(Shape):

    def __init__(self, x: float, y: float, r: float, start_angle: float, stop_angle: float, bordercolor=(255, 255, 255), borderwidth: int = 1):
        super().__init__()
        self.__x, self.__y, self.__r = x, y, r
        self.__start_angle: float = math.radians(min(max(start_angle, 0.0), 360.0))
        self.__stop_angle: float = math.radians(min(max(self.__start_angle, stop_angle), self.__start_angle + 360.0))
        self.bordercolor = bordercolor
        self.borderwidth = borderwidth
        self._collider = ArcCollider(x, y, r, start_angle, stop_angle)

    def draw(self, surface: pygame.Surface):
        pygame.draw.arc(surface, self.bordercolor, ((self.__x - self.__r, self.__y - self.__r), (2 * self.__r, 2 * self.__r)), self.__start_angle, self.__stop_angle, self.borderwidth)
        pygame.draw.line(surface, self.bordercolor, (self.__x, self.__y), (self.x + self.__r * math.cos(self.__start_angle), self.y - self.__r * math.sin(self.__start_angle)), self.borderwidth)
        pygame.draw.line(surface, self.bordercolor, (self.__x, self.__y), (self.x + self.__r * math.cos(self.__stop_angle), self.y - self.__r * math.sin(self.__stop_angle)), self.borderwidth)

    @property
    def fillcolor(self):
        return self.bordercolor

    @fillcolor.setter
    def fillcolor(self, value):
        self.bordercolor = value

    @property
    def x(self) -> float:
        return self.__x

    @x.setter
    def x(self, value: float):
        self.__x = value

    @property
    def y(self) -> float:
        return self.__y

    @y.setter
    def y(self, value: float):
        self.__y = value

    @property
    def r(self) -> float:
        return self.__r

    @r.setter
    def r(self, value: float):
        self.__r = value

    @property
    def start_angle(self):
        return math.degrees(self.__start_angle)

    @start_angle.setter
    def start_angle(self, value: float):
        self.__start_angle = math.radians(value)

    @property
    def stop_angle(self):
        return math.degrees(self.__start_angle)

    @stop_angle.setter
    def stop_angle(self, value: float):
        self.__start_angle = math.radians(value)


class AABB(Shape):

    def __init__(self, x: float, y: float, width: float, height: float,
                 fillcolor=None, bordercolor=(255, 255, 255), borderwidth: int = 1):
        super().__init__()
        self.__x, self.__y, self.__width, self.__height = x, y, width, height
        self.fillcolor, self.bordercolor = fillcolor, bordercolor
        self.borderwidth = borderwidth
        self._collider = AABBCollider(x, y, width, height)

    def draw(self, surface: pygame.Surface):
        if self.borderwidth != 0:
            pygame.draw.rect(surface, self.bordercolor, ((self.__x, self.__y), (self.__width, self.__height)), self.borderwidth)

        if self.fillcolor is not None:
            pygame.draw.rect(surface, self.fillcolor, ((self.__x, self.__y), (self.__width, self.__height)))

    @property
    def x(self) -> float:
        return self.__x

    @x.setter
    def x(self, value: float):
        self.__x = value

    @property
    def y(self) -> float:
        return self.__y

    @y.setter
    def y(self, value: float):
        self.__y = value

    @property
    def width(self) -> float:
        return self.__width

    @width.setter
    def width(self, value: float):
        self.__width = value

    @property
    def height(self) -> float:
        return self.__height

    @height.setter
    def height(self, value: float):
        self.__height = value


class Rectangle(Shape):

    def __init__(self, x: float, y: float, width: float, height: float, angle: float,
                 fillcolor=None, bordercolor=(255, 255, 255), borderwidth: int = 1):
        super().__init__()
        self.__x0, self.__y0 = x, y
        self.__width, self.__height = width, height
        self.__angle = math.radians(angle)
        self.fillcolor, self.bordercolor = fillcolor, bordercolor
        self.borderwidth = borderwidth

        self.__recompute_vertices()
        self._collider = RectangleCollider(self.__x2, self.__y2, width, height, angle)

    def __recompute_vertices(self):
        """
        x0, y0          x1, y1

        x2, y2          x3, y3
        """
        cs, sn = math.cos(self.__angle), math.sin(self.__angle)
        self.__x1, self.__y1 = self.__x0 + self.__width * cs, self.__y0 - self.__width * sn
        self.__x2, self.__y2 = self.__x0 + self.__height * sn, self.__y0 + self.__height * cs
        self.__x3, self.__y3 = self.__x1 + self.__height * sn, self.__y1 + self.__height * cs

    def draw(self, surface: pygame.Surface):
        if self.borderwidth != 0:
            pygame.draw.polygon(surface, self.bordercolor,
                                [
                                    (self.__x0, self.__y0),
                                    (self.__x1, self.__y1),
                                    (self.__x3, self.__y3),
                                    (self.__x2, self.__y2)
                                ], self.borderwidth)

        if self.fillcolor is not None:
            pygame.draw.polygon(surface, self.fillcolor,
                                [
                                    (self.__x0, self.__y0),
                                    (self.__x1, self.__y1),
                                    (self.__x3, self.__y3),
                                    (self.__x2, self.__y2)
                                ])

    @property
    def x(self) -> float:
        return self.__x0

    @x.setter
    def x(self, value: float):
        self.__x0 = value

    @property
    def y(self) -> float:
        return self.__y0

    @y.setter
    def y(self, value: float):
        self.__y0 = value

    @property
    def width(self) -> float:
        return self.__width

    @width.setter
    def width(self, value: float):
        self.__width = value

    @property
    def height(self) -> float:
        return self.__height

    @height.setter
    def height(self, value: float):
        self.__height = value

    @property
    def angle(self):
        return math.degrees(self.__angle)

    @angle.setter
    def angle(self, value: float):
        self.__angle = math.radians(value)
        self.__recompute_vertices()


class Polygon(Shape):

    def __init__(self, points: Tuple[Tuple[float, float], ...], fillcolor=None, bordercolor=(255, 255, 255), borderwidth: int = 1):
        super().__init__()
        self.points: Tuple[Tuple[float, float], ...] = points
        self.fillcolor = fillcolor
        self.bordercolor = bordercolor
        self.borderwidth: int = borderwidth
        self._collider = PolygonCollider(self.points)

    def draw(self, surface: pygame.Surface):
        if self.borderwidth != 0:
            pygame.draw.polygon(surface, self.bordercolor, self.points, self.borderwidth)

        if self.fillcolor is not None:
            pygame.draw.polygon(surface, self.fillcolor, self.points)
