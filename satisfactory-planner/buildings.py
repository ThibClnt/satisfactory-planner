from __future__ import annotations
import pygame
from typing import Any


class BuildingInfo:

    def __init__(self, name: str, image_path: Any, size: list[int, int]):
        """
        :param name: Name of the building
        :param image_path: Path of the image for displaying the building in the editor
        :param size: [width, height] in meter of the building
        """
        self.__name = name
        self.__image_path = image_path
        self.__w, self.__h = size

        # image and size in px
        self.__image = pygame.image.load(image_path).convert_alpha()
        self.__width, self.__height = self.__image.get_size()

        self.__native_resolution = self.__width // self.__w

    def get_scaled_image(self, resolution: int) -> pygame.Surface:
        scale_factor = resolution / self.__native_resolution
        return pygame.transform.smoothscale(self.__image, (self.__width * scale_factor, self.__height * scale_factor)).convert_alpha()

    @property
    def name(self) -> str:
        return self.__name

    @property
    def w(self) -> int:
        return self.__w

    @property
    def h(self) -> int:
        return self.__h

    @property
    def size(self) -> tuple[int, int]:
        return self.__w, self.__h

    @property
    def image(self) -> pygame.Surface:
        return self.__image


class Building:

    def __init__(self, info: BuildingInfo, pos: tuple[int, int], angle: int = 0):
        self.__info = info
        self.__x, self.__y = pos
        self.__angle = angle

    def get_scaled_image(self, resolution: int) -> pygame.Surface:
        return pygame.transform.rotate(self.__info.get_scaled_image(resolution), self.__angle).convert_alpha()

    def rotate(self, angle: int):
        self.__angle += angle

    def copy(self) -> Building:
        print(self.pos)
        return Building(self.__info, self.pos, self.angle)

    @property
    def name(self):
        return self.__info.name

    @property
    def pos(self) -> tuple[int, int]:
        return self.__x, self.__y

    @pos.setter
    def pos(self, new_pos: tuple[int, int]):
        self.__x, self.__y = new_pos

    @property
    def x(self) -> int:
        return self.__x

    @property
    def y(self) -> int:
        return self.__y

    @property
    def w(self) -> int:
        return self.__info.w

    @property
    def h(self) -> int:
        return self.__info.h

    @property
    def size(self) -> tuple[int, int]:
        return self.__info.w, self.__info.h

    @property
    def angle(self) -> int:
        return int(self.__angle)

    @property
    def image(self) -> pygame.Surface:
        return self.__info.image

    def __str__(self):
        return f"{'{'}name: '{self.name}', pos: {self.pos}, angle: {self.angle}{'}'}"
