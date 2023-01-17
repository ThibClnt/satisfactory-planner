import os.path
from typing import Any
import json

import pygame

import settings
from ui import ImageButton, ShortcutButton
from buildings import BuildingInfo, Building


class Mode:
    IDLE = 0
    BUILD = 1

    names = {
        IDLE: "IDLE",
        BUILD: "BUILD"
    }


class Application:

    def __init__(self, size, flags):
        self.__size = size
        self.__running = True
        self.__screen = pygame.display.set_mode(size, flags)

        self.__mode = Mode.IDLE

        self.__controlbar = ControlBar(self, (size[0], settings.control_bar_size), "#404040")
        self.__viewport = ViewPort(self, (0, settings.control_bar_size), size)

        self.__building_name: str = "conveyor"

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

        self.__controlbar.process_event(events)
        self.__viewport.process_events(events)

    def __resize(self, size: list[int, int]):
        w = size[0]
        h = max(size[1] - settings.control_bar_size, 0)
        self.__size = size

        self.__controlbar.resize((w, settings.control_bar_size))
        self.__viewport.resize((w, h))
        print(f"Resized to {size[0]} x {size[1]}")

    def render(self):
        self.__screen.fill((0, 0, 0))
        self.__controlbar.render(self.__screen)
        self.__viewport.render(self.__screen)
        pygame.display.flip()

    def quit(self):
        self.__running = False

    @property
    def mode(self) -> int:
        return self.__mode

    @mode.setter
    def mode(self, value: int):
        if self.__mode != value:
            print(f"Mode set to {Mode.names[value]}")

        if value != Mode.BUILD:
            self.__controlbar.loose_shortcuts_focus()

        self.__mode = value

    @property
    def building_selected(self) -> str:
        return self.__building_name

    @building_selected.setter
    def building_selected(self, building_name: str):
        self.__building_name = building_name
        self.mode = Mode.BUILD


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
        self.__resolution = 16  # px / m
        self.__show_floor = True
        self.__show_grid = True

        self.__buildings: list[Building] = []
        self.__buildings_infos: dict[str, BuildingInfo] = dict()
        self.__scaled_building_images: dict[str, pygame.Surface] = dict()

        self.__load_buildings()

    def __load_buildings(self):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data/buildings.json"), 'r') as file:
            building_infos = json.load(file)["buildings"]
            self.__buildings_infos: dict[str, BuildingInfo] = {
                building["name"]: BuildingInfo(
                    building["name"],
                    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "../ressources/top/" + building["name"] + ".png"),
                    building["size"]
                )
                for building in building_infos
            }

        self.__scaled_building_images = {
            building.name: building.get_scaled_image(self.__resolution)
            for building in self.__buildings_infos.values()
        }
        self.resolution = self.__resolution     # Will render the images with the right scale

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

    @resolution.setter
    def resolution(self, r: int):
        self.__resolution = r

        self.__scaled_building_images = {
            building.name: building.get_scaled_image(self.__resolution)
            for building in self.__buildings_infos.values()
        }

    def process_events(self, events: list[pygame.event.Event]):
        keys_pressed = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.MOUSEMOTION:
                if event.buttons[1] or (event.buttons[0] and keys_pressed[pygame.K_LCTRL]):
                    self.__pan(event.rel)

            elif event.type == pygame.MOUSEWHEEL:
                self.__zoom(event.y, pygame.mouse.get_pos())

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:  # show/hide grid
                    self.__show_grid = not self.__show_grid

                elif event.key == pygame.K_f:  # show/hide floor
                    self.__show_floor = not self.__show_floor

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1\
                        and self.__application.mode == Mode.BUILD\
                        and not keys_pressed[pygame.K_LCTRL]\
                        and self.__contains_coord(event.pos):
                    self.__place_building()

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
            self.resolution *= 2
            xoff *= 2
            yoff *= 2
        elif amount < 0 and self.resolution > 4:
            self.resolution = self.resolution // 2
            xoff /= 2
            yoff /= 2

        self.__x_offset = int(xoff) + pos[0]
        self.__y_offset = int(yoff) + pos[1]

    def __place_building(self):
        aligned_pos = self.px_to_meter(*self.__get_mouse_coord())[:2]
        self.__buildings.append(Building(self.__buildings_infos[self.__application.building_selected], aligned_pos))
        print(self.__buildings)

    def render(self, surface: pygame.Surface):
        self.__surface.fill(settings.background_color)

        if self.__show_floor:
            self.__draw_floor()

        self.__draw_buildings()

        if self.__show_grid:
            self.__draw_grid()

        if self.__application.mode == Mode.BUILD:
            self.__draw_selected_building()

        surface.blit(self.__surface, self.__pos)

    def __draw_floor(self):
        floor: pygame.Surface = self.__scaled_building_images["floor"]
        w, h = floor.get_width(), floor.get_height()  # image
        width, height = self.__size[0], self.__size[1]  # viewport
        mod_xoffset, mod_yoffset = self.__x_offset % w - w, self.__y_offset % h - h

        for x in range(mod_xoffset, width + 1, w):
            for y in range(mod_yoffset, height + 1, h):
                self.__surface.blit(floor, (x, y))

    def __draw_buildings(self):
        for building in self.__buildings:
            pos = self.meter_to_px(*building.pos)[:2]
            self.__surface.blit(self.__scaled_building_images[building.name], pos)

    def __draw_grid(self):
        mod_xoffset, mod_yoffset = self.__x_offset % self.__resolution, self.__y_offset % self.__resolution
        width, height = self.__size[0], self.__size[1]

        for x in range(mod_xoffset, width + 1, self.__resolution):
            pygame.draw.line(self.__surface, settings.grid_color, (x, mod_yoffset - self.__resolution),
                             (x, mod_yoffset + height))

        for y in range(mod_yoffset, height + 1, self.__resolution):
            pygame.draw.line(self.__surface, settings.grid_color, (mod_xoffset - self.__resolution, y),
                             (mod_xoffset + width, y))

    def __draw_selected_building(self):
        aligned_pos = self.meter_to_px(*self.px_to_meter(*self.__get_mouse_coord()))[:2]
        self.__surface.blit(self.__scaled_building_images[self.__application.building_selected], aligned_pos)

    @staticmethod
    def __get_mouse_coord() -> tuple[int, int]:
        """
        :return: Mouse coordinate on the viewport's surface
        """
        x, y = pygame.mouse.get_pos()
        return x, y - settings.control_bar_size

    def __contains_coord(self, pos: list[int, int]):
        x, y = pos
        return 0 < x < self.__size[0] and 0 < y - settings.control_bar_size < self.__size[1]

    def meter_to_px(self, x: int, y: int, w: int = 0, h: int = 0) -> tuple[int, int, int, int]:
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

    def px_to_meter(self, x: int, y: int, w: int = 0, h: int = 0) -> tuple[int, int, int, int]:
        """
        :param x: x pos in px
        :param y: y pos in px
        :param w: width in px
        :param h: height in px
        :return: (x, y, w, h) in meters
        """
        nx = int((x - 1 - self.__x_offset) / self.__resolution)
        ny = int((y - 1 - self.__y_offset) / self.__resolution)

        nx -= 1 if nx < 0 else 0
        ny -= 1 if ny < 0 else 0

        return (nx,
                ny,
                int((w + 1) / self.__resolution),
                int((h + 1) / self.__resolution))


class ControlBar:

    def __init__(self, application: Application, size: tuple[int, int], color: Any):
        self.__application = application
        self.__color = color
        self.__w, self.__h = size
        self.__close_button = ImageButton((self.__w - 40, (settings.control_bar_size - 32) / 2), (32, 32),
                                          os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                       "../ressources/close.png"), self.__application.quit)

        # int(text): (index, text, name)
        self.__shortcuts_properties = {
            1: (0, "1", "conveyor"),
            2: (1, "2", "splitter"),
            3: (2, "3", "merger"),
            4: (3, "4", "smelter"),
            5: (4, "5", "foundry"),
            6: (5, "6", "refinery"),
            7: (6, "7", "constructor"),
            8: (7, "8", "assembler"),
            9: (8, "9", "manufacturer"),
            0: (9, "0", "container"),
        }

        self.__buttons = [
            ShortcutButton((4 + i * 52, 4), (48, 48),
                           os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "../ressources/shortcuts/" + n + ".png"),
                           t, lambda _: 0, "#202020", "#a0a0a0"
                           )
            for i, t, n in self.__shortcuts_properties.values()
        ]

    def render(self, surface: pygame.Surface):
        pygame.draw.rect(surface, self.__color, pygame.Rect(0, 0, self.__w, self.__h))
        for button in self.__buttons:
            button.render(surface)
        self.__close_button.render(surface)

    def process_event(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.__close_button.try_press(event)

                    for i, button in enumerate(self.__buttons):
                        if button.try_press(event, False):
                            self.__shortcut_used(i)

            elif event.type == pygame.KEYDOWN:
                if event.key - 48 in range(10):
                    self.__shortcut_used(self.__shortcuts_properties[event.key - 48][0])

    def __shortcut_used(self, building_index: int):
        # Update buttons
        button = self.__buttons[building_index]
        for b in self.__buttons:
            b.loose_focus()
        button.set_focus()

        # Change mode and current building
        self.__application.building_selected = \
            self.__shortcuts_properties[(building_index + 1) % len(self.__shortcuts_properties.keys())][2]

    def loose_shortcuts_focus(self):
        for b in self.__buttons:
            b.loose_focus()

    def resize(self, size: tuple[int, int]):
        self.__w, self.__h = size
        self.__close_button.move_to(self.__w - 40, (settings.control_bar_size - 32) / 2)
