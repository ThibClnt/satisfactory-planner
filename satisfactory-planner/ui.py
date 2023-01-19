import pygame
from typing import Callable, Any

import settings
from common import get_path


class Button:

    def __init__(self, pos: tuple[int, int],
                 size: tuple[int, int],
                 action: Callable,
                 color: Any = None,
                 border_color: Any = None,
                 border_width: int = 0,
                 border_radius: int = -1,
                 *args):

        self.__x, self.__y = pos
        self.__w, self.__h = size
        self.__action = action
        self.__surface = pygame.Surface(size, pygame.SRCALPHA)
        self.color = color
        self.border_color = border_color
        self.border_width = border_width
        self.border_radius = border_radius
        self.__args = args

        Button.draw(self)

    def draw(self):
        self.__surface.fill(pygame.color.Color(0, 0, 0, 0))

        # Draw background
        if self.color is not None:
            pygame.draw.rect(self.__surface, self.color, pygame.Rect(0, 0, *self.size), border_radius=self.border_radius)

        # Draw outline
        if self.border_width != 0 and self.border_color is not None:
            pygame.draw.rect(self.__surface, self.border_color, pygame.Rect(0, 0, *self.size), width=self.border_width, border_radius=self.border_radius)

    def render(self, surface: pygame.Surface):
        surface.blit(self.__surface, self.pos)

    def try_press(self, event: pygame.event.Event, trigger_action: bool = True) -> bool:
        if self.__x < event.pos[0] < self.__x + self.__w and self.__y < event.pos[1] < self.__y + self.__h:
            if trigger_action:
                self.trigger()
            return True
        else:
            return False

    def trigger(self):
        if self.__action is not None:
            self.__action(*self.__args)

    @property
    def pos(self) -> list[int, int]:
        return [self.__x, self.__y]

    @pos.setter
    def pos(self, new_pos: list[int, int]):
        self.__x, self.__y = new_pos

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
    def width(self) -> int:
        return self.__w

    @property
    def height(self) -> int:
        return self.__h

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

    def __init__(self, pos: tuple[int, int],
                 size: tuple[int, int],
                 image_path: Any,
                 action: Callable,
                 color: Any = None,
                 border_color: Any = None,
                 border_width: int = 0,
                 border_radius: int = -1,
                 *args):

        super().__init__(pos, size, action, color, border_color, border_width, border_radius, *args)
        self.__image_path = image_path
        self.draw()

    def draw(self):
        super().draw()
        self.surface.blit(pygame.transform.smoothscale(pygame.image.load(self.__image_path), self.size).convert_alpha(), (0, 0))


class ShortcutButton(Button):

    if not pygame.get_init():
        pygame.init()

    if not pygame.font.get_init():
        pygame.font.get_init()

    font = pygame.font.Font(get_path("ressources/fonts/Satisfontory_v1.5.ttf"), settings.shortcut_button_font_size)

    def __init__(self, pos: tuple[int, int],
                 size: tuple[int, int],
                 image_path: Any,
                 text: str,
                 action: Callable = lambda _: 0,
                 color: Any = None,
                 border_color: Any = None,
                 border_width: int = 0,
                 border_radius: int = -1,
                 *args):

        super().__init__(pos, size, action, color, border_color, border_width, border_radius, *args)
        self.__image_path = image_path
        self.__text = text
        self.draw()

    def draw(self):
        super().draw()

        margin = settings.shortcut_button_margin
        image_width = self.width - 2 * margin
        image_height = self.height - 2 * margin

        image = pygame.image.load(self.__image_path)
        scaled_image = pygame.transform.smoothscale(image, (image_width, image_height)).convert_alpha()

        self.surface.blit(scaled_image, (margin, margin))

        font_size = settings.shortcut_button_font_size
        font_color = settings.shortcut_button_font_color
        font_x = self.width - font_size
        font_y = self.height - font_size - margin

        self.surface.blit(self.font.render(self.__text, True, font_color), (font_x, font_y))

    def set_focus(self):
        self.border_width = 2
        self.draw()

    def loose_focus(self):
        self.border_width = 0
        self.draw()
