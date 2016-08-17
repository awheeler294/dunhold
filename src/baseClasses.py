import math
import random

from components.basic_components import *
from utilityClasses import *
from defaultConstants import *

class GameObject:
   """Base class for all game objects"""
   def __init__(self, x, y, char, name, color, blocks=False, always_visible=False, block_sight = None):
      self.x = x
      self.y = y
      self.char = char
      self.name = name
      self.color = color
      self.blocks = blocks
      self.always_visible = always_visible

   def distance_to_object(self, other):
      #return the distance to another object
      dx = other.x - self.x
      dy = other.y - self.y
      return math.sqrt(dx ** 2 + dy ** 2)

   def distance_to_position(self, x, y):
      #return the distance to some coordinates
      return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)


class Tile(GameObject):
   """GameObject with a tile component, makes up the spaces on the map"""
   def __init__(self, x, y, char, name, color, blocks=False, always_visible=False, block_sight = None):
      GameObject.__init__(self, x, y, char, name, color, blocks, always_visible, block_sight)
      self.tileComponent = TileComponent(self, blocks)
      self.tile_color = color
      self.dark_color = color * 0.5
      self.explored = False


class Level:
   """class contains map data and monster/item data"""
   def __init__(self, name, max_rooms=MAX_ROOMS, min_room_size=ROOM_MIN_SIZE, max_room_size=ROOM_MAX_SIZE, max_room_objects=MAX_ROOM_OBJECTS):
      self.objects = []
      self._wallChar = None
      self._floorChar = None
      self._wallColor = COLOR_LIGHT_WALL
      self._floorColor = COLOR_LIGHT_GROUND
      self._entranceChar = ENTRANCE_CHAR
      self._exitChar = EXIT_CHAR
      self._name = name
      self.mapHeight = MAP_HEIGHT
      self.mapWidth = MAP_WIDTH
      self._maxRoomObjects = max_room_objects
      self._maxRooms = max_rooms
      self._roomMinSize = min_room_size
      self._roomMaxSize = max_room_size

   @property
   def map(self):
       return self._map
   @map.setter
   def map(self, value):
       self._map = value

   @property
   def name(self):
       return self._name
   @name.setter
   def name(self, value):
       self._name = value

   @property
   def levelEntrance(self):
       return self._levelEntrance
   @levelEntrance.setter
   def levelEntrance(self, value):
       self._levelEntrance = value

   @property
   def levelExit(self):
       return self._levelExit
   @levelExit.setter
   def levelExit(self, value):
       self._levelExit = value

   @property
   def objects(self):
       return self._objects
   @objects.setter
   def objects(self, value):
       self._objects = value

   class Room:

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

      def __init__(self, x, y, w, h, roomEffect=None):
         self.room_effect = roomEffect
         self.wall_rect = self.Rect(x - 1, y - 1, w + 2 , h + 2)
         self._floor_rect = self.Rect(x, y, w - 1, h - 1)
         self.floor_spaces = [ (floor_x, floor_y) for floor_x in range(x, x + w) for floor_y in range(y, y + h) ]

      @property
      def center(self):
          return self.wall_rect.center()

      def intersect(self, other):
         return self.wall_rect.intersect(other.wall_rect)

      def get_random_floor_space(self):
         return random.choice(self.floor_spaces)

      def get_random_floor_space_not_touching_wall(self):
         x1, x2, y1, y2 = self._floor_rect.x1, self._floor_rect.x2, self._floor_rect.y1, self._floor_rect.y2
         if x2 - x1 <= 1 or y2 - y1 <= 1:
            return False #no floor spaces not touching a wall

         while True:
            x, y = self.get_random_floor_space()
            if x != x1 and x != x2 and y != y1 and y != y2:
               return (x, y)

   def send_to_back(self, obj):
      #make this object be drawn first, so all others appear above it if they're in the same tile.
      if obj in self.objects:
         self.objects.remove(obj)

      self.objects.insert(0, obj)

   def is_blocked(self, x, y):
      #first test the map tile
      if self._map[x][y].blocks:
         return True

      #now check for any blocking objects
      for obj in self.objects:
         if obj.blocks and obj.x == x and obj.y == y:
            return True

      return False

   def make_map(self, mapWidth = None, mapHeight = None, maxRooms = None, roomMinSize = None, roomMaxSize = None):
      self._build_map(mapWidth, mapHeight, maxRooms, roomMinSize, roomMaxSize)
      #create entrance and exit
      self._make_level_entrance()
      self._make_level_exit()

   def _build_map(self, mapWidth = None, mapHeight = None, maxRooms = None, roomMinSize = None, roomMaxSize = None):
      if mapWidth is not None:
         self.mapWidth = mapWidth
      if mapHeight is not None:
         self.mapHeight = mapHeight
      if maxRooms is not None:
         self._maxRooms = maxRooms
      if roomMinSize is not None:
         self._roomMinSize = roomMinSize
      if roomMaxSize is not None:
         self.roomMaxSize = roomMaxSize

      #fill map with "blocked" tiles
      self._map = [[ self._make_wall(x, y)
             for y in range(self.mapHeight) ]
           for x in range(self.mapWidth) ]

      self._rooms = []
      num_rooms = 0

      for r in range(self._maxRooms):
         #random width and height
         w = get_random_int(self._roomMinSize, self._roomMaxSize)
         h = get_random_int(self._roomMinSize, self._roomMaxSize)
         #random position without _going out of the boundaries of the map
         x = get_random_int(0, self.mapWidth - w - 1)
         y = get_random_int(0, self.mapHeight - h - 1)

         #"Rect" class makes rectangles easier to work with
         new_room = self.Room(x, y, w, h)

         #run through the other rooms and see if they intersect with this one
         failed = False
         for other_room in self._rooms:
            if new_room.intersect(other_room):
                failed = True
                break

         if not failed:
            #this means there are no intersections, so this room is valid

            #"paint" it to the map's tiles
            self._create_room(new_room)

            #add some contents to this room, such as monsters
            #self.place_objects(new_room)

            #center coordinates of new room, will be useful later
            new_x, new_y = new_room.center

            if num_rooms > 0:
               #all rooms after the first:
               #connect it to the previous room with a tunnel

               #center coordinates of previous room
               prev_x, prev_y = self._rooms[num_rooms - 1].center

               #draw a coin (random number that is either 0 or 1)
               if get_random_int(0, 1) == 1:
                  #first move horizontally, then vertically
                  self._create_h_tunnel(prev_x, new_x, prev_y)
                  self._create_v_tunnel(prev_y, new_y, new_x)
               else:
                  #first move vertically, then horizontally
                  self._create_v_tunnel(prev_y, new_y, prev_x)
                  self._create_h_tunnel(prev_x, new_x, new_y)

            #finally, append the new room to the list
            self._rooms.append(new_room)
            num_rooms += 1

   def _create_room(self, room):
      #go through the tiles in the rectangle and make them passable
      for x, y in room.floor_spaces:
         self._map[x][y] = self._make_floor(x, y)

   def _create_h_tunnel(self, x1, x2, y):
      #horizontal tunnel. min() and max() are used in case x1>x2
      for x in range(min(x1, x2), max(x1, x2) + 1):
         self._map[x][y] = self._make_floor(x, y)

   def _create_v_tunnel(self, y1, y2, x):
      #vertical tunnel
      for y in range(min(y1, y2), max(y1, y2) + 1):
         self._map[x][y] = self._make_floor(x, y)

   def _make_wall(self, x, y):
      wall = Tile(x, y, self.getWallChar(), "Wall", self.getWallColor())
      wall.wallComponent = WallComponent(wall)
      return wall

   def _make_floor(self, x, y):
      floor = Tile(x, y, self.getFloorChar(), "Floor", self.getFloorColor())
      floor.floorComponent = FloorComponent(floor)
      return floor

   def _make_level_entrance(self):
      x, y = self._get_exit_space()
      entrance = self._map[x][y]
      entrance.entranceComponent = LevelExitComponent(entrance, 'Entrance', self._entranceChar)
      self.send_to_back(entrance)  #so it's drawn below the monsters
      self._levelEntrance = entrance

   def _make_level_exit(self):
      x, y = self._get_exit_space()
      exit = self._map[x][y]
      exit.exitComponent = LevelExitComponent(exit, 'Exit', self._exitChar)
      self.send_to_back(exit)  #so it's drawn below the monsters
      self._levelExit = exit

   def _get_exit_space(self):
      goodRoom = False
      while not goodRoom:
         room = self._rooms[get_random_int(0, len(self._rooms) - 1)]
         goodRoom = True
         for x, y in room.floor_spaces:
            if hasattr(self._map[x][y], 'entranceComponent') or hasattr(self._map[x][y], 'exitComponent'):
               goodRoom = False

      space = room.get_random_floor_space_not_touching_wall()
      if space is False:
         space = room.get_random_floor_space()
      return space

   def _place_objects(self, room):
      numItems = get_random_int(0, self._maxRoomObjects)
      goodSpace = False
      while not goodSpace:
         space = room.get_random_floor_space

   def getWallColor(self):
      return self._wallColor

   def getFloorColor(self):
      return self._floorColor

   def getWallChar(self):
      return self._wallChar

   def getFloorChar(self):
      return self._floorChar
