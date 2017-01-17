#!/usr/bin/env python

import math
import textwrap
import libtcodpy as libtcod

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 56

MAP_WIDTH = 80
MAP_HEIGHT = 46

#LIMIT_FPS = 20

#parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30

MAX_ROOM_MONSTERS = 3
MAX_ROOM_ITEMS = 2

FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = True  #light walls or not
SIGHT_RADIUS = 10

#sizes and coordinates relevant for the GUI
MSG_X = 2
MSG_WIDTH = SCREEN_WIDTH - MSG_X - 2
MSG_HEIGHT = 4

BAR_WIDTH = 20
STAT_PANEL_HEIGHT = 4
STAT_PANEL_Y = SCREEN_HEIGHT - STAT_PANEL_HEIGHT - 1

color_dark_wall = libtcod.dark_gray
color_background = libtcod.black
color_light_wall = libtcod.white
color_dark_ground = libtcod.dark_gray
color_light_ground = libtcod.light_gray

class Tile:
   #a tile of the map and its properties
   def __init__(self, passable, character = None, block_sight = None, light_color = None):
      self.passable = passable
      self.explored = False

      if character is None:
         character = '#'
      self.character = character

      if light_color is None:
         light_color = color_light_wall
      self.light_color = light_color

      self.dark_color = light_color * 0.5

      #by default, if a tile is blocked, it also blocks sight
      if block_sight is None:
         block_sight = not passable
      self.block_sight = block_sight


class Rect:
   #a rectangle on the map. used to characterize a room.
   def __init__(self, x, y, w, h):
      self.x1 = x
      self.y1 = y
      self.x2 = x + w
      self.y2 = y + h

   def center(self):
      center_x = (self.x1 + self.x2) / 2
      center_y = (self.y1 + self.y2) / 2
      return (center_x, center_y)

   def intersect(self, other):
      #returns true if this rectangle intersects with another one
      return (self.x1 <= other.x2 and self.x2 >= other.x1 and
         self.y1 <= other.y2 and self.y2 >= other.y1)


class Object:
   #this is a generic object: the player, a monster, an item, the stairs...
   #it's always represented by a character on screen.
   def __init__(self, x, y, char, name, color, blocks=False, fighter=None, ai=None, item=None):
      self.x = x
      self.y = y
      self.char = char
      self.name = name
      self.color = color
      self.blocks = blocks

      self.fighter = fighter
      if self.fighter:  #let the fighter component know who owns it
         self.fighter.owner = self

      self.ai = ai
      if self.ai:  #let the AI component know who owns it
         self.ai.owner = self

      self.item = item
      if self.item:  #let the Item component know who owns it
         self.item.owner = self

   def move(self, dx, dy):
      if not is_blocked(self.x + dx, self.y + dy):
         #move by the given amount
         self.x += dx
         self.y += dy

   def move_towards(self, target_x, target_y):
      #vector from this object to the target, and distance
      dx = target_x - self.x
      dy = target_y - self.y
      distance = math.sqrt(dx ** 2 + dy ** 2)

      #normalize it to length 1 (preserving direction), then round it and
      #convert to integer so the movement is restricted to the map grid
      dx = int(round(dx / distance))
      dy = int(round(dy / distance))
      self.move(dx, dy)

   def distance_to(self, other):
      #return the distance to another object
      dx = other.x - self.x
      dy = other.y - self.y
      return math.sqrt(dx ** 2 + dy ** 2)

   def send_to_back(self):
      #make this object be drawn first, so all others appear above it if they're in the same tile.
      global objects
      objects.remove(self)
      objects.insert(0, self)


class Fighter:
   #combat-related properties and methods (monster, player, NPC).
   def __init__(self, hp, defense, power, death_function=None):
      self.max_hp = hp
      self.hp = hp
      self.defense = defense
      self.power = power
      self.death_function = death_function

   def attack(self, target):
      #a simple formula for attack damage
      damage = self.power - target.fighter.defense

      if damage > 0:
         #make the target take some damage
         message(self.owner.name + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.')
         target.fighter.take_damage(damage)
      else:
         message(self.owner.name + ' attacks ' + target.name + ' but it has no effect!')

   def take_damage(self, damage):
      #apply damage if possible
      if damage > 0:
         self.hp -= damage

         #check for death. if there's a death function, call it
         if self.hp <= 0:
            if self.death_function is not None:
               self.death_function(self.owner)


class BasicMonster:
   #AI for a basic monster.
   def take_turn(self):
      #a basic monster takes its turn. if you can see it, it can see you
      monster = self.owner
      if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):

         #move towards player if far away
         if monster.distance_to(player) >= 2:
            monster.move_towards(player.x, player.y)

         #close enough, attack! (if the player is still alive.)
         elif player.fighter.hp > 0:
            monster.fighter.attack(player)


class Item:
    #an item that can be picked up and used.
    def pick_up(self):
        #add to the player's inventory and remove from the map
        if len(inventory) >= 26:
            message('Your inventory is full, cannot pick up ' + self.owner.name + '.', libtcod.red)
        else:
            inventory.append(self.owner)
            objects.remove(self.owner)
            message('You picked up a ' + self.owner.name + '!', libtcod.green)


def player_death(player):
   #the game ended!
   global game_state
   message('You died!', libtcod.red)
   game_state = 'dead'

   #for added effect, transform the player into a corpse!
   player.char = '%'
   #player.color = libtcod.dark_red


def monster_death(monster):
   #transform it into a nasty corpse! it doesn't block, can't be
   #attacked and doesn't move
   message(monster.name + ' dies!', libtcod.orange)
   monster.char = '%'
   #monster.color = libtcod.dark_red
   monster.blocks = False
   monster.fighter = None
   monster.ai = None
   monster.name = 'remains of ' + monster.name
   monster.send_to_back()


def is_blocked(x, y):
    #first test the map tile
    if not map[x][y].passable:
        return True

    #now check for any blocking objects
    for object in objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False


def place_objects(room):
   #choose random number of monsters
   num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)

   for i in range(num_monsters):
      #choose random spot for this monster
      x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
      y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

      #only place it if the tile is not blocked
      if not is_blocked(x, y):
         if libtcod.random_get_int(0, 0, 100) < 80:  #80% chance of getting an orc
            #create an orc
            fighter_component = Fighter(hp=10, defense=0, power=3, death_function=monster_death)
            ai_component = BasicMonster()

            monster = Object(x, y, 'o', 'orc', libtcod.desaturated_green,
              blocks=True, fighter=fighter_component, ai=ai_component)
         else:
            #create a troll
            fighter_component = Fighter(hp=16, defense=1, power=4, death_function=monster_death)
            ai_component = BasicMonster()

            monster = Object(x, y, 'T', 'troll', libtcod.darker_green,
              blocks=True, fighter=fighter_component, ai=ai_component)

         objects.append(monster)

   #choose random number of items
   num_items = libtcod.random_get_int(0, 0, MAX_ROOM_ITEMS)

   for i in range(num_items):
      #choose random spot for this item
      x = libtcod.random_get_int(0, room.x1 + 1, room.x2 - 1)
      y = libtcod.random_get_int(0, room.y1 + 1, room.y2 - 1)

      #only place it if the tile is not blocked
      if not is_blocked(x, y):
         #create a healing potion
         item_component = Item()
         item = Object(x, y, '!', 'healing potion', libtcod.violet, item=item_component)

         objects.append(item)
         item.send_to_back()  #items appear below other objects


def make_tile_floor(tile):
   tile.passable = True
   tile.block_sight = False
   tile.character = '.'
   tile.light_color = color_light_ground


def create_room(room):
   global map
   #go through the tiles in the rectangle and make them passable
   for x in range(room.x1 + 1, room.x2):
      for y in range(room.y1 + 1, room.y2):
         make_tile_floor(map[x][y])


def create_h_tunnel(x1, x2, y):
   global map
   #horizontal tunnel. min() and max() are used in case x1>x2
   for x in range(min(x1, x2), max(x1, x2) + 1):
      make_tile_floor(map[x][y])

def create_v_tunnel(y1, y2, x):
   global map
   #vertical tunnel
   for y in range(min(y1, y2), max(y1, y2) + 1):
      make_tile_floor(map[x][y])


def make_map():
   global map, player

   #fill map with impassable tiles
   map = [[ Tile(False)
      for y in range(MAP_HEIGHT) ]
         for x in range(MAP_WIDTH) ]

   rooms = []
   num_rooms = 0

   for r in range(MAX_ROOMS):
      #random width and height
      w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
      h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
      #random position without going out of the boundaries of the map
      x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
      y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)

      #"Rect" class makes rectangles easier to work with
      new_room = Rect(x, y, w, h)

      #run through the other rooms and see if they intersect with this one
      failed = False
      for other_room in rooms:
         if new_room.intersect(other_room):
            failed = True
            break

      if not failed:
         #this means there are no intersections, so this room is valid

         #"paint" it to the map's tiles
         create_room(new_room)

         #add some contents to this room, such as monsters
         place_objects(new_room)

         #center coordinates of new room, will be useful later
         (new_x, new_y) = new_room.center()

         if num_rooms == 0:
            #this is the first room, where the player starts at
            player.x = new_x
            player.y = new_y
         else:
            #all rooms after the first:
            #connect it to the previous room with a tunnel

            #center coordinates of previous room
            (prev_x, prev_y) = rooms[num_rooms-1].center()

            #draw a coin (random number that is either 0 or 1)
            if libtcod.random_get_int(0, 0, 1) == 1:
               #first move horizontally, then vertically
               create_h_tunnel(prev_x, new_x, prev_y)
               create_v_tunnel(prev_y, new_y, new_x)
            else:
               #first move vertically, then horizontally
               create_v_tunnel(prev_y, new_y, prev_x)
               create_h_tunnel(prev_x, new_x, new_y)

         #finally, append the new room to the list
         rooms.append(new_room)
         num_rooms += 1


def message(new_msg, color = libtcod.white):
   #split the message if necessary, among multiple lines
   new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)

   for line in new_msg_lines:
      #if the buffer is full, remove the first line to make room for the new one
      if len(game_msgs) == MSG_HEIGHT - 1:
         del game_msgs[0]

      #add the new line as a tuple, with the text and the color
      game_msgs.append( (line, color) )


def render_bar(x, y, total_width, name, value, maximum, bar_color, back_color):
   #render a bar (HP, experience, etc). first calculate the width of the bar
   bar_width = int(float(value) / maximum * total_width)

   #render the background first
   libtcod.console_set_default_background(stat_panel, back_color)
   libtcod.console_rect(stat_panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

   #now render the bar on top
   libtcod.console_set_default_background(stat_panel, bar_color)
   if bar_width > 0:
      libtcod.console_rect(stat_panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

   #finally, some centered text with the values
   libtcod.console_set_default_foreground(stat_panel, libtcod.white)
   libtcod.console_print_ex(stat_panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER, name + ': ' + str(value) + '/' + str(maximum))


def get_names_under_mouse():
   global mouse

   #return a string with the names of all objects under the mouse
   (x, y) = (mouse.cx, mouse.cy)

   #create a list with the names of all objects at the mouse's coordinates and in FOV
   names = [obj.name for obj in objects
      if obj.x == x and obj.y == y and libtcod.map_is_in_fov(fov_map, obj.x, obj.y)]

   names = ', '.join(names)  #join the names, separated by commas

   return names.capitalize()


def render_all():
   global fov_map, color_dark_wall, color_light_wall
   global color_dark_ground, color_light_ground, color_background
   global fov_recompute

   #libtcod.console_clear(con)

   if fov_recompute:
      #recompute FOV if needed (the player moved or something)
      fov_recompute = False
      libtcod.map_compute_fov(fov_map, player.x, player.y, SIGHT_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)

      for y in range(MAP_HEIGHT):
         for x in range(MAP_WIDTH):
            visible = libtcod.map_is_in_fov(fov_map, x, y)
            tile = map[x][y]
            if not visible:
               #it's out of the player's FOV
               #if it's not visible right now, the player can only see it if it's explored
               if tile.explored:
                  libtcod.console_put_char_ex(con, x, y, tile.character, tile.dark_color, color_background )
            else:
               #it's visible
               libtcod.console_put_char_ex(con, x, y, tile.character, tile.light_color, color_background )
               tile.explored = True

   for obj in objects:
      if libtcod.map_is_in_fov(fov_map, obj.x, obj.y):
         if obj != player:
            libtcod.console_set_default_foreground(con, obj.color)
            libtcod.console_put_char(con, obj.x, obj.y, obj.char, libtcod.BKGND_NONE)

   libtcod.console_set_default_foreground(con, player.color)
   libtcod.console_put_char(con, player.x, player.y, player.char, libtcod.BKGND_NONE)

   libtcod.console_blit(con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, MSG_HEIGHT + 1)

   #prepare to render the GUI stat_panel
   libtcod.console_set_default_background(stat_panel, libtcod.black)
   libtcod.console_clear(stat_panel)
   libtcod.console_clear(msg_panel)

   #print the game messages, one line at a time
   y = 1
   for (line, color) in game_msgs:
      libtcod.console_set_default_foreground(msg_panel, color)
      libtcod.console_print_ex(msg_panel, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
      y += 1

   #show the player's stats
   render_bar(1, 1, BAR_WIDTH, 'HP', player.fighter.hp, player.fighter.max_hp, libtcod.light_red, libtcod.darker_red)

   #display names of objects under the mouse
   libtcod.console_set_default_foreground(stat_panel, libtcod.light_gray)
   libtcod.console_print_ex(stat_panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, get_names_under_mouse())

   #blit the contents of "stat_panel" to the root console
   libtcod.console_blit(stat_panel, 0, 0, SCREEN_WIDTH, STAT_PANEL_HEIGHT, 0, 0, STAT_PANEL_Y)

   #blit the contents of "msg_panel" to the root console
   libtcod.console_blit(msg_panel, 0, 0, SCREEN_WIDTH, STAT_PANEL_HEIGHT, 0, MSG_X , 0)


def player_move_or_attack(dx, dy):
   global fov_recompute

   #the coordinates the player is moving to/attacking
   x = player.x + dx
   y = player.y + dy

   #try to find an attackable object there
   target = None
   for object in objects:
      if object.fighter and object.x == x and object.y == y:
         target = object
         break

   #attack if target found, move otherwise
   if target is not None:
      player.fighter.attack(target)
   else:
      player.move(dx, dy)

   fov_recompute = True


def handle_keys():
   global player, fov_recompute

   global key

   if key.vk == libtcod.KEY_ENTER and (key.lalt or key.ralt):
      #Alt+Enter: toggle fullscreen
      libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

   elif key.vk == libtcod.KEY_ESCAPE:
      return 'exit'  #exit game

   if game_state == 'playing':
      #movement keys
      if key.vk == (libtcod.KEY_8) or key.vk == (libtcod.KEY_KP8) or key.vk == (libtcod.KEY_UP):
         player_move_or_attack(0, -1)

      elif key.vk == (libtcod.KEY_2) or key.vk == (libtcod.KEY_KP2) or key.vk == (libtcod.KEY_DOWN):
         player_move_or_attack(0, 1)

      elif key.vk == (libtcod.KEY_4) or key.vk == (libtcod.KEY_KP4) or key.vk == (libtcod.KEY_LEFT):
         player_move_or_attack(-1, 0)

      elif key.vk == (libtcod.KEY_6) or key.vk == (libtcod.KEY_KP6) or key.vk == (libtcod.KEY_RIGHT):
         player_move_or_attack(1, 0)

      elif key.vk == (libtcod.KEY_7) or key.vk == (libtcod.KEY_KP7):
         player_move_or_attack(-1, -1)

      elif key.vk == (libtcod.KEY_9) or key.vk == (libtcod.KEY_KP9):
         player_move_or_attack(1, -1)

      elif key.vk == (libtcod.KEY_1) or key.vk == (libtcod.KEY_KP1):
         player_move_or_attack(-1, 1)

      elif key.vk == (libtcod.KEY_3) or key.vk == (libtcod.KEY_KP3):
         player_move_or_attack(1, 1)

      elif key.vk == (libtcod.KEY_5) or key.vk == (libtcod.KEY_KP5):
         pass

      else:
         #test for other keys
         key_char = chr(key.c)

         if key_char == ',':
             #pick up an item
             for object in objects:  #look for an item in the player's tile
                 if object.x == player.x and object.y == player.y and object.item:
                     object.item.pick_up()
                     break

         else:
            return 'didnt-take-turn'


#############################################
# Initialization & Main Loop
#############################################

libtcod.console_set_custom_font('fonts/dejavu12x12_gs_tc.png', libtcod.FONT_TYPE_GRAYSCALE | libtcod.FONT_LAYOUT_TCOD)

libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'roguebasin python/libtcod tutorial', False)

con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
stat_panel = libtcod.console_new(SCREEN_WIDTH, STAT_PANEL_HEIGHT)
msg_panel = libtcod.console_new(MSG_WIDTH, MSG_HEIGHT)

#create object representing the player
fighter_component = Fighter(hp=30, defense=2, power=5, death_function=player_death)
player = Object(0, 0, '@', 'player', libtcod.white, blocks=True, fighter=fighter_component)

objects = [player]

inventory = []

#create the list of game messages and their colors, starts empty
game_msgs = []

#generate map (at this point it's not drawn to the screen)
make_map()

#create the FOV map, according to the generated map
fov_map = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
for y in range(MAP_HEIGHT):
   for x in range(MAP_WIDTH):
      libtcod.map_set_properties(fov_map, x, y, not map[x][y].block_sight, map[x][y].passable)

fov_recompute = True

game_state = 'playing'
player_action = None

mouse = libtcod.Mouse()
key = libtcod.Key()

#a warm welcoming message!
#message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)

message('Welcome stranger!', libtcod.red)

while not libtcod.console_is_window_closed():

   libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE,key,mouse)

   libtcod.console_set_default_foreground(con, libtcod.white)

   render_all()

   libtcod.console_flush()

   #handle keys and exit game if needed
   player_action = handle_keys()
   if player_action == 'exit':
      break

   #let monsters take their turn
   if game_state == 'playing' and player_action != 'didnt-take-turn':
      for object in objects:
         if object.ai:
            object.ai.take_turn()
