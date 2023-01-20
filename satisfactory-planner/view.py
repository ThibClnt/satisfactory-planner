from __future__ import annotations

import math
import pygame

import settings
from buildings import Building, BuildingInformations
from common import trim, AppState


class ViewPort:
    """
    View of the satisfactory planning. Can zoom and pan.
    The unit is the meter.
    At start, the rendering is set to 16px/m.
    """

    def __init__(self, app_state: AppState, pos: tuple[int, int], size: tuple[int, int]):
        self.__app_state = app_state
        self.__pos = pos
        self.__size = size
        self.__surface = pygame.Surface(size)
        self.__x_offset, self.__y_offset = 0, 0
        self.__resolution = settings.default_resolution  # px / m
        self.__show_floor = True
        self.__show_grid = False

        # Load buildings data
        self.__buildings: list[Building] = []
        self.__buildings_infos = BuildingInformations("data/buildings.json")
        self.__buildings_infos.scale_building_images(self.__resolution)

        # Building selected in build mode
        self.__current_building: Building = Building(self.__buildings_infos.get_building_type("conveyor"), (0, 0))

        self.__conveyor_types = (
            "conveyor", "conveyor-reduced", "conveyor-l-shaped", "conveyor-wave-left", "conveyor-wave-right"
        )
        self.__conveyor_index = 0

    def process_events(self, events: list[pygame.event.Event]):
        def is_building_conveyor():
            return "conveyor" in self.__current_building.name and self.__app_state.get() == AppState.BUILD

        keys_pressed = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.MOUSEMOTION:
                if event.buttons[1] or (event.buttons[0] and keys_pressed[pygame.K_LCTRL]):
                    self.__pan(event.rel)

            elif event.type == pygame.MOUSEWHEEL:
                self.__zoom(event.y, pygame.mouse.get_pos())

            elif event.type == pygame.MOUSEWHEEL and self.__app_state.get() == AppState.BUILD:
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

                elif event.key == pygame.K_r and self.__app_state.get() == AppState.BUILD:
                    self.__rotate_selected(-1 if keys_pressed[pygame.K_LSHIFT] else 1)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if (
                        event.button == 1
                        and self.__app_state.get() == AppState.BUILD
                        and not keys_pressed[pygame.K_LCTRL]
                        and self.contains_coord(event.pos)
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
        mouse_pos = self.get_view_coord(pygame.mouse.get_pos())
        grid_pos = self.px_to_meter(*mouse_pos)[:2]

        building = Building(
            self.__buildings_infos.get_building_type(self.selected_building_name),
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

        if self.__app_state.get() == AppState.BUILD:
            self.__draw_selected_building()

        surface.blit(self.__surface, self.__pos)

    def __draw_floor(self):
        floor: pygame.Surface = self.__buildings_infos.get_image_from_name("floor", 0)

        floor_width, floor_height = floor.get_width(), floor.get_height()  # floor image
        view_width, view_height = self.__size[0], self.__size[1]  # viewport

        offset_x = self.__x_offset % floor_width - floor_width
        offset_y = self.__y_offset % floor_height - floor_height

        for x in range(offset_x, view_width + 1, floor_width):
            for y in range(offset_y, view_height + 1, floor_height):
                self.__surface.blit(floor, (x, y))

    def __draw_buildings(self):
        for building in self.__buildings:
            building_image = self.__buildings_infos.get_image(building)

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
        building_image = self.__buildings_infos.get_image(self.__current_building)
        grid_pos = self.px_to_meter(*self.get_view_coord(pygame.mouse.get_pos()))

        x_px, y_px = self.meter_to_px(*grid_pos)[:2]
        x_px -= building_image.get_width() / 2
        y_px -= building_image.get_height() / 2

        self.__surface.blit(building_image, (x_px, y_px))

    def get_view_coord(self, pos: tuple[int, int]) -> tuple[int, int]:
        """
        :return: Mouse position in the viewport, in px
        """
        x = trim(pos[0] - self.__pos[0], 0, self.__size[0])
        y = trim(pos[1] - self.__pos[1], 0, self.__size[1])

        return x, y

    def contains_coord(self, pos: tuple[int, int]):
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
    def resolution(self) -> int:
        return self.__resolution

    @resolution.setter
    def resolution(self, r: int):
        # Ensure r is a power of two
        r = 2 ** (int(math.log2(r)))

        self.__resolution = r
        self.__buildings_infos.scale_building_images(r)

    @property
    def selected_building_name(self) -> str:
        return self.__current_building.name

    @selected_building_name.setter
    def selected_building_name(self, building_name: str):
        angle = self.__current_building.angle
        self.__current_building = Building(self.__buildings_infos.get_building_type(building_name), (0, 0), angle)