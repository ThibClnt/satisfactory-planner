from __future__ import annotations

import pygame
from typing import Callable

import settings
from buildings import Building, BuildingInformations, BuildingStorage
from common import trim, AppState, Camera


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
        self.__show_floor = True
        self.__show_grid = False

        self.__buildings_infos = BuildingInformations("data/buildings.json")
        self.__camera = Camera(self.__buildings_infos.scale_building_images)
        self.__buildings_infos.scale_building_images(self.__camera.resolution)
        self.__buildings: BuildingStorage = BuildingStorage(self.__buildings_infos, self.__camera)

        # Building selected in build mode
        self.__build_overlay: BuildOverlay = BuildOverlay(self.__buildings_infos, "conveyor", self.__surface,
                                                          self.__camera.meter_to_px)

    def process_events(self, events: list[pygame.event.Event]):
        def is_building_conveyor():
            return "conveyor" in self.__build_overlay.building_type and self.__app_state.get() == AppState.BUILD

        keys_pressed = pygame.key.get_pressed()

        for event in events:
            if event.type == pygame.MOUSEMOTION:
                if event.buttons[1] or (event.buttons[0] and keys_pressed[pygame.K_LCTRL]):
                    self.__camera.pan(event.rel)

            elif event.type == pygame.MOUSEWHEEL:
                self.__camera.zoom(event.y, pygame.mouse.get_pos())

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_g:  # show/hide grid
                    self.__show_grid = not self.__show_grid

                elif event.key == pygame.K_f:  # show/hide floor
                    self.__show_floor = not self.__show_floor

                elif (event.key == pygame.K_q or event.key == pygame.K_LEFT) and is_building_conveyor():
                    self.__build_overlay.next_conveyor_type(-1)

                elif (event.key == pygame.K_d or event.key == pygame.K_RIGHT) and is_building_conveyor():
                    self.__build_overlay.next_conveyor_type(1)

                elif event.key == pygame.K_r and self.__app_state.get() == AppState.BUILD:
                    self.__build_overlay.rotate(-1 if keys_pressed[pygame.K_LSHIFT] else 1)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if (
                        event.button == 1
                        and self.__app_state.get() == AppState.BUILD
                        and not keys_pressed[pygame.K_LCTRL]
                        and self.contains_coord(event.pos)
                ):
                    self.__buildings.add(self.__build_overlay.create())

    def resize(self, size: tuple[int, int]):
        self.__size = size
        self.__surface = pygame.transform.scale(self.__surface, size)

    def update(self):
        grid_pos = self.__camera.px_to_meter(*self.get_view_coord(pygame.mouse.get_pos()))[:2]
        self.__build_overlay.update_pos(grid_pos)

    def render(self, surface: pygame.Surface):
        self.__surface.fill(settings.background_color)

        if self.__show_floor:
            self.__draw_floor()

        self.__buildings.draw(self.__surface)

        if self.__show_grid:
            self.__draw_grid()

        if self.__app_state.get() == AppState.BUILD:
            self.__build_overlay.draw(self.__surface)

        surface.blit(self.__surface, self.__pos)

    def __draw_floor(self):
        floor: pygame.Surface = self.__buildings_infos.get_image_from_name("floor", 0)

        floor_width, floor_height = floor.get_width(), floor.get_height()  # floor image
        view_width, view_height = self.__size[0], self.__size[1]  # viewport

        offset_x = self.__camera.x % floor_width - floor_width
        offset_y = self.__camera.y % floor_height - floor_height

        for x in range(offset_x, view_width + 1, floor_width):
            for y in range(offset_y, view_height + 1, floor_height):
                self.__surface.blit(floor, (x, y))

    def __draw_grid(self):
        offset_x = self.__camera.x % self.__camera.resolution
        offset_y = self.__camera.y % self.__camera.resolution
        view_width, view_height = self.__size[0], self.__size[1]

        for x in range(offset_x, view_width + 1, self.__camera.resolution):
            from_pos = (x, offset_y - self.__camera.resolution)
            to_pos = (x, offset_y + view_height)
            pygame.draw.line(self.__surface, settings.grid_color, from_pos, to_pos)

        for y in range(offset_y, view_height + 1, self.__camera.resolution):
            from_pos = (offset_x - self.__camera.resolution, y)
            to_pos = (offset_x + view_width, y)
            pygame.draw.line(self.__surface, settings.grid_color, from_pos, to_pos)

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

    @property
    def build_overlay(self) -> BuildOverlay:
        return self.__build_overlay


class BuildOverlay:

    def __init__(self,
                 buildings_infos: BuildingInformations,
                 default: str,
                 surface: pygame.Surface,
                 to_px_function: Callable[[int, int, int, int], tuple[int, int, int, int]]
                 ):
        self.__buildings_infos = buildings_infos
        self.__building = Building(buildings_infos.get_building_type(default), (0, 0))
        self.__surface = surface
        self.__func = to_px_function

        self.__conveyor_types = (
            "conveyor", "conveyor-reduced", "conveyor-l-shaped", "conveyor-wave-left", "conveyor-wave-right"
        )
        self.__conveyor_index = 0

    def rotate(self, direction: int):
        self.__building.rotate(-90 * direction)

    def update_pos(self, pos: tuple[int, int]):
        self.__building.pos = pos

    def draw(self, surface: pygame.Surface):
        image = self.__buildings_infos.get_image(self.__building)

        x_px, y_px = self.__func(*self.__building.pos)[:2]
        x_px -= image.get_width() / 2
        y_px -= image.get_height() / 2

        surface.blit(image, (x_px, y_px))

    def create(self):
        return self.__building.copy()

    def next_conveyor_type(self, direction: int):
        self.__conveyor_index = (self.__conveyor_index + direction) % len(self.__conveyor_types)
        self.building_type = self.__conveyor_types[self.__conveyor_index]

    @property
    def building_type(self) -> str:
        return self.__building.name

    @building_type.setter
    def building_type(self, typename: str):
        self.__building = Building(self.__buildings_infos.get_building_type(typename),
                                   self.__building.pos,
                                   self.__building.angle)
