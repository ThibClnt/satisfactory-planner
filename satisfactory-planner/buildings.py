from __future__ import annotations

import json
from os import PathLike
import pygame
from typing import Any

from common import get_path


class BuildingType:

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
    def width(self) -> int:
        return self.__w

    @property
    def height(self) -> int:
        return self.__h

    @property
    def size(self) -> tuple[int, int]:
        return self.__w, self.__h

    @property
    def image(self) -> pygame.Surface:
        return self.__image


class Building:

    def __init__(self, info: BuildingType, pos: tuple[int, int], angle: int = 0):
        self.__info = info
        self.__x, self.__y = pos
        self.__angle = angle

    def get_scaled_image(self, resolution: int) -> pygame.Surface:
        return pygame.transform.rotate(self.__info.get_scaled_image(resolution), self.__angle).convert_alpha()

    def rotate(self, angle: int):
        self.__angle += angle

    def copy(self) -> Building:
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
    def width(self) -> int:
        return self.__info.width

    @property
    def height(self) -> int:
        return self.__info.height

    @property
    def size(self) -> tuple[int, int]:
        return self.__info.width, self.__info.height

    @property
    def angle(self) -> int:
        return int(self.__angle)

    @property
    def image(self) -> pygame.Surface:
        return self.__info.image

    def __str__(self):
        return f"{'{'}name: '{self.name}', pos: {self.pos}, angle: {self.angle}{'}'}"


class BuildingInformations:

    def __init__(self, filepath:  str | PathLike[bytes]):
        self.__building_types: dict[str, BuildingType] = dict()
        self.__building_images: dict[str, list[pygame.Surface]] = dict()

        with open(get_path(filepath), 'r') as file:
            building_types = json.load(file)["buildings"]
            for building in building_types:
                self.__building_types[building["name"]] = BuildingType(
                    building["name"],
                    get_path("ressources/top/" + building["name"] + ".png"),
                    building["size"]
                )

    def scale_building_images(self, resolution: int):
        for building in self.__building_types.values():
            scaled_image = building.get_scaled_image(resolution)
            self.__building_images[building.name] = [
                pygame.transform.rotate(scaled_image, angle)
                for angle in (0, 90, 180, 270)
            ]

    def get_image(self, building: Building) -> pygame.Surface:
        index = (building.angle % 360) // 90
        return self.__building_images[building.name][index]

    def get_image_from_name(self, typename: str, angle: int) -> pygame.Surface:
        index = (angle % 360) // 90
        return self.__building_images[typename][index]

    def get_building_type(self, typename: str) -> BuildingType:
        return self.__building_types[typename]


class BuildingStorage:

    def __init__(self):
        self.__buildings: set[Building] = set()

    def add(self, building: Building):
        if self.get(building.pos) is not None:
            return
        self.__buildings.add(building)

    def remove(self, building: Building):
        self.__buildings.remove(building)

    def get(self, pos: tuple[int, int]) -> Building:
        for building in self.__buildings:
            if building.pos == pos:
                return building

    def __iter__(self):
        return self.__buildings.__iter__()
