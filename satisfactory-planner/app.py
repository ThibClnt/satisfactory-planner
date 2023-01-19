from typing import Any

import pygame

import settings
from common import Mode, get_path
from ui import ImageButton, ShortcutButton
from view import ViewPort


class Application:

    def __init__(self, size, flags):
        self.__size = size
        self.__running = True
        self.__screen = pygame.display.set_mode(size, flags)

        self.__mode = Mode.IDLE

        self.__controlbar = ControlBar(self, (size[0], settings.control_bar_size), settings.control_bar_color)
        self.__hotbar = HotBar(self, HotBar.calculate_center_pos(size[0], settings.control_bar_size))
        self.__viewport = ViewPort(self, (0, settings.control_bar_size), size)

    def loop(self):
        while self.__running:
            self.process_events()
            self.render()

    def process_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.__running = False

            elif event.type == pygame.VIDEORESIZE:
                self.__resize(event.size)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.__mode == Mode.BUILD:
                        self.mode = Mode.IDLE

        self.__controlbar.process_events(events)
        self.__hotbar.process_events(events)
        self.__viewport.process_events(events)

    def __resize(self, size: list[int, int]):
        w = size[0]
        h = max(size[1] - settings.control_bar_size, 0)
        self.__size = size

        self.__controlbar.resize((w, settings.control_bar_size))
        self.__hotbar.resize((w, settings.control_bar_size))
        self.__viewport.resize((w, h))

    def render(self):
        self.__screen.fill((0, 0, 0))
        self.__controlbar.render(self.__screen)
        self.__hotbar.render(self.__screen)
        self.__viewport.render(self.__screen)
        pygame.display.flip()

    def quit(self):
        self.__running = False

    @property
    def mode(self) -> int:
        return self.__mode

    @mode.setter
    def mode(self, value: int):
        if value != Mode.BUILD:
            self.__hotbar.loose_focus()

        self.__mode = value

    @property
    def viewport(self):
        return self.__viewport


class ControlBar:

    def __init__(self, application: Application, size: tuple[int, int], color: Any):
        self.__application = application
        self.__color = color
        self.__w, self.__h = size

        close_button_pos = (self.__w - 40, (settings.control_bar_size - settings.close_button_size) / 2)
        close_button_size = (settings.close_button_size, settings.close_button_size)
        self.__close_button = ImageButton(close_button_pos, close_button_size, get_path("ressources/close.png"),
                                          self.__application.quit)

    def render(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.__color, pygame.Rect(0, 0, self.__w, self.__h))
        self.__close_button.render(surface)

    def process_events(self, events: list[pygame.event.Event]):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.__close_button.try_press(event)

    def resize(self, size: tuple[int, int]):
        self.__w, self.__h = size
        self.__close_button.pos = (self.__w - 40, (settings.control_bar_size - 32) / 2)


class HotBar:
    shortcuts_properties = {1: (0, "1", "conveyor"),
                            2: (1, "2", "splitter"),
                            3: (2, "3", "merger"),
                            4: (3, "4", "smelter"),
                            5: (4, "5", "foundry"),
                            6: (5, "6", "refinery"),
                            7: (6, "7", "constructor"),
                            8: (7, "8", "assembler"),
                            9: (8, "9", "manufacturer"),
                            0: (9, "0", "container")}

    @staticmethod
    def calculate_center_pos(width: int, height: int) -> tuple[int, int]:
        button_padding = settings.shortcut_button_padding
        button_size = settings.shortcut_button_size

        x = (width + button_padding - (button_size + button_padding) * len(HotBar.shortcuts_properties)) / 2
        y = (height - button_size) / 2

        return x, y

    def __init__(self, application: Application, pos: tuple[int, int]):
        self.__application = application
        self.__x, self.__y = pos

        self.__buttons: list[ShortcutButton] = []
        self.__create_shortcuts_buttons()

    def __create_shortcuts_buttons(self):

        for i, text, name in self.shortcuts_properties.values():
            pos = (self.__x + i * (settings.shortcut_button_size + settings.shortcut_button_padding),
                   settings.shortcut_button_padding)
            size = (settings.shortcut_button_size, settings.shortcut_button_size)

            self.__buttons.append(
                ShortcutButton(
                    pos, size, get_path("ressources/shortcuts/" + name + ".png"), text,
                    color=settings.shortcut_button_background_color,
                    border_color=settings.shortcut_button_focus_color
                )
            )

    def render(self, surface: pygame.Surface):
        for button in self.__buttons:
            button.render(surface)

    def process_events(self, events: list[pygame.event.Event]):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for i, button in enumerate(self.__buttons):
                        if button.try_press(event, False):
                            self.use_shortcut(i)

            elif event.type == pygame.KEYDOWN:
                if event.key - 48 in range(10):
                    self.use_shortcut(self.shortcuts_properties[event.key - 48][0])

    def use_shortcut(self, button_index: int):
        # Update buttons
        button = self.__buttons[button_index]
        for b in self.__buttons:
            b.loose_focus()
        button.set_focus()

        # Change mode and current building
        button_index = (button_index + 1) % len(self.shortcuts_properties.keys())
        self.__application.viewport.selected_building_name = self.shortcuts_properties[button_index][2]
        self.__application.mode = Mode.BUILD

    def loose_focus(self):
        for b in self.__buttons:
            b.loose_focus()

    def resize(self, size: tuple[int, int]):
        self.__move(self.calculate_center_pos(*size))

    def __move(self, pos: tuple[int, int]):
        self.__x, self.__y = pos

        for i, button in enumerate(self.__buttons):
            button.pos = (self.__x + i * (settings.shortcut_button_size + settings.shortcut_button_padding),
                          settings.shortcut_button_padding)
