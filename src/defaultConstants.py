import libtcodpy as libtcod

# actual size of the window
SCREEN_WIDTH = 100
SCREEN_HEIGHT = 80
# SCREEN_WIDTH = 80
# SCREEN_HEIGHT = 50

# size of the map
MAP_WIDTH = 80
MAP_HEIGHT = 43

# sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 50
CHARACTER_SCREEN_WIDTH = 30
LEVEL_SCREEN_WIDTH = 40

# parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_OBJECTS = 7

# spell values
HEAL_AMOUNT = 40
LIGHTNING_DAMAGE = 40
LIGHTNING_RANGE = 5
CONFUSE_RANGE = 8
CONFUSE_NUM_TURNS = 10
FIREBALL_RADIUS = 3
FIREBALL_DAMAGE = 25

# experience and level-ups
LEVEL_UP_BASE = 200
LEVEL_UP_FACTOR = 150


SEIGHT_RADIUS = 10

COLOR_DARK_WALL = libtcod.dark_gray
COLOR_LIGHT_WALL = libtcod.white
COLOR_DARK_GROUND = libtcod.dark_gray
COLOR_LIGHT_GROUND = libtcod.Color(0, 0, 100)
COLOR_BACKGROUND = libtcod.black
COLOR_EXIT = libtcod.gray

ENTRANCE_CHAR = '<'
EXIT_CHAR = '>'

AVERAGE_STAT = 10

SAFE_MOVE_WAIT_TIME = 50

# movement constants
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
UP_LEFT = (-1, -1)
UP_RIGHT = (1, -1)
DOWN_LEFT = (-1, 1)
DOWN_RIGHT = (1, 1)
HERE = (0, 0)

SURROUNDING_OFFSETS = frozenset([UP, DOWN, LEFT, RIGHT, UP_LEFT, UP_RIGHT, DOWN_LEFT, DOWN_RIGHT])
############# ############# ############# #############
# ...........# #...........# #...........# #...........#
# ..#######..# #..#.#......# #..#######..# #......#.#..#
# ..#@.......# #..#.#......# #.......@#..# #......#.#..#
# ..#.#####..# #..#.#####..# #..#####.#..# #..#####.#..#
# ..#.#......# #..#@.......# #......#.#..# #.......@#..#
# ..#.#......# #..#######..# #......#.#..# #..#######..#
# ...........# #...........# #...........# #...........#
############# ############# ############# #############
LEFT_TOP_ELBOW = frozenset([DOWN, RIGHT])
LEFT_BOTTOM_ELBOW = frozenset([UP, RIGHT])
RIGHT_TOP_ELBOW = frozenset([DOWN, LEFT])
RIGHT_BOTTOM_ELBOW = frozenset([UP, LEFT])
############# ############# ############# #############
# ...........# #...........# #...........# #...........#
# ..#######..# #....#.#....# #......#.#..# #..#.#......#
# .....@.....# #....#.#....# #..#####.#..# #..#.#####..#
# ..###.###..# #..###.###..# #.......@#..# #..#@.......#
# ....#.#....# #.....@.....# #..#####.#..# #..#.#####..#
# ....#.#....# #..#######..# #......#.#..# #..#.#......#
# ...........# #...........# #...........# #...........#
############# ############# ############# #############
TOP_TEE = frozenset([DOWN, LEFT, RIGHT])
BOTTOM_TEE = frozenset([UP, LEFT, RIGHT])
LEFT_TEE = frozenset([UP, DOWN, LEFT])
RIGHT_TEE = frozenset([UP, DOWN, RIGHT])
############# ############# #############
# ...........# #...........# #...........#
# ....#.#....# #....#.#....# #...........#
# .####.###..# #....#.#....# #..#######..#
# .....@.....# #....#@#....# #.....@.....#
# .####.###..# #....#.#....# #..#######..#
# ....#.#....# #....#.#....# #...........#
# ...........# #...........# #...........#
############# ############# #############
FOURWAY_INTERSECTION = frozenset([UP, DOWN, LEFT, RIGHT])
VERTICAL_HALLWAY = frozenset([UP, DOWN])
HORIZONTAL_HALLWAY = frozenset([LEFT, RIGHT])
############# ############# ############# #############
# ...........# #...........# #...........# #...........#
# ..#######..# #...........# #..#........# #........#..#
# .....@.....# #...........# #..#........# #........#..#
# ...........# #...........# #..#@.......# #.......@#..#
# ...........# #.....@.....# #..#........# #........#..#
# ...........# #..#######..# #..#........# #........#..#
# ...........# #...........# #...........# #...........#
############# ############# ############# #############
WALL_ABOVE = frozenset([DOWN, LEFT, RIGHT, DOWN_LEFT, DOWN_RIGHT])
WALL_BELOW = frozenset([UP, LEFT, RIGHT, UP_LEFT, UP_RIGHT])
WALL_LEFT = frozenset([UP, DOWN, RIGHT, UP_RIGHT, DOWN_RIGHT])
WALL_RIGHT = frozenset([UP, DOWN, LEFT, UP_LEFT, DOWN_LEFT])

INTERSECTIONS = frozenset([TOP_TEE, BOTTOM_TEE, LEFT_TEE, RIGHT_TEE, FOURWAY_INTERSECTION])
HALLWAYS = frozenset([VERTICAL_HALLWAY, HORIZONTAL_HALLWAY])
WALLS = frozenset([WALL_ABOVE, WALL_BELOW, WALL_LEFT, WALL_RIGHT])

# hostility
HOSITLE_TO_PLAYER = 1
