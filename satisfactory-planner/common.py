import os.path
from os import PathLike
import math
from typing import Callable
import settings


class Camera:

    def __init__(self, on_resolution_change: Callable[[int], None]):
        self.__x_offset, self.__y_offset = 0, 0
        self.__resolution = settings.default_resolution  # px / m
        self.__on_resolution_change = on_resolution_change

    def pan(self, rel: tuple[int, int]):
        self.__x_offset += rel[0]
        self.__y_offset += rel[1]

    def zoom(self, amount: int, pos: tuple[int, int]):
        xoff = self.__x_offset - pos[0]
        yoff = self.__y_offset - pos[1]

        if amount > 0 and self.resolution < 64:
            self.resolution *= 2
            xoff *= 2
            yoff *= 2
        elif amount < 0 and self.resolution > 4:
            self.resolution = self.resolution // 2
            xoff /= 2
            yoff /= 2

        self.__x_offset = int(xoff) + pos[0]
        self.__y_offset = int(yoff) + pos[1]

    def meter_to_px(self, x: int, y: int, w: int = 0, h: int = 0) -> tuple[int, int, int, int]:
        return (1 + x * self.__resolution + self.__x_offset,
                1 + y * self.__resolution + self.__y_offset,
                w * self.__resolution - 1,
                h * self.__resolution - 1)

    def px_to_meter(self, x: int, y: int, w: int = 0, h: int = 0) -> tuple[int, int, int, int]:
        nx = int((x - 1 - self.__x_offset) / self.__resolution)
        ny = int((y - 1 - self.__y_offset) / self.__resolution)

        nx -= 1 if nx < 0 else 0
        ny -= 1 if ny < 0 else 0

        return (nx,
                ny,
                int((w + 1) / self.__resolution),
                int((h + 1) / self.__resolution))

    @property
    def x(self) -> int:
        return self.__x_offset

    @x.setter
    def x(self, x: int):
        self.__x_offset = x

    @property
    def y(self) -> int:
        return self.__y_offset

    @y.setter
    def y(self, y: int):
        self.__y_offset = y

    @property
    def resolution(self) -> int:
        return self.__resolution

    @resolution.setter
    def resolution(self, r: int):
        # Ensure r is a power of two
        r = 2 ** (int(math.log2(r)))

        self.__resolution = r
        self.__on_resolution_change(r)


class AppState:
    IDLE = 0
    BUILD = 1

    def __init__(self, state: int = 0):
        self.__state = state

    def set(self, state: int):
        self.__state = state

    def get(self) -> int:
        return self.__state


def get_path(relative_path: str | PathLike[bytes]) -> str:
    """
    :param relative_path: Relative path from root directory to a file
    :type relative_path str | PathLike[bytes]
    :return: Absolute path to the file
    :rtype: str
    """
    dir_path = os.path.dirname(os.path.abspath(__file__))
    root_path = os.path.join(dir_path, "../")
    return os.path.join(root_path, relative_path)


def trim(value, start, end):
    return min(max(value, start), end)
