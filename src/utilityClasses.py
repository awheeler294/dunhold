import libtcodpy as libtcod
import math

from defaultConstants import *


class QuitException(Exception):
    def __init__(self):
        pass


def get_random_int(minimum, maximum, stream=0):
    return libtcod.random_get_int(stream, minimum, maximum)


def is_window_closed():
    return libtcod.console_is_window_closed()


def create_fov_map(map_height, map_width, level_map):
    # create the FOV map, according to the level map
    fov_map = libtcod.map_new(map_width, map_height)
    for y in range(map_height):
        for x in range(map_width):
            libtcod.map_set_properties(fov_map, x, y, not level_map[x][y].block_sight, not level_map[x][y].blocks)

    return fov_map


def compute_fov(fov_map, x, y, sight_radius, fov_light_walls):
    libtcod.map_compute_fov(fov_map, x, y, sight_radius, fov_light_walls, FOV_ALGO)


def make_alphabetical_index(options):
    indexed = []
    index = ord('a')
    for option in options:
        index_letter = chr(index)
        entry = (index, option)
        indexed.append(entry)
        index += 1

    return indexed


def get_equipped_in_slot(slot, inventory):  # returns the equipment in a slot, or None if it's empty
    for obj in inventory:
        if obj.equipment and obj.equipment.slot == slot and obj.equipment.is_equipped:
            return obj.equipment
    return None


def random_choice_index(chances):  # choose one option from list of chances, returning its index
    # the dice will land on some number between 1 and the sum of the chances
    dice = libtcod.random_get_int(0, 1, sum(chances))

    # go through all chances, keeping the sum so far
    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w

        # see if the dice landed in the part that corresponds to this choice
        if dice <= running_sum:
            return choice
        choice += 1


def random_choice(chances_dict):
    # choose one option from dictionary of chances, returning its key
    chances = chances_dict.values()
    strings = chances_dict.keys()

    return strings[random_choice_index(chances)]


def from_danger_level(table, danger_level):
    # returns a value that depends on danger level.
    # The table specifies what value occurs after each level, default is 0.
    for (value, level) in reversed(table):
        if danger_level >= level:
            return value
    return 0
