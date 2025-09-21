from __future__ import annotations
import copy
import random
import re
import sys
from typing import Tuple, Union

import pygame.mouse
from pygame import Surface, SurfaceType, Rect
from pygame.rect import RectType

from surface_info import *
from draw_grids import *


def set_text_transparency(font_value, transparency, coordinates=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)):
    """
    Set text on the screen with specified attributes.

    Parameters:
    - font_value (Surface): The font to use for the text.
    - transparency (int): The transparency level of the text.
    - coordinates (Tuple[int, int]): The coordinates for the text position.

    Returns:
    Tuple[Surface, pygame.Rect]: A tuple containing the rendered text and its rect object.
    """
    font_value.set_alpha(transparency)
    font_rect = font_value.get_rect()

    font_rect.center = coordinates

    return font_value, font_rect


def resize_image(background_image, size, coordinates=(0, 0)):
    """
    Resize and reposition an image on the screen.

    Parameters:
    - background_image (Tuple[Surface | SurfaceType, str]): The image to resize.
    - coordinates (Tuple[int, int]): The coordinates for the image position.
    - size (Tuple[int, int]): The new size of the image.

    Returns:
    Tuple[Surface | SurfaceType, pygame.Rect]: A tuple containing the resized image and its rect object.
    """
    bg_img_rect = background_image[0][1]
    bg_img_rect.topleft = coordinates

    resized_image = pygame.transform.scale(background_image[0][0], size)
    return resized_image, bg_img_rect


def update_score(rack_size, rack_coordinates):
    key_deletion = []
    for key, value in PLAYER_1.items():
        if isinstance(value, list):  # Check if value is a list or tuple
            x, y = value[1][0], value[1][1]
            rack_x = (WINDOW_WIDTH // 2 - rack_size[0] // 2)
            rack_y = (WINDOW_HEIGHT - rack_size[1] * 2 + rack_size[1])
            if "1-15" in key and (x not in range(rack_coordinates[0], rack_x + rack_size[0]) or
                                  y not in range(rack_coordinates[1] - rack_size[1], rack_y + rack_size[1])):
                key_deletion.append(key)

    for key in key_deletion:
        del PLAYER_1[key]


def extract_last_number_from_filename(filename: str) -> int:
    """
    Extract the last number from the filename.

    Parameters:
    - filename (str): The filename to extract the last number from.

    Returns:
    int: The extracted last number.
    """
    match = re.search(r'_(\d+).png', filename)
    if match:
        return int(match.group(1))
    return 0


def extract_color_from_filename(filename: str) -> str:
    """
    Extract the color from the filename.

    Parameters:
    - filename (str): The filename to extract color from.

    Returns:
    str: The extracted color.
    """
    match = re.search(r'images\\tiles\\1-15 (BLACK|BLUE|GREEN|RED|YELLOW)_\d+_\d+.png', filename)
    if match:
        return match.group(1).lower()
    return ''


def identify_rummikub_runs(player):
    tile_keys = [key for key in player.keys() if 'images/tiles/1-15' in key]
    color_groups = {}

    for key in tile_keys:
        color = key.split('/')[-1].split('_')[0]
        if color not in color_groups:
            color_groups[color] = []
        color_groups[color].append(key)

    runs = []

    for color, tiles in color_groups.items():
        tiles.sort(key=extract_last_number_from_filename)
        current_run = []

        for i in range(len(tiles) - 1):
            current_number = int(extract_last_number_from_filename(tiles[i]))
            next_number = int(extract_last_number_from_filename(tiles[i + 1]))

            if next_number - current_number == 2:
                if tiles[i] not in current_run:
                    current_run.append(tiles[i])
                current_run.append(tiles[i + 1])
            else:
                if len(current_run) >= 2:
                    runs.append(current_run)
                current_run = []

        if len(current_run) >= 2:
            runs.append(current_run)

    return runs


def identify_rummikub_groups():
    groups = []
    seen_tiles = set()

    for key, value in PLAYER_1.items():
        if 'images/tiles/1-15' in key and key not in seen_tiles:
            number = extract_last_number_from_filename(key)
            color = extract_color_from_filename(key)

            group = [key]
            seen_tiles.add(key)

            for other_key, other_value in PLAYER_1.items():
                if 'images/tiles/1-15' in other_key and other_key not in seen_tiles:
                    other_number = extract_last_number_from_filename(other_key)
                    other_color = extract_color_from_filename(other_key)

                    if number == other_number and color == other_color:
                        group.append(other_key)
                        seen_tiles.add(other_key)

            if len(list(set(group))) >= 2:
                groups.append(group)

    return groups


class RummikubGame:
    def __init__(self, display_surface: Surface | SurfaceType):
        self.display_surface = display_surface
        self.image_database = {}
        self.font_database = {}
        self.game_object_database = {}
        self.DEFAULT_TILE_POSITIONS = tuple()
        pygame.font.init()  # Initialize the font module

    def initialize_window(self) -> None:
        """
        Initialize the Pygame module, create the application window, and set window properties.

        Returns:
        None
        """
        pygame.init()
        pygame.display.set_caption("Rummikub Game")
        pygame.display.set_icon(self.load_image(ICON_PATH)[0][0])

    def load_image(self, image_path: str, coordinates: Tuple[int, int] = None, size: Tuple[int, int] = None) -> \
            tuple[tuple[Surface | SurfaceType, Rect | RectType], str]:
        """
        Load an image from the specified path.

        Parameters:
        - image_path (str): The path to the image file.
        - coordinates (Tuple[int, int]): The coordinates to place the image.
        - size (Tuple[int, int]): The size of the image.

        Returns:
        Tuple[Surface | SurfaceType, str]: The loaded image and its path.
        """
        loaded_image = pygame.image.load(image_path)
        is_none = coordinates is not None and size is not None

        if is_none and image_path not in self.image_database:
            image_rect = loaded_image.get_rect()
            image_rect.x = coordinates[0]
            image_rect.y = coordinates[1]
            self.image_database[image_path] = (loaded_image, list(coordinates), size, image_rect)
        elif is_none and image_path in self.image_database:
            image_rect = loaded_image.get_rect()
            image_rect.x = coordinates[0]
            image_rect.y = coordinates[1]
            self.image_database[image_path] = (loaded_image, list(coordinates), size, image_rect)
        return (loaded_image, loaded_image.get_rect()), image_path

    def load_font(self, font_path: str, text: Tuple[str, Tuple[int, int, int], Union[None, Tuple[int, int, int]]],
                  size: int) -> Surface | SurfaceType:
        """
        Load a font and render text with specified attributes.

        Parameters:
        - font_path (str): A string contains path to text.
        - text (Tuple[str, Tuple[int, int, int], Union[None, Tuple[int, int, int]]]): A tuple containing text,
        text color, and background color.
        - size (int): The size of the font.

        Returns:
        Surface: The rendered text surface.
        """
        set_font = pygame.font.Font(font_path, size)
        set_font_rend = set_font.render(text[0], True, text[1], text[2])
        self.font_database[FONT_PATH] = set_font_rend
        return set_font_rend

    def set_image_transparency(self, color: Tuple[int, int, int, int], rect: Tuple[int, int, int, int]):
        """
        Draw a transparent rectangle on the display surface.

        Parameters:
        - color (Tuple[int, int, int, int]): The color of the rectangle with alpha channel.
        - rect (Tuple[int, int, int, int]): The coordinates and size of the rectangle.

        Returns:
        None
        """
        shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
        pygame.draw.rect(shape_surf, color, shape_surf.get_rect())
        self.display_surface.blit(shape_surf, rect)
        return

    def get_game_object(self):
        default_button_size = self.load_image(ADD_CARDS_PATH)[0][0].get_width()
        SIZE = {"background_image": self.display_surface.get_size(), "brown_rack_image_tile1": RACK_SIZE,
                "brown_rack_image_tile2": (RACK_SIZE[0] - 10, RACK_SIZE[1]),
                "add_cards": (default_button_size, 175),
                "check_logic_button": (default_button_size, default_button_size),
                "rearrange_numbers": (default_button_size, 155),
                "menu_button": (default_button_size, 60),
                "background_text": 64,
                }

        COORDINATES = {"background_image": (0, 0),
                       "brown_rack_image_tile1": (WINDOW_WIDTH // 2 - SIZE["brown_rack_image_tile1"][0] // 2,
                                                  WINDOW_HEIGHT - SIZE["brown_rack_image_tile1"][1]),
                       "brown_rack_image_tile2": (WINDOW_WIDTH // 2 - SIZE["brown_rack_image_tile2"][0] // 2,
                                                  WINDOW_HEIGHT - SIZE["brown_rack_image_tile2"][1] * 2),
                       "add_cards": (WINDOW_WIDTH - SIZE["add_cards"][0] - 30,
                                     WINDOW_HEIGHT - SIZE["add_cards"][1] - 50),
                       "check_logic_button": (WINDOW_WIDTH - SIZE["add_cards"][0] - 30,
                                              WINDOW_HEIGHT - SIZE["add_cards"][1] - 200),
                       "rearrange_numbers": (WINDOW_WIDTH - SIZE["rearrange_numbers"][0] - 30,
                                             WINDOW_HEIGHT - SIZE["rearrange_numbers"][1] - SIZE["add_cards"][1] - 300),
                       "menu_button": (WINDOW_WIDTH - SIZE["menu_button"][0] - 30, 25),
                       "background_text": "default"
                       }

        IMAGES = (BG_IMAGE_PATH, TABLE_IMAGE_PATH, TABLE_IMAGE_PATH,
                  ADD_CARDS_PATH, CHECK_LOGIC_BUTTON, REARRANGE_TILES_ICON_PATH, MENU_ICON_PATH, FONT_PATH)
        return SIZE, COORDINATES, IMAGES

    def set_game_object(self) -> dict:
        set_object = self.get_game_object()
        size, coordinates, images = set_object[0], set_object[1], set_object[2]

        for s, c, path in zip(size.keys(), coordinates.keys(), images):
            if "text" not in s:
                loaded_image = self.load_image(path, coordinates[s], size[s])
                if s == c and "text" not in s:
                    self.game_object_database[s] = (
                        resize_image(loaded_image, size[s], coordinates[c])[0], loaded_image[0][1])
                else:
                    print("{0} not found in the system".format(s))
            else:
                loaded_text = self.load_font(path, BG_TEXT, size[s])
                self.game_object_database[s] = (set_text_transparency(loaded_text, 50))

        return self.game_object_database

    def get_tile_by_position(self, big_box):
        data_list = {}
        for key, (tile_surface, tile_position) in self.game_object_database.items():
            if "1-15" in key:
                # Calculate the center of the tile
                tile_center_x = tile_position.x + tile_position.width // 2
                tile_center_y = tile_position.y + tile_position.height // 2

                # Check if the center of the tile is within the big_box
                if big_box.left <= tile_center_x <= big_box.right and \
                        big_box.top <= tile_center_y <= big_box.bottom:
                    data_list[key] = (tile_position.x, tile_position.y)

        def sort_by_dimensions(item):
            return item[1][1], item[1][0]

        sorted_data = sorted(data_list.items(), key=sort_by_dimensions)
        dimensions_dict = {}
        for data_item in sorted_data:
            dimensions = data_item[1][1]
            dimensions_dict.setdefault(dimensions, []).append(data_item)

        # Initialize lists to store the final result
        shuffled_combinations = []
        remaining_items = []

        # Iterate through dimensions_dict and categorize items
        for dimensions, items in dimensions_dict.items():
            if len(items) > 1:
                shuffled_combinations.append(items)
            else:
                remaining_items.extend(items)
        # Sort the final lists
        shuffled_combinations = [sorted(sublist, key=sort_by_dimensions) for sublist in shuffled_combinations]
        remaining_items = sorted(remaining_items, key=sort_by_dimensions)
        final_combinations, filtering_list = [], []

        for combination_items in shuffled_combinations:
            temp_combination = []
            i, j = 0, 1
            while j != len(combination_items):
                first_item = combination_items[i][1]
                next_item = combination_items[j][1]
                if (first_item[1] == next_item[1]
                        and (first_item[0] + 52 == next_item[0] or
                             first_item[0] - 52 == next_item[0] or
                             first_item[0] == next_item[0] + 52 or
                             first_item[0] == next_item[0] - 52)):

                    if combination_items[i] not in temp_combination:
                        temp_combination.append(combination_items[i])
                    if combination_items[j] not in temp_combination:
                        temp_combination.append(combination_items[j])

                else:
                    filtering_list.append(combination_items[i])
                    filtering_list.append(combination_items[j])
                    if len(combination_items) >= 2:
                        final_combinations.append(copy.deepcopy(temp_combination))
                    temp_combination.clear()
                i += 1
                j += 1
            if len(combination_items) >= 2:
                final_combinations.append(copy.deepcopy(temp_combination))
            if i == len(combination_items):
                break
        final_combinations_remove_empty_set = [sublist for sublist in final_combinations if sublist]

        def is_filtered():
            for filer_values in filtering_list:
                for sub_list in final_combinations_remove_empty_set:
                    if filer_values in sub_list:
                        filtering_list.remove(filer_values)

        for i in range(15):
            is_filtered()

        for filer_val in filtering_list:
            final_combinations_remove_empty_set.append([filer_val])

        remaining_items = [item for i, item in enumerate(remaining_items) if
                           all(item != remaining_items[j] for j in range(len(remaining_items)) if i != j)]

        for values in final_combinations_remove_empty_set:
            for value in values:
                while value in remaining_items:
                    remaining_items.remove(value)

        if len(remaining_items) > 0:
            final_combinations_remove_empty_set.append(remaining_items)

        return final_combinations_remove_empty_set

    def play_ai_turn(self):
        card_number = {}
        for key, value in PLAYER_2.items():
            if key[-6:-4].isdigit():
                card, color = key[-6:-4], key[-8:-7]
                card_number[key] = (card, color, value)
            else:
                card, color = key[-5:-4], key[-7:-6]
                card_number[key] = (card, color, value)

        odd_sequence = {}
        even_sequence = {}

        for key, values in card_number.items():
            if int(values[0]) % 2 == 0:
                even_sequence[key] = values
            else:
                odd_sequence[key] = values

        def group_tiles_by_integer(tile_list):
            grouped_tiles = {}

            for tile in tile_list:
                integer_value = tile[1][1]
                if integer_value not in grouped_tiles:
                    grouped_tiles[integer_value] = []
                grouped_tiles[integer_value].append(tile)

            for group_key in grouped_tiles:
                grouped_tiles[group_key] = sorted(grouped_tiles[group_key], key=lambda item: int(item[1][0]))

            return grouped_tiles

        even_sequence_sorted = sorted(even_sequence.items(), key=lambda item: (item[1][1], int(item[1][0])))
        odd_sequence_sorted = sorted(odd_sequence.items(), key=lambda item: (item[1][1], int(item[1][0])))

        grouped_by_even_seq = group_tiles_by_integer(even_sequence_sorted)
        grouped_by_odd_seq = group_tiles_by_integer(odd_sequence_sorted)

        c_x, c_y = BIG_BOX_POSITION[0], BIG_BOX_POSITION[1]
        is_odd = False
        c_x_change = 52
        prev_key = None
        keys_to_delete = []

        for index, (key, value) in enumerate(grouped_by_even_seq.items()):
            if len(value) in range(3, 6):
                is_odd = True
                for v in value:
                    v[1][2][1].x = c_x
                    v[1][2][1].y = c_y

                    self.game_object_database[v[0]] = v[1][2]
                    img = v[1][2]
                    self.image_database[v[0]] = (img[0], (c_x, c_y), (52, 73), img[1])

                    if prev_key is not None and prev_key != key:
                        c_x += c_x_change
                        c_x_change = 52
                    else:
                        c_x += c_x_change

                    prev_key = key

                    keys_to_delete.append(v[0])

        if is_odd:
            c_x += 52

        for index, (key, value) in enumerate(grouped_by_odd_seq.items()):
            if len(value) in range(3, 6):
                for v in value:

                    v[1][2][1].x = c_x
                    v[1][2][1].y = c_y

                    self.game_object_database[v[0]] = v[1][2]
                    img = v[1][2]
                    self.image_database[v[0]] = (img[0], (c_x, c_y), (52, 73), img[1])

                    if prev_key is not None and prev_key != key:
                        c_x += c_x_change
                        c_x_change = 52
                    else:
                        c_x += c_x_change

                    prev_key = key

                    keys_to_delete.append(v[0])

        for key_to_delete in keys_to_delete:
            if key_to_delete in PLAYER_2:
                del PLAYER_2[key_to_delete]

        self.update_blit()

    def show_computer_cards(self):
        show_cards = True

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONUP:
                    show_cards = not show_cards

            if show_cards:

                c_x, c_y = 350, WINDOW_HEIGHT - 210
                font = pygame.font.Font(FONT_PATH, 36)
                text = font.render("PLAYER 2 :=", True, (255, 255, 255))
                rect = text.get_rect()
                rect.x, rect.y = 50, WINDOW_HEIGHT - 200
                for ai_key, ai_cards in PLAYER_2.items():
                    ai_cards[1].x = c_x
                    ai_cards[1].y = c_y
                    self.display_surface.blit(ai_cards[0], ai_cards[1])
                    self.display_surface.blit(text, rect)
                    c_x += ai_cards[0].get_width() + 5
                    if c_x > WINDOW_WIDTH:
                        c_x = WINDOW_WIDTH + 5
                        c_y += ai_cards[0].get_height() + 5

            else:
                for ai_key, ai_cards in PLAYER_2.items():
                    ai_cards[1].x = -1000
                    ai_cards[1].y = -1000
                pygame.display.flip()
                return False

            pygame.display.flip()

    def menu_function(self):
        menu_options = [
            "1. Play For Me",
            "2. Show AI Cards",
            "3. Close Menu",
            "4. Exit Game"
        ]

        self.set_image_transparency((0, 0, 0, 150), (0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))

        font = pygame.font.Font(FONT_PATH, 36)
        y_offset = 100
        selected_menu = {}

        for option in menu_options:
            text = font.render(option, True, (255, 255, 255))
            rect = text.get_rect(center=(WINDOW_WIDTH // 2, y_offset))
            selected_menu[option] = rect  # Store only the Rect object
            self.display_surface.blit(text, rect)
            y_offset += 40

        pygame.display.flip()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONUP:
                    position = pygame.mouse.get_pos()
                    for k, rect in selected_menu.items():
                        if rect.collidepoint(position):
                            if k == "3. Close Menu":
                                return False
                            elif k == "4. Exit Game":
                                pygame.quit()
                                sys.exit()
                            elif k == "2. Show AI Cards":
                                while True:
                                    status = self.show_computer_cards()
                                    if not status:
                                        break
                                pygame.display.flip()

    def rearrange_tiles_by_groups(self, groups):
        rack_coordinates = self.get_game_object()[1]["brown_rack_image_tile2"]
        c_x, c_y = rack_coordinates[0] + 5, rack_coordinates[1]
        non_group_positions = []

        if groups:
            for group in groups:
                for key in group:
                    tile_image, _ = self.game_object_database[key]
                    new_tile_position = pygame.Rect(c_x, c_y, tile_image.get_width(), tile_image.get_height())
                    self.game_object_database[key] = (tile_image, new_tile_position)
                    self.image_database[key] = (tile_image, (c_x, c_y), (52, 73), new_tile_position)
                    c_x += tile_image.get_width() + 10
                non_group_positions.append((c_x, c_y))
            c_x, c_y = non_group_positions[-1]

        for key, (tile_image, _) in PLAYER_1.items():
            if 'images/tiles/1-15' in key and key not in [tile for group in groups for tile in group]:
                new_tile_position = pygame.Rect(c_x, c_y, tile_image.get_width(), tile_image.get_height())
                self.game_object_database[key] = (tile_image, new_tile_position)
                self.image_database[key] = (tile_image, (c_x, c_y), (52, 73), new_tile_position)
                c_x += tile_image.get_width() + 10

                if (c_x + tile_image.get_width()) > (
                        rack_coordinates[0] + self.get_game_object()[0]["brown_rack_image_tile2"][0]):
                    c_x, c_y = rack_coordinates[0] + 5, c_y + tile_image.get_height() + 10

        self.update_blit()
        pygame.display.flip()

    def rearrange_tiles_by_runs(self, runs):
        rack_coordinates = self.get_game_object()[1]["brown_rack_image_tile2"]
        c_x, c_y = rack_coordinates[0] + 5, rack_coordinates[1]
        non_run_positions = []

        if runs:
            runs = [tile for run in runs for tile in run]
            runs.sort(key=extract_last_number_from_filename)

            for key in runs:
                tile_image, placeholder = self.game_object_database[key]
                new_tile_position = pygame.Rect(c_x, c_y, tile_image.get_width(), tile_image.get_height())
                self.game_object_database[key] = (tile_image, new_tile_position)
                self.image_database[key] = (tile_image, (c_x, c_y), (52, 73), new_tile_position)
                c_x += tile_image.get_width() + 10

            non_run_positions.append((c_x, c_y))
            c_x, c_y = non_run_positions[-1]

            for key, (tile_image, _) in PLAYER_1.items():
                if 'images/tiles/1-15' in key and key not in runs:
                    new_tile_position = pygame.Rect(c_x, c_y, tile_image.get_width(), tile_image.get_height())
                    self.game_object_database[key] = (tile_image, new_tile_position)
                    self.image_database[key] = (tile_image, (c_x, c_y), (52, 73), new_tile_position)
                    c_x += tile_image.get_width() + 10

                    if (c_x + tile_image.get_width()) > (
                            rack_coordinates[0] + self.get_game_object()[0]["brown_rack_image_tile2"][0]):
                        c_x, c_y = rack_coordinates[0] + 5, c_y + tile_image.get_height() + 10

            self.update_blit()
            pygame.display.flip()

    def rearrange_tiles_by_colors(self):
        tile_keys = [key for key in PLAYER_1.keys() if 'images/tiles/1-15' in key]

        color_groups = {}
        for key in tile_keys:
            color = key.split('/')[-1].split('_')[0]
            if color not in color_groups:
                color_groups[color] = []
            color_groups[color].append(key)

        for color, tiles in color_groups.items():
            tiles.sort(key=extract_last_number_from_filename)

        def sort_key(item):
            return extract_last_number_from_filename(item[1][0])

        sorted_color_groups = sorted(color_groups.items(), key=sort_key)

        rack_size = self.get_game_object()[0]["brown_rack_image_tile2"]
        rack_coordinates = self.get_game_object()[1]["brown_rack_image_tile2"]
        c_x, c_y = rack_coordinates[0] + 5, rack_coordinates[1]

        for _, tiles in sorted_color_groups:
            for key in tiles:
                tile_image = self.game_object_database[key][0]
                tile_position = pygame.Rect(c_x, c_y, tile_image.get_width(), tile_image.get_height())

                self.game_object_database[key] = (tile_image, tile_position)
                self.image_database[key] = (tile_image, (c_x, c_y), (52, 73), tile_position)

                c_x += tile_image.get_width() + 10

                if (c_x + tile_image.get_width()) > (rack_size[0] + rack_coordinates[0]):
                    c_y = rack_coordinates[1] + rack_size[1]
                    c_x = rack_coordinates[0]

        self.update_blit()
        pygame.display.flip()

    def rearrange_tiles(self, player_tiles, rack_size, rack_coordinates):
        c_x, c_y = rack_coordinates[0] + 5, rack_coordinates[1]

        for key, value in player_tiles.items():
            if key in self.game_object_database:

                self.game_object_database[key][1][0] = c_x
                self.game_object_database[key][1][1] = c_y
                self.image_database[key][3].x = c_x
                self.image_database[key][3].y = c_y

                rect_copy = copy.deepcopy(self.game_object_database[key][1])
                self.DEFAULT_TILE_POSITIONS += ((key, rect_copy),)

                c_x += 52 + 10

                if (c_x + 52) > (rack_size[0] + rack_coordinates[0]):
                    c_y = rack_coordinates[1] + rack_size[1]
                    c_x = rack_coordinates[0]

        # Update the display or blit the rearranged tiles
        self.update_blit()

    def add_tile_to_rack(self, rack_size):
        last_key, last_value = list(PLAYER_1.items())[-1]
        random_tile_temp = []
        tile_image_list = TILES_IMAGES_PATHS
        TILE_MARGIN_X = 10
        color = ["BLACK", "BLUE", "GREEN", "RED", "YELLOW"]
        new_tile_position = [
            last_value[1][0] + 52 + TILE_MARGIN_X,
            last_value[1][1]
        ]

        while True:
            random_tile = (
                random.randint(1, len(tile_image_list) - 1),
                random.randint(1, len(tile_image_list[0]))
            )

            tile_image_path = "images/tiles/1-15 {}/{}_{}_{}.png".format(
                color[random_tile[0] - 1],
                color[random_tile[0] - 1],
                random_tile[0],
                random_tile[1]
            )
            if new_tile_position[0] > rack_size[0] + 273:
                new_tile_position[0] = self.game_object_database["brown_rack_image_tile1"][1][0] + TILE_MARGIN_X
                new_tile_position[1] = last_value[1][1] + rack_size[1]
            if tile_image_path in IMG_PATHS or tile_image_path in PLAYER_2:
                continue

            if (tile_image_path not in IMG_PATHS or tile_image_path not in PLAYER_2 or
                    new_tile_position[1] > new_tile_position[1] + rack_size[1] * 2):
                break

        if (new_tile_position[0] < rack_size[0] + 273 and tile_image_path not in PLAYER_2 and
                tile_image_path not in IMG_PATHS and
                new_tile_position[1] < new_tile_position[1] + rack_size[1] * 2):
            is_present = str(random_tile[0]) + str(random_tile[1])
            random_tile_temp.append(is_present)

            # Load the new tile image
            tile_image = self.load_image(tile_image_path, (new_tile_position[0], new_tile_position[1]), (52, 73))
            # Update IMG_PATHS
            IMG_PATHS.append(tile_image_path)

            recreated_surface = resize_image(tile_image, (52, 73), new_tile_position)
            self.game_object_database["{0}".format(tile_image_path)] = recreated_surface
            PLAYER_1["{0}".format(tile_image_path)] = list(recreated_surface)
            # self.play_ai_turn()
            self.update_blit()

    def draw_initial_tiles(self, tile_image_list, players_database):
        random_tile_temp = []
        for players in players_database:
            while len(players) != 15:
                random_tile = (
                    random.randint(0, len(tile_image_list) - 1),
                    random.randint(1, len(tile_image_list[0]))
                )
                is_present = str(random_tile[0]) + str(random_tile[1])

                if is_present not in random_tile_temp:
                    random_tile_temp.append(is_present)
                    tile_image_path = tile_image_list[random_tile[0]][random_tile[1]]
                    tile_image = self.load_image(tile_image_path)
                    players[tile_image[1]] = list(tile_image[0])
        return players_database

    def place_initial_tiles(self, player_tiles, rack_size, rack_coordinates):
        c_x, c_y = rack_coordinates[0] + 5, rack_coordinates[1]
        for tile_value in player_tiles:
            for key, value in tile_value.items():
                tile_image = self.load_image(key, (c_x, c_y), (52, 73))

                if value not in IMG_PATHS:
                    IMG_PATHS.append(copy.deepcopy(key))
                surface_info = SurfaceInfo(tile_image[1], (c_x, c_y), (52, 73))
                recreated_surface = recreate_surface(surface_info)
                self.game_object_database[key] = recreated_surface
                PLAYER_1[key] = list(recreated_surface)
                rect_copy = copy.deepcopy(recreated_surface[1])
                self.DEFAULT_TILE_POSITIONS += ((key, rect_copy),)
                c_x += 52 + 10

                if (c_x + 52) > (rack_size[0] + rack_coordinates[0]):
                    c_y = rack_coordinates[1] + rack_size[1]
                    c_x = rack_coordinates[0]

    def update_values(self, item_sum):
        prev_item_value, prev_item_color = item_sum[next(iter(item_sum))][0], item_sum[next(iter(item_sum))][1]

        all_same_numbers_satisfied = all(item_value[0] == prev_item_value
                                         for item_value in item_sum.values())
        all_different_color_satisfied = all(item_value[1] != prev_item_color
                                            for index, item_value in enumerate(item_sum.values())
                                            if index != 0)
        all_same_color_satisfied = all(item_value[1] == prev_item_color
                                       for index, item_value in enumerate(item_sum.values())
                                       if index != 0)

        all_even_numbers_satisfied = True
        even_values = list(item_sum.values())
        for i in range(len(even_values) - 1):
            current_value = int(even_values[i][0])
            next_value = int(even_values[i + 1][0])

            if current_value % 2 != 0 or (current_value >= next_value and current_value + 2 != next_value):
                all_even_numbers_satisfied = False
                break

        if int(even_values[-1][0]) % 2 != 0:
            all_even_numbers_satisfied = False

        all_odd_numbers_satisfied = True
        odd_values = list(item_sum.values())

        for i in range(len(odd_values) - 1):
            current_value = int(odd_values[i][0])
            next_value = int(odd_values[i + 1][0])

            if current_value % 2 == 0 or (current_value >= next_value and current_value + 2 != next_value):
                all_odd_numbers_satisfied = False
                break

        if int(odd_values[-1][0]) % 2 == 0:
            all_odd_numbers_satisfied = False

        if ((all_same_numbers_satisfied and all_different_color_satisfied) or
                (all_same_color_satisfied and all_even_numbers_satisfied or all_odd_numbers_satisfied)):
            for index, (item_key, item_value) in enumerate(item_sum.items()):
                if item_key in self.game_object_database.keys():
                    if item_key in PLAYER_1.keys():
                        PLAYER_1[item_key][1][0], PLAYER_1[item_key][1][1] = item_value[2][0], item_value[2][1]
                    (self.game_object_database[item_key][1][0],
                     self.game_object_database[item_key][1][1],
                     self.image_database[item_key][3][0],
                     self.image_database[item_key][3][1]) = (item_value[2][0], item_value[2][1],
                                                             item_value[2][0], item_value[2][1])

                    update_score((self.game_object_database["brown_rack_image_tile2"][1][2],
                                  self.game_object_database["brown_rack_image_tile2"][1][3]),
                                 (self.game_object_database["brown_rack_image_tile2"][1]))
                    self.rearrange_tiles(PLAYER_1, (self.game_object_database["brown_rack_image_tile2"][1][2],
                                                    self.game_object_database["brown_rack_image_tile2"][1][3]),
                                         (self.game_object_database["brown_rack_image_tile2"][1]))
                    # self.play_ai_turn()
        else:
            for key, value in PLAYER_1.items():
                if "images/tiles/1-15" in key:
                    (self.game_object_database[key][1][0],
                     self.game_object_database[key][1][1]) = (self.image_database[key][1][0],
                                                              self.image_database[key][1][1])
        self.update_blit()

    def check_logic(self):
        permutation_values = self.get_tile_by_position(BIG_BOX)
        if len(CURRENT_POSITION) >= 3 and permutation_values != []:
            card_number, check_sum, index = {}, [], 0

            for perm_values in permutation_values:
                if all(len(perm_value) >= 3 for perm_value in permutation_values):
                    card_number.clear()
                    for key, value in perm_values:
                        if key[-6:-4].isdigit():
                            card, color = key[-6:-4], key[-8:-7]
                            card_number[key] = (card, color, value)
                        else:
                            card, color = key[-5:-4], key[-7:-6]
                            card_number[key] = (card, color, value)
                    if card_number not in check_sum:
                        check_sum.append(copy.deepcopy(card_number))
                else:
                    for key, value in PLAYER_1.items():
                        if "images/tiles/1-15" in key:
                            (self.game_object_database[key][1][0],
                             self.game_object_database[key][1][1]) = (self.image_database[key][1][0],
                                                                      self.image_database[key][1][1])

            for check in check_sum:
                self.update_values(check)

        else:
            for key, value in PLAYER_1.items():
                if "images/tiles/1-15" in key:
                    (self.game_object_database[key][1][0],
                     self.game_object_database[key][1][1]) = (self.image_database[key][1][0],
                                                              self.image_database[key][1][1])
        self.update_blit()

    def move_tiles(self, mouse_position, key_list, value_list):
        mouse_x, mouse_y = mouse_position

        for key, value in zip(key_list, value_list):
            tile_surface, tile_position = self.game_object_database[key]
            if tile_position.collidepoint(mouse_x, mouse_y):
                # Calculate the offset from the center of the tile
                offset_x = mouse_x - (tile_position.x + tile_position.width // 2)
                offset_y = mouse_y - (tile_position.y + tile_position.height // 2)

                dragging = True
                while dragging:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        elif event.type == pygame.MOUSEMOTION:
                            mouse_x, mouse_y = event.pos
                            # Update the tile position based on the mouse movement
                            tile_position.x = mouse_x - offset_x - tile_position.width // 2
                            tile_position.y = mouse_y - offset_y - tile_position.height // 2

                            # Draw grids while dragging
                            draw_3d_grid(self.display_surface, GRID_WIDTH, GRID_HEIGHT, BIG_BOX)

                            pygame.display.flip()
                        elif event.type == pygame.MOUSEBUTTONUP:
                            dragging = False

                            # Snap the tile to the grid
                            snapped_rect, status = snap_to_grid(tile_position, GRID_WIDTH, GRID_HEIGHT, BIG_BOX,
                                                                value[1])
                            if status:
                                if (snapped_rect[0], snapped_rect[1]) not in (CURRENT_POSITION, value[1]):
                                    CURRENT_POSITION[key] = (snapped_rect[0], snapped_rect[1])

                            tile_position.x, tile_position.y = snapped_rect.x, snapped_rect.y

                            self.update_blit()

                            draw_3d_grid(self.display_surface, GRID_WIDTH, GRID_HEIGHT, BIG_BOX)

                            pygame.display.flip()

        pygame.display.update()

    def handle_mouse_motion(self, value: dict, color: Tuple[int, int, int, int] = (36, 160, 237, 30),
                            mouse=False) -> None:
        """
        Handle mouse motion events.

        Parameters:
        - value (dict): A dictionary containing rect objects of various elements.
        - color (Tuple[int, int, int, int]): The color of the transparent rectangle.

        Returns:
        None
        """
        position = pygame.mouse.get_pos()
        for k, val in value.items():
            flag = False
            if value["add_cards"] == val and val.collidepoint(position) and mouse:
                self.add_tile_to_rack(self.get_game_object()[0]["brown_rack_image_tile2"])
            elif value["check_logic_button"] == val and val.collidepoint(position) and mouse:
                self.check_logic()
            elif value["menu_button"] == val and val.collidepoint(position) and mouse:
                while True:
                    status = self.menu_function()
                    if not status:
                        break
                self.update_blit()
            elif value["rearrange_numbers"] == val and val.collidepoint(position) and mouse:
                x_top_axis, y_top_axis, width, height = (
                    val[0], val[1],
                    val[2], val[3]
                )
                r_777 = pygame.Rect(x_top_axis, y_top_axis, width, height // 2)

                r_789 = pygame.Rect(x_top_axis, y_top_axis + height // 2, width, height // 2)

                if r_777.collidepoint(position):
                    groups = identify_rummikub_groups()
                    self.rearrange_tiles_by_groups(groups)

                elif r_789.collidepoint(position):
                    runs = identify_rummikub_runs(PLAYER_1)
                    self.rearrange_tiles_by_runs(runs)

            if val.collidepoint(position):
                rearrange_button_path = IMG_PATHS[1]
                for i, img_path in enumerate(IMG_PATHS):
                    x_top_axis, y_top_axis, x_bottom_axis, y_bottom_axis = (
                        self.image_database[img_path][1][0],
                        self.image_database[img_path][1][1],
                        (self.image_database[img_path][1][0] + self.image_database[img_path][2][0]),
                        (self.image_database[img_path][1][1] + self.image_database[img_path][2][1])
                    )

                    if (position[0] in range(x_top_axis, x_bottom_axis) and
                            position[1] in range(y_top_axis, y_bottom_axis)):

                        if img_path == rearrange_button_path:
                            if position[1] in range(y_top_axis, (y_bottom_axis + y_top_axis) // 2):
                                self.set_image_transparency(color, (x_top_axis, y_top_axis,
                                                                    x_bottom_axis - x_top_axis,
                                                                    (y_bottom_axis - y_top_axis) // 2))

                            else:
                                self.set_image_transparency(color, (x_top_axis, y_top_axis * 2 - 40,
                                                                    x_bottom_axis - x_top_axis,
                                                                    (y_bottom_axis - y_top_axis) // 2))
                            flag = True
                            break
                        else:
                            self.set_image_transparency(color, (x_top_axis, y_top_axis,
                                                                x_bottom_axis - x_top_axis,
                                                                y_bottom_axis - y_top_axis))

                            flag = True
                            break

                if flag:
                    break

    def update_blit(self) -> dict:
        """
        Update and blit the elements on the display surface.

        Returns:
        dict: A dictionary containing the rect objects of various elements.
        """
        display_object = {}
        for key, value in self.game_object_database.items():
            self.display_surface.blit(value[0], value[1])
            display_object[key] = value[1]

        pygame.draw.line(self.display_surface, LINE_COLOR, (0, WINDOW_HEIGHT),
                         (WINDOW_WIDTH, WINDOW_HEIGHT), 20)
        pygame.display.flip()
        return display_object

    def game_status(self):
        """
        Main function to manage the game status and events.

        Returns:
        str: The status of the game (e.g., "Exit").
        """
        self.initialize_window()
        status, running = None, True

        self.set_game_object()

        PLAYERS_DB = self.draw_initial_tiles(TILES_IMAGES_PATHS, PLAYERS)
        self.place_initial_tiles([PLAYERS_DB[0]], self.get_game_object()[0]["brown_rack_image_tile2"],
                                 self.get_game_object()[1]["brown_rack_image_tile2"])

        while running:
            value = self.update_blit()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONUP:
                    KEYS_LIST = [k for k, v in self.game_object_database.items() if
                                 "brown_rack_image_tile" not in k and "tile" in k]
                    VALUE_LIST = [v for k, v in self.image_database.items() if "1-15" in k]
                    self.move_tiles(pygame.mouse.get_pos(), KEYS_LIST, VALUE_LIST)
                    self.handle_mouse_motion(value, (36, 160, 237, 120), True)
                if event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(value)

            pygame.display.flip()
