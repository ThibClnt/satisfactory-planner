import pygame
from typing import Callable, Any


class Button:

    def __init__(self, pos: tuple[int, int], size: tuple[int, int], action: Callable,
                 color: Any = None, border_color: Any = None, border_width: int = 0, border_radius: int = -1):
        self.__x, self.__y = pos
        self.__w, self.__h = size
        self.__action = action
        self.__surface = pygame.Surface(size, pygame.SRCALPHA)

        self.__surface.fill(pygame.color.Color(0, 0, 0, 0))

        if color is not None:
            pygame.draw.rect(self.__surface, color, pygame.Rect(*pos, *size), border_radius=border_radius)

        if border_width != 0 and border_color is not None:
            pygame.draw.rect(self.__surface, border_color, pygame.Rect(*pos, *size), width=border_width, border_radius=border_radius)

    def render(self, surface: pygame.Surface):
        surface.blit(self.__surface, self.pos)

    def try_press(self, event: pygame.event.Event, trigger_action: bool = True) -> bool:
        if self.__x < event.pos[0] < self.__x + self.__w and self.__y < event.pos[1] < self.__y + self.__h:
            if trigger_action:
                self.__action()
            return True
        else:
            return False

    @property
    def pos(self) -> list[int, int]:
        return [self.__x, self.__y]

    @property
    def size(self) -> list[int, int]:
        return [self.__w, self.__h]

    @property
    def x(self) -> int:
        return self.__x

    @property
    def y(self) -> int:
        return self.__y

    @property
    def w(self) -> int:
        return self.__w

    @property
    def h(self) -> int:
        return self.h

    @property
    def action(self) -> Callable:
        return self.__action

    @action.setter
    def action(self, new_action: Callable):
        self.__action = new_action

    @property
    def surface(self) -> pygame.Surface:
        return self.__surface


class ImageButton(Button):

    def __init__(self, pos: tuple[int, int], size: tuple[int, int], image_path: Any, action: Callable):
        super().__init__(pos, size, action)
        image = pygame.transform.smoothscale(pygame.image.load(image_path), size).convert_alpha()
        self.surface.blit(image, (0, 0))
