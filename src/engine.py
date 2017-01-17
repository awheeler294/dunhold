import math
import textwrap
import shelve

from utilityClasses import *
from baseClasses import *
from defaultConstants import *


class View:
    FOV_ALGO = 0
    FOV_LIGHT_WALLS = False
    LIMIT_FPS = 60

    FULLSCREEN = True

    FONT = 'fonts/dejavu16x16_gs_tc.png'
    FONT_WIDTH = 16
    FONT_HEIGHT = 16

    SCREEN_OFFSET = 1

    def __init__(self):
        screen_width_px, screen_height_px = libtcod.sys_get_current_resolution()

        libtcod.console_set_custom_font(self.FONT, libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
        # font_size_width, font_size_height = libtcod.sys_get_char_size()

        self.screen_width = (screen_width_px / self.FONT_WIDTH) - self.SCREEN_OFFSET - 1
        self.screen_height = (screen_height_px / self.FONT_HEIGHT) - self.SCREEN_OFFSET

        libtcod.console_init_root(self.screen_width + self.SCREEN_OFFSET, self.screen_height + self.SCREEN_OFFSET,
                                  'Dunhold Station',
                                  self.FULLSCREEN)

        libtcod.sys_set_fps(self.LIMIT_FPS)

        # self.debug_print_centering_marks(step=2,
        #                                  min_x=self.SCREEN_OFFSET, min_y=self.SCREEN_OFFSET,
        #                                  max_x=self.screen_width, max_y=self.screen_height)

        self._con = libtcod.console_new(MAP_WIDTH, MAP_HEIGHT)
        self._bottomPanel = libtcod.console_new(self.screen_width, PANEL_HEIGHT)

        self._fovLightWalls = self.FOV_LIGHT_WALLS
        self._fovAlgorithm = self.FOV_ALGO

        libtcod.console_clear(self._con)  # unexplored areas start black (which is the default background color)

        self.msgX = MSG_X

        self._fov_map = None

    @property
    def fov_map(self):
        return self._fov_map

    @fov_map.setter
    def fov_map(self, value):
        self._fov_map = value

    @property
    def screen_width(self):
        return self._screen_width

    @screen_width.setter
    def screen_width(self, width):
        self._screen_width = width

    @property
    def screen_height(self):
        return self._screen_height

    @screen_height.setter
    def screen_height(self, height):
        self._screen_height = height

    @staticmethod
    def debug_print_centering_marks(console=0, mark='*', step=1, min_x=0, min_y=0, max_x=0, max_y=0):
        for x in range(0, max_x, step):

            libtcod.console_print(console,
                                  min_x + x, min_y + x,
                                  mark)
            libtcod.console_print(console,
                                  max_x - x, min_y + x,
                                  mark)

            libtcod.console_print(console,
                                  max_x - x, max_y - x,
                                  mark)
            libtcod.console_print(console,
                                  min_x + x, max_y - x,
                                  mark)

        libtcod.console_flush()

    def main_menu(self):
        main_menu_width = SCREEN_WIDTH
        main_menu_height = self.screen_height

        mm_center_x = main_menu_width / 2
        mm_center_y = main_menu_height / 2

        main_menu_x = (self.screen_width / 2) - mm_center_x
        main_menu_y = (self.screen_height / 2) - mm_center_y

        background_img = libtcod.image_load('spacestation3.png')
        bg_img_size = libtcod.image_get_size(background_img)

        bg_img_width = bg_img_size[0] / self.FONT_WIDTH
        bg_img_height = bg_img_size[1] / self.FONT_HEIGHT

        bg_image_center_x = bg_img_width / 2
        bg_image_center_y = bg_img_height / 2

        bg_image_x = bg_image_center_x
        bg_image_y = bg_image_center_y

        main_menu = libtcod.console_new(main_menu_width, main_menu_height)

        while not is_window_closed():
            # show the background image, at twice the regular console resolution
            libtcod.image_blit_2x(background_img, main_menu, bg_image_x, bg_image_y)

            # show the game's title, and some credits!
            libtcod.console_set_default_foreground(main_menu, libtcod.light_yellow)

            libtcod.console_print_ex(main_menu,
                                     mm_center_x, mm_center_y - 8,
                                     libtcod.BKGND_NONE, libtcod.CENTER, 'DUNHOLD STATION')

            libtcod.console_print_ex(main_menu,
                                     mm_center_x, mm_center_y + 10,
                                     libtcod.BKGND_NONE, libtcod.CENTER, 'By Andrew Wheeler')

            # self.debug_print_centering_marks(main_menu,
            #                                  step=1,
            #                                  min_x=0, min_y=0,
            #                                  max_x=main_menu_width, max_y=main_menu_height)

            libtcod.console_blit(main_menu,
                                 0, 0,
                                 0, 0,
                                 0,
                                 main_menu_x, main_menu_y,
                                 1.0, 1.0)

            # show options and wait for the player's choice
            options = [('n', 'Play a new game'), ('c', 'Continue last game'), ('q', 'Quit')]
            selection = self.menu('', options, 24)
            if selection == 'n' or selection == 'c' or selection == 'q':
                return selection

    def menu(self, header, options, width):
        """display a menu.
           @param header: string to display as the menu header
           @param options: list of menu options to display containing the index and option pairs as tuples
           @param width: integer width of the menu"""

        if len(options) > 26:
            raise ValueError('Cannot have a menu with more than 26 options.')

        indexes = []

        # calculate total height for the header (after auto-wrap) and one line per option
        header_height = libtcod.console_get_height_rect(self._con, 0, 0, width, self.screen_height, header)
        if header == '':
            header_height = 0
        height = len(options) + header_height

        # create an off-screen console that represents the menu's window
        window = libtcod.console_new(width, height)

        # print the header, with auto-wrap
        libtcod.console_set_default_foreground(window, libtcod.white)
        libtcod.console_print_rect_ex(window,
                                      0, 0,
                                      width, height,
                                      libtcod.BKGND_NONE, libtcod.LEFT,
                                      header)

        # print all the options
        y = header_height
        for index, option in options:
            indexes.append(index)
            text = '(' + index + ') ' + option
            libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
            y += 1

        # blit the contents of "window" to the root console
        x = (self.screen_width / 2) - (width / 2)
        y = (self.screen_height / 2) - (height / 2)
        libtcod.console_blit(window,
                             0, 0,
                             0, 0,
                             0,
                             x, y,
                             1.0, 0.7)

        # present the root console to the player and wait for a key-press
        libtcod.console_flush()
        key = libtcod.console_wait_for_keypress(True)

        if key.vk == libtcod.KEY_ENTER and key.lalt:  # (special case) Alt+Enter: toggle fullscreen
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen)

        # convert the ASCII code to an index; if it corresponds to an option, return it
        index = chr(key.c)
        if index in indexes:
            return index
        return None

    def msgbox(self, text, width=50):
        self.menu(text, [], width)  # use menu() as a sort of "message box"

    def render_all(self, current_level, player, mouse):
        objects = current_level.objects
        level_map = current_level.map
        # draw all objects in the list, except the player. we want it to
        # always appear over all other objects! so it's drawn later.
        for obj in objects:
            self.draw_object(obj, self._fov_map, level_map)

        self.draw_object(player, self._fov_map, level_map)

        # blit the contents of "con" to the root console
        libtcod.console_blit(self._con,
                             0, 0,
                             MAP_WIDTH, MAP_HEIGHT,
                             0,
                             10, 10,
                             0.5)

        # prepare to render the GUI panel
        libtcod.console_set_default_background(self._bottomPanel, libtcod.black)
        libtcod.console_clear(self._bottomPanel)
        '''
        # print the game messages, one line at a time
        y = 1
        for (line, color) in game_msgs:
           libtcod.console_set_default_foreground(self._bottomPanel, color)
           libtcod.console_print_ex(self._bottomPanel, self.msgX, y, libtcod.BKGND_NONE, libtcod.LEFT,line)
           y += 1
        '''
        # show the player's stats
        self.render_bar(self._bottomPanel, 1, 1, BAR_WIDTH, 'HP', player.combatComponent.hp,
                        player.combatComponent.max_hp,
                        libtcod.light_red, libtcod.darker_red)
        libtcod.console_print_ex(self._bottomPanel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, str(current_level.name))
        '''
        # display names of objects under the mouse
        libtcod.console_set_default_foreground(self._bottomPanel, libtcod.light_gray)
        libtcod.console_print_ex(self._bottomPanel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse(objects, self._fov_map, mouse))
        '''
        # blit the contents of "bottomPanel" to the root console
        libtcod.console_blit(self._bottomPanel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)

        libtcod.console_flush()

    @staticmethod
    def render_bar(panel, x, y, total_width, name, value, maximum, bar_color, back_color):
        # render a bar (HP, experience, etc). first calculate the width of the bar
        bar_width = int(float(value) / maximum * total_width)

        # render the background first
        libtcod.console_set_default_background(panel, back_color)
        libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

        # now render the bar on top
        libtcod.console_set_default_background(panel, bar_color)
        if bar_width > 0:
            libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

        # finally, some centered text with the values
        libtcod.console_set_default_foreground(panel, libtcod.white)
        libtcod.console_print_ex(panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
                                 name + ': ' + str(value) + '/' + str(maximum))

    def fov_redraw(self, fov_map, map_height, map_width, level_map):
        # go through all tiles, and set their background color according to the FOV
        for y in range(map_height):
            for x in range(map_width):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                if not visible:
                    # if it's not visible right now, the player can only see it if it's explored
                    if level_map[x][y].explored:
                        libtcod.console_set_char_background(self._con, x, y, level_map[x][y].dark_color,
                                                            libtcod.BKGND_SET)
                else:
                    # it's visible
                    libtcod.console_set_char_background(self._con, x, y, level_map[x][y].tile_color, libtcod.BKGND_SET)
                    # since it's visible, explore it
                    level_map[x][y].explored = True

    def draw_object(self, obj, fov_map, level_map):
        # only show if it's visible to the player; or it's set to "always visible" and on an explored tile

        # fov = libtcod.map_is_in_fov(fov_map, obj.x, obj.y)
        # always_visible = obj.always_visible
        # explored = level_map[obj.x][obj.y].explored

        if (libtcod.map_is_in_fov(fov_map, obj.x, obj.y) or
                (obj.always_visible and level_map[obj.x][obj.y].explored)):
            # set the color and then draw the character that represents this object at its position
            libtcod.console_set_default_foreground(self._con, obj.color)
            libtcod.console_put_char(self._con, obj.x, obj.y, obj.char, libtcod.BKGND_NONE)

    def clear_object(self, obj):
        # erase the character that represents this object
        libtcod.console_put_char(self._con, obj.x, obj.y, ' ', libtcod.BKGND_NONE)

    @staticmethod
    def get_names_under_mouse(objects, fov_map, mouse):
        # return a string with the names of all objects under the mouse

        (x, y) = (mouse.cx, mouse.cy)

        # create a list with the names of all objects at the mouse's coordinates and in FOV
        names = [obj.name for obj in objects
                 if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]

        names = ', '.join(names)  # join the names, separated by commas
        return names.capitalize()


class Controller:
    def __init__(self):
        self.initialize_game()

    def initialize_game(self):
        self._game_state = {'initialize': True, 'playing': False}

        self._view = View()
        self._model = Model()

        self._fov_recompute = True

        self.display_main_menu()

    def display_main_menu(self):
        menu_selection = self._view.main_menu()
        print " Menu Selection: " + str(menu_selection)
        if menu_selection is 'n':
            self.new_game()

        elif menu_selection is 'c':
            # load game
            try:
                pass
            except:
                self._view.msgbox('\n No saved game to load.\n', 24)

        elif menu_selection is 'q':
            # quit
            self.quit()

    def new_game(self):
        self._model.create_world()
        # self._master_object_list = self.generate_object_list()
        self._game_state['initialize'] = False
        self._game_state['playing'] = True
        self.play_game()

    @staticmethod
    def quit():
        raise QuitException

    def play_game(self):
        # print " I'm alive!\n"

        # main game loop
        player_action = None
        initialize_safe_move = False
        # safe_move = False

        mouse = libtcod.Mouse()
        key = libtcod.Key()

        # main loop
        while not libtcod.console_is_window_closed():
            libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

            # render the screen
            current_level = self._model.current_level
            player = self._model.player

            if player.mobComponent.fov_recompute:
                player.mobComponent.recompute_fov(current_level.mapHeight, current_level.mapWidth)
                self._view.fov_redraw(player.mobComponent.fov_map, current_level.mapHeight, current_level.mapWidth,
                                      current_level.map)

            current_level = self._model.current_level
            self._view.render_all(current_level, player, mouse)

            # level up if needed
            # check_level_up()

            # erase all objects at their old locations, before they move
            for obj in current_level.objects:
                if not hasattr(obj, 'is_terrain'):
                    self._view.clear_object(obj)
            self._view.clear_object(player)

            # handle keys and exit game if needed
            if initialize_safe_move:
                direction = self.get_movement_keys(key)
                if direction is not False:
                    dx, dy = direction
                    player.mobComponent.safe_move_dx = dx
                    player.mobComponent.safe_move_dy = dy
                    player_action = self._model.move_or_attack(player, dx, dy)
                    if not self._model.is_hostile_mob_in_fov(player):
                        player.mobComponent.possible_moves = self._model.get_possible_moves(player)
                        player.mobComponent.safe_move = True
                    initialize_safe_move = False
            elif player.mobComponent.safe_move == True:
                player_action = self.safe_move(player)
            else:
                player_action = self.handle_keypress(key)
                if player_action == 'safe_move':
                    initialize_safe_move = True
                if player_action == 'exit':
                    self.save_game()
                    break

            if player_action == 'didnt-take-turn' or player_action == 'blocked' or player_action == 'cancel-safe-move':
                player.mobComponent.safe_move = False
            '''
            #let monsters take their turn
            if game_state == 'playing' and player_action != 'didnt-take-turn':
               for object in objects:
                  if object.ai:
                     object.ai.take_turn()
            '''

    def handle_keypress(self, key):

        if key.vk == libtcod.KEY_ENTER and key.lalt:
            # Alt+Enter: toggle fullscreen
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        elif key.vk == libtcod.KEY_ESCAPE:
            # self._game_state['playing']
            self.quit()  # exit game

        player = self._model.player

        if self._game_state['playing']:
            direction = self.get_movement_keys(key)
            if direction is not False:
                dx, dy = direction
                return self._model.move_or_attack(player, dx, dy)
            else:
                # test for other keys
                key_char = chr(key.c)

                if key_char == 'w':
                    return 'safe_move'
                '''
                if key_char == 'g':
                   #pick up an item
                   for object in objects:  #look for an item in the player's tile
                      if object.x == player.x and object.y == player.y and object.item:
                         object.item.pick_up()
                         break

                if key_char == 'i':
                   #show the inventory; if an item is selected, use it
                   selected_item = inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
                   if selected_item is not None:
                      selected_item.use()

                if key_char == 'd':
                   #show the inventory; if an item is selected, drop it
                   selected_item = inventory_menu('Press the key next to an item to drop it, or any other to cancel.\n')
                   if selected_item is not None:
                      selected_item.drop()

                if key_char == 'c':
                   #show character information
                   level_up_xp = LEVEL_UP_BASE + player.level * LEVEL_UP_FACTOR
                   msgbox('Character Information\n\nLevel: ' + str(player.level) + '\nExperience: ' + str(player.fighter.xp) +
                         '\nExperience to level up: ' + str(level_up_xp) + '\n\nMaximum HP: ' + str(player.fighter.max_hp) +
                         '\nAttack: ' + str(player.fighter.power) + '\nDefense: ' + str(player.fighter.defense), CHARACTER_SCREEN_WIDTH)

                if key_char == '<':
                   #go down stairs, if the player is on them
                   if stairs.x == player.x and stairs.y == player.y:
                      next_level()
                '''
                return 'didnt-take-turn'

    @staticmethod
    def get_movement_keys(key):

        # movement keys
        if key.vk == libtcod.KEY_UP or key.vk == libtcod.KEY_KP8:
            return UP
        elif key.vk == libtcod.KEY_DOWN or key.vk == libtcod.KEY_KP2:
            return DOWN
        elif key.vk == libtcod.KEY_LEFT or key.vk == libtcod.KEY_KP4:
            return LEFT
        elif key.vk == libtcod.KEY_RIGHT or key.vk == libtcod.KEY_KP6:
            return RIGHT
        elif key.vk == libtcod.KEY_HOME or key.vk == libtcod.KEY_KP7:
            return UP_LEFT
        elif key.vk == libtcod.KEY_PAGEUP or key.vk == libtcod.KEY_KP9:
            return UP_RIGHT
        elif key.vk == libtcod.KEY_END or key.vk == libtcod.KEY_KP1:
            return DOWN_LEFT
        elif key.vk == libtcod.KEY_PAGEDOWN or key.vk == libtcod.KEY_KP3:
            return DOWN_RIGHT
        elif key.vk == libtcod.KEY_KP5 or key.c == '.':
            return HERE
        else:
            return False

    def safe_move(self, mob):
        # if the path is blocked or hostile mobs are visible:
        # make a normal move in the direction of travel

        # otherwise:
        # determine how many possible moves the mob has

        # if the direction of travel is clear, and no hostile mobs are visible,
        # and the number of possible moves remains the same:
        # move in the direction of travel

        dx = mob.mobComponent.safe_move_dx
        dy = mob.mobComponent.safe_move_dy

        x = mob.x + dx
        y = mob.y + dy

        if self._model.is_blocked(x, y):
            return 'didnt-take-turn'

        if self._model.is_hostile_mob_in_fov(mob):
            return 'didnt-take-turn'

        if self._model.is_item_at_location(x, y):
            self._model.move_or_attack(mob, dx, dy)
            return 'cancel-safe-move'

        possible_moves = self._model.get_possible_moves(mob)
        if possible_moves in INTERSECTIONS:
            return 'cancel-safe-move'
        player_action = self._model.move_or_attack(mob, dx, dy)
        new_moves = self._model.get_possible_moves(mob)
        elbow_moves = self._model.is_elbow(mob)
        if elbow_moves is not False:
            assert (len(elbow_moves) == 2), ""
            back_dx = dx * -1
            back_dy = dy * -1
            move1, move2 = elbow_moves
            x1, y1 = move1
            x2, y2 = move2
            if x1 == back_dx and y1 == back_dy:
                mob.mobComponent.safe_move_dx = x2
                mob.mobComponent.safe_move_dy = y2
            elif x2 == back_dx and y2 == back_dy:
                mob.mobComponent.safe_move_dx = x1
                mob.mobComponent.safe_move_dy = y1
            mob.mobComponent.possible_moves = new_moves
            return ''
        if possible_moves != mob.mobComponent.possible_moves:
            if new_moves in HALLWAYS or new_moves in WALLS:
                mob.mobComponent.possible_moves = new_moves
            else:
                return 'cancel-safe-move'

        return player_action

    def save_game(self):
        pass


class Model:
    def __init__(self):
        self.initialize()

    def initialize(self):
        self._levels = []

    @property
    def current_level(self):
        return self._currentLevel

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, value):
        self._player = value

    def create_world(self):
        level_name = len(self._levels) + 1

        new_level = self.make_new_level(level_name)
        self._levels.append(new_level)
        self._currentLevel = new_level

        self._player = GameObject(new_level.levelEntrance.x, new_level.levelEntrance.y, '@', 'player', libtcod.yellow,
                                  blocks=True)
        self._player.playerComponent = PlayerComponent(self._player, 100, 0, 2, 0, death_function=None)

        # <PLACEHOLDER>
        self._player.seightRadius = SEIGHT_RADIUS
        # </PLACEHOLDER>

        self._player.mobComponent.initialize_fov(new_level.mapHeight, new_level.mapWidth, new_level.map)

    @staticmethod
    def make_new_level(name):
        new_level = Level(name)
        new_level.make_map()
        return new_level

    def initialize_fov(self):

        # create the FOV map, according to the generated map
        map_height = self._currentLevel.mapHeight
        map_width = self._currentLevel.mapWidth
        fov_map = libtcod.map_new(map_width, map_height)
        level_map = self._currentLevel.map
        for y in range(map_height):
            for x in range(map_width):
                libtcod.map_set_properties(fov_map, x, y, not level_map[x][y].block_sight, not level_map[x][y].blocks)

        return fov_map

    def move_or_attack(self, mob, dx, dy):
        objects = self.current_level.objects

        # the coordinates the mob is moving to/attacking
        x = mob.x + dx
        y = mob.y + dy

        # try to find an attackable object there
        target = None
        for obj in objects:
            if obj.x == x and obj.y == y:
                if hasattr(obj, 'combatComponent'):
                    target = obj
                    break

        # attack if target found, move otherwise
        if target is not None:
            mob.combatComponent.attack(target)
        else:
            if self.is_blocked(x, y):
                return 'blocked'
            mob.mobilityComponent.move(dx, dy)
            if dx != 0 or dy != 0:
                mob.mobComponent.fov_recompute = True

    def is_blocked(self, x, y):
        return self.current_level.is_blocked(x, y)

    def is_item_at_location(self, x, y):
        return False

    def is_hostile_mob_in_fov(self, mob):
        for obj in self._currentLevel.objects:
            if hasattr(obj, "mobComponent"):
                if mob.is_hostile(obj):
                    return True
        return False

    def get_num_possible_moves(self, mob):
        return len(self.get_possible_moves(mob))

    def get_possible_moves(self, mob):
        moves = []
        for offset in SURROUNDING_OFFSETS:
            dx, dy = offset
            x = mob.x + dx
            y = mob.y + dy
            if not self.is_blocked(x, y):
                moves.append((dx, dy))
        return set(moves)

    def is_elbow(self, mob):
        # determine if location is part of an elbow turn
        ############# ############# ############# #############
        # ...........# #...........# #...........# #...........#
        # ..#######..# #..#.#......# #..#######..# #......#.#..#
        # ..#@.......# #..#.#......# #.......@#..# #......#.#..#
        # ..#.#####..# #..#.#####..# #..#####.#..# #..#####.#..#
        # ..#.#......# #..#@.......# #......#.#..# #.......@#..#
        # ..#.#......# #..#######..# #......#.#..# #..#######..#
        # ...........# #...........# #...........# #...........#
        ############# ############# ############# #############

        possible_moves = self.get_possible_moves(mob)
        if possible_moves == LEFT_TOP_ELBOW:
            return LEFT_TOP_ELBOW
        if possible_moves == LEFT_BOTTOM_ELBOW:
            return LEFT_BOTTOM_ELBOW
        if possible_moves == RIGHT_TOP_ELBOW:
            return RIGHT_TOP_ELBOW
        if possible_moves == RIGHT_BOTTOM_ELBOW:
            return RIGHT_BOTTOM_ELBOW
        return False
