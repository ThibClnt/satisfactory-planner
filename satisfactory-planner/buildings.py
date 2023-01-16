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
