import json
from typing import Any

import pygame

import settings
from buildings import BuildingInfo, Building
from common import get_path
from ui import ImageButton, ShortcutButton


class Mode:
    IDLE = 0
    BUILD = 1


class Application:

    def __init__(self, size, flags):
        self.__size = size
        self.__running = True
        self.__screen = pygame.display.set_mode(size, flags)

        self.__mode = Mode.IDLE

        self.__controlbar = ControlBar(self, (size[0], settings.control_bar_size), settings.control_bar_color)
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

        self.__controlbar.process_event(events)
        self.__viewport.process_events(events)

    def __resize(self, size: list[int, int]):
        w = size[0]
        h = max(size[1] - settings.control_bar_size, 0)
        self.__size = size

        self.__controlbar.resize((w, settings.control_bar_size))
        self.__viewport.resize((w, h))

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
        if value != Mode.BUILD:
            self.__controlbar.loose_shortcuts_focus()

        self.__mode = value

    @property
    def viewport(self):
        return self.__viewport


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
        self.__resolution = settings.default_resolution  # px / m
        self.__show_floor = True
        self.__show_grid = False

        # Load buildings data
        self.__buildings: list[Building] = []
        self.__buildings_infos: dict[str, BuildingInfo] = dict()
        self.__building_images: dict[str, list[pygame.Surface]] = dict()
        self.__load_buildings()

        # Building selected in build mode
        self.__current_building: Building = Building(self.__buildings_infos["conveyor"], (0, 0))

        self.__conveyor_types = (
            "conveyor", "conveyor-reduced", "conveyor-l-shaped", "conveyor-wave-left", "conveyor-wave-right"
        )
        self.__conveyor_index = 0

    def __load_buildings(self):
        with open(get_path("data/buildings.json"), 'r') as file:
            building_infos = json.load(file)["buildings"]
            for building in building_infos:
                self.__buildings_infos[building["name"]] = BuildingInfo(
                    building["name"],
                    get_path("ressources/top/" + building["name"] + ".png"),
                    building["size"]
                )

        self.__rescale_building_images()

    def __rescale_building_images(self):
        for building in self.__buildings_infos.values():
            scaled_image = building.get_scaled_image(self.__resolution)
            self.__building_images[building.name] = \
                [
                    pygame.transform.rotate(scaled_image, angle)
                    for angle in (0, 90, 180, 270)
                ]

    def process_events(self, events: list[pygame.event.Event]):
        def is_building_conveyor():
            return "conveyor" in self.__current_building.name and self.__application.mode == Mode.BUILD

        keys_pressed = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.MOUSEMOTION:
                if event.buttons[1] or (event.buttons[0] and keys_pressed[pygame.K_LCTRL]):
                    self.__pan(event.rel)

            elif event.type == pygame.MOUSEWHEEL:
                self.__zoom(event.y, pygame.mouse.get_pos())

            elif event.type == pygame.MOUSEWHEEL and self.__application.mode == Mode.BUILD:
                self.__rotate_selected(event.y)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:  # show/hide grid
                    self.__show_grid = not self.__show_grid

                elif event.key == pygame.K_f:  # show/hide floor
                    self.__show_floor = not self.__show_floor

                elif (event.key == pygame.K_q or event.key == pygame.K_LEFT) and is_building_conveyor():
                    self.__next_conveyor_type(-1)

                elif (event.key == pygame.K_d or event.key == pygame.K_RIGHT) and is_building_conveyor():
                    self.__next_conveyor_type(1)

                elif event.key == pygame.K_r and self.__application.mode == Mode.BUILD:
                    self.__rotate_selected(-1 if keys_pressed[pygame.K_LSHIFT] else 1)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if (
                        event.button == 1
                        and self.__application.mode == Mode.BUILD
                        and not keys_pressed[pygame.K_LCTRL]
                        and self.__contains_coord(event.pos)
                ):
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

    def __rotate_selected(self, direction: int):
        self.__current_building.rotate(-90 * direction)

    def __place_building(self):
        mouse_pos = self.__get_mouse_coord()
        grid_pos = self.px_to_meter(*mouse_pos)[:2]

        building = Building(
            self.__buildings_infos[self.selected_building_name],
            grid_pos,
            self.__current_building.angle
        )

        self.__buildings.append(building)

    def __next_conveyor_type(self, direction: int):
        self.__conveyor_index = (self.__conveyor_index + direction) % len(self.__conveyor_types)
        self.selected_building_name = self.__conveyor_types[self.__conveyor_index]

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
        floor: pygame.Surface = self.__building_images["floor"][0]

        floor_width, floor_height = floor.get_width(), floor.get_height()  # floor image
        view_width, view_height = self.__size[0], self.__size[1]  # viewport

        offset_x = self.__x_offset % floor_width - floor_width
        offset_y = self.__y_offset % floor_height - floor_height

        for x in range(offset_x, view_width + 1, floor_width):
            for y in range(offset_y, view_height + 1, floor_height):
                self.__surface.blit(floor, (x, y))

    def __draw_buildings(self):
        for building in self.__buildings:
            building_image = self.__building_images[building.name][(building.angle % 360) // 90]

            x_px, y_px = self.meter_to_px(*building.pos)[:2]
            x_px -= building_image.get_width() / 2
            y_px -= building_image.get_height() / 2

            self.__surface.blit(building_image, (x_px, y_px))

    def __draw_grid(self):
        offset_x = self.__x_offset % self.__resolution
        offset_y = self.__y_offset % self.__resolution
        view_width, view_height = self.__size[0], self.__size[1]

        for x in range(offset_x, view_width + 1, self.__resolution):
            from_pos = (x, offset_y - self.__resolution)
            to_pos = (x, offset_y + view_height)
            pygame.draw.line(self.__surface, settings.grid_color, from_pos, to_pos)

        for y in range(offset_y, view_height + 1, self.__resolution):
            from_pos = (offset_x - self.__resolution, y)
            to_pos = (offset_x + view_width, y)
            pygame.draw.line(self.__surface, settings.grid_color, from_pos, to_pos)

    def __draw_selected_building(self):
        building_image = self.__building_images[self.__current_building.name][
            (self.__current_building.angle % 360) // 90]
        grid_pos = self.px_to_meter(*self.__get_mouse_coord())

        x_px, y_px = self.meter_to_px(*grid_pos)[:2]
        x_px -= building_image.get_width() / 2
        y_px -= building_image.get_height() / 2

        self.__surface.blit(building_image, (x_px, y_px))

    @staticmethod
    def __get_mouse_coord() -> tuple[int, int]:
        """
        :return: Mouse position in the viewport, in px
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
        self.__rescale_building_images()

    @property
    def selected_building_name(self) -> str:
        return self.__current_building.name

    @selected_building_name.setter
    def selected_building_name(self, building_name: str):
        angle = self.__current_building.angle
        self.__current_building = Building(self.__buildings_infos[building_name], (0, 0), angle)


class ControlBar:

    def __init__(self, application: Application, size: tuple[int, int], color: Any):
        self.__application = application
        self.__color = color
        self.__w, self.__h = size

        close_button_pos = (self.__w - 40, (settings.control_bar_size - settings.close_button_size) / 2)
        close_button_size = (settings.close_button_size, settings.close_button_size)
        self.__close_button = ImageButton(close_button_pos, close_button_size, get_path("ressources/close.png"),
                                          self.__application.quit)

        self.__shortcuts_properties: dict[int, tuple[int, str, str]] = dict()
        self.__buttons: list[ShortcutButton] = []
        self.__create_shortcuts_buttons()

    def __create_shortcuts_buttons(self):
        self.__shortcuts_properties = {1: (0, "1", "conveyor"),
                                       2: (1, "2", "splitter"),
                                       3: (2, "3", "merger"),
                                       4: (3, "4", "smelter"),
                                       5: (4, "5", "foundry"),
                                       6: (5, "6", "refinery"),
                                       7: (6, "7", "constructor"),
                                       8: (7, "8", "assembler"),
                                       9: (8, "9", "manufacturer"),
                                       0: (9, "0", "container")}

        offset_x = (
                    self.__w + settings.shortcut_button_padding
                    - (settings.shortcut_button_size + settings.shortcut_button_padding) * len(self.__shortcuts_properties)
                   ) / 2

        for i, text, name in self.__shortcuts_properties.values():
            pos = (offset_x + i * (settings.shortcut_button_size + settings.shortcut_button_padding),
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
        shortcut_index = (building_index + 1) % len(self.__shortcuts_properties.keys())
        self.__application.viewport.selected_building_name = self.__shortcuts_properties[shortcut_index][2]
        self.__application.mode = Mode.BUILD

    def loose_shortcuts_focus(self):
        for b in self.__buttons:
            b.loose_focus()

    def resize(self, size: tuple[int, int]):
        self.__w, self.__h = size
        self.__close_button.pos = (self.__w - 40, (settings.control_bar_size - 32) / 2)
        self.__update_shortcuts_pos()

    def __update_shortcuts_pos(self):
        offset_x = (
                    self.__w + settings.shortcut_button_padding
                    - (settings.shortcut_button_size + settings.shortcut_button_padding) * len(self.__shortcuts_properties)
                   ) / 2

        for i, button in enumerate(self.__buttons):
            button.pos = (offset_x + i * (settings.shortcut_button_size + settings.shortcut_button_padding),
                          settings.shortcut_button_padding)
