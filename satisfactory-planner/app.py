import os.path
from typing import Any

import pygame

import settings
from ui import ImageButton


class Application:

    def __init__(self, size, flags):
        self.__size = size
        self.__running = True
        self.__screen = pygame.display.set_mode(size, flags)

        self.__controlbar = ControlBar(self, (size[0], 48), "#404040")
        self.__viewport = ViewPort(self, (0, 48), size)

    def loop(self):
        while self.__running:
            self.process_events()
            self.render()

    def process_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.__running = False

            if event.type == pygame.VIDEORESIZE:
                self.__resize(event.size)

        self.__controlbar.process_event(events)
        self.__viewport.process_events(events)

    def __resize(self, size: list[int, int]):

        w = size[0]
        h = max(size[0] - 48, 0)
        self.__size = size

        self.__controlbar.resize((w, 48))
        self.__viewport.resize((w, h))
        print(f"Resized to {size[0]} x {size[1]}")

    def render(self):
        self.__screen.fill((0, 0, 0))
        self.__controlbar.render(self.__screen)
        self.__viewport.render(self.__screen)
        pygame.display.flip()

    def quit(self):
        self.__running = False


class ViewPort:
    """
    View of the satisfactory planning. Can zoom and pan.
    The unit is the meter.
    At start, the rendering is set to 16px/m.
    """

    def __init__(self, application: Application, pos: tuple[int, int], size: tuple[int, int]):
        self.__application = application
        self.__pos = pos
        self.__size = size
        self.__surface = pygame.Surface(size)
        self.__x_offset, self.__y_offset = 0, 0
        self.__resolution = 16                      # px / m
        self.__show_grid = True

    @property
    def application(self):
        return self.__application

    @property
    def x_offset(self) -> int:
        return self.__x_offset

    @property
    def y_offset(self) -> int:
        return self.__y_offset

    @property
    def resolution(self) -> int:
        return self.__resolution

    def process_events(self, events: list[pygame.event.Event]):
        for event in events:
            if event.type == pygame.MOUSEMOTION:
                if event.buttons[1]:
                    self.__pan(event.rel)

            elif event.type == pygame.MOUSEWHEEL:
                self.__zoom(event.y, pygame.mouse.get_pos())

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:
                    self.__show_grid = not self.__show_grid

    def resize(self, size: tuple[int, int]):
        self.__size = size
        self.__surface = pygame.transform.scale(self.__surface, size)

    def __pan(self, rel: tuple[int, int]):
        self.__x_offset += rel[0]
        self.__y_offset += rel[1]

    def __zoom(self, amount: int, pos: tuple[int, int]):
        xoff = self.__x_offset - pos[0]
        yoff = self.__y_offset - pos[1]

        if amount > 0 and self.resolution < 64:
            self.__resolution *= 2
            xoff *= 2
            yoff *= 2
        elif amount < 0 and self.resolution > 4:
            self.__resolution = self.resolution // 2
            xoff /= 2
            yoff /= 2

        self.__x_offset = int(xoff) + pos[0]
        self.__y_offset = int(yoff) + pos[1]

    def render(self, surface: pygame.Surface):
        self.__surface.fill(settings.background_color)

        if self.__show_grid:
            self.__draw_grid()

        surface.blit(self.__surface, self.__pos)

    def __draw_grid(self):
        mod_xoffset, mod_yoffset = self.__x_offset % self.__resolution, self.__y_offset % self.__resolution
        width, height = self.__size[0], self.__size[1]
        for i in range(width // self.__resolution + 1):
            x = mod_xoffset + i * self.__resolution
            pygame.draw.line(self.__surface, settings.grid_color, (x, mod_yoffset - self.__resolution),
                             (x, mod_yoffset + height))

        for i in range(height // self.__resolution + 1):
            y = mod_yoffset + i * self.__resolution
            pygame.draw.line(self.__surface, settings.grid_color, (mod_xoffset - self.__resolution, y),
                             (mod_xoffset + width, y))

    def transform(self, x, y, w=0, h=0):
        """
        :param x: x pos in meter
        :param y: y pos in meter
        :param w: width in meter
        :param h: height in meter
        :return: (x, y, w, h) in px
        """
        return (1 + x * self.__resolution + self.__x_offset,
                1 + y * self.__resolution + self.__y_offset,
                w * self.__resolution - 1,
                h * self.__resolution - 1)


class ControlBar:

    def __init__(self, application: Application, size: tuple[int, int], color: Any):
        self.__application = application
        self.__color = color
        self.__w, self.__h = size
        self.__close_button = ImageButton((self.__w - 40, 8), (32, 32),
                                          os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                       "../ressources/close.png"), self.__application.quit)

    def render(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.__color, pygame.Rect(0, 0, self.__w, self.__h))
        self.__close_button.render(surface)

    def process_event(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.__close_button.try_press(event)

    def resize(self, size: tuple[int, int]):
        self.__w, self.__h = size
        self.__close_button.move_to(self.__w - 40, 8)
