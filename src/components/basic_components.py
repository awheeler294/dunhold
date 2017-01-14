from component import Component
from src.utilityClasses import *
from src.defaultConstants import *


class MobilityComponent(Component):

    """Movement functions"""
    def __init__(self, owner):
        Component.__init__(self, owner)

    def move(self, dx, dy):
        # move by the given amount
        self.owner.x += dx
        self.owner.y += dy

    def move_towards(self, target_x, target_y):
        dx = target_x - self.owner.x
        dy = target_y - self.owner.y
        distance_to_position = math.sqrt(dx ** 2 + dy ** 2)

        # vector from this object to the target, and distance
        # normalize it to length 1 (preserving direction), then round it and
        # convert to integer so the movement is restricted to the map grid
        dx = int(round(dx / distance_to_position))
        dy = int(round(dy / distance_to_position))
        self.move(dx, dy)


class PlayerComponent(Component):
    def __init__(self, owner, hp, defense, power, xp, death_function=None):
        Component.__init__(self, owner)
        owner.mobComponent = MobComponent(owner, hp, defense, power, xp, death_function,
                                          fov_light_walls=False,
                                          is_hostile=False)
        owner.always_visible = True


class MobComponent(Component):
   def __init__(self, owner, hp, defense, power, xp, death_function=None, fov_light_walls=False, is_hostile = True):
      Component.__init__(self, owner)
      self._fovLightWalls = fov_light_walls
      self._fov_recompute = True
      self._safe_move = False
      self._safe_wait_counter = 0
      self.death_function = death_function
      owner.stats = StatComponent(owner)
      owner.inventory = InventoryComponent(owner)
      owner.mobilityComponent = MobilityComponent(owner)
      owner.combatComponent = CombatComponent(owner, hp, defense, power, xp, death_function)
      self._hostility = {HOSITLE_TO_PLAYER: is_hostile}

   @property
   def hostility(self):
       return self._hostility
   @hostility.setter
   def hostility(self, value):
       self._hostility = value

   @property
   def fov_map(self):
       return self._fov_map
   @fov_map.setter
   def fov_map(self, value):
       self._fov_map = value

   @property
   def fov_recompute(self):
       return self._fov_recompute
   @fov_recompute.setter
   def fov_recompute(self, value):
       self._fov_recompute = value

   @property
   def safe_move(self):
       return self._safe_move
   @safe_move.setter
   def safe_move(self, value):
       self._safe_move = value

   @property
   def safe_move_dx(self):
       return self.owner._safe_move_dx
   @safe_move_dx.setter
   def safe_move_dx(self, value):
       self.owner._safe_move_dx = value

   @property
   def safe_move_dy(self):
       return self.owner._safe_move_dy
   @safe_move_dy.setter
   def safe_move_dy(self, value):
       self.owner._safe_move_dy = value

   @property
   def possible_moves(self):
       return self._possible_moves
   @possible_moves.setter
   def possible_moves(self, value):
       self._possible_moves = value

   def is_hostile(self, other):
      if hasattr(self.owner, 'playerComponent'):
         return other.hostility[HOSITLE_TO_PLAYER]
      if self.hostility[HOSITLE_TO_PLAYER]:
         if hasattr(other.owner, 'playerComponent'):
            return True
      return False

   def safe_move_wait(self):
      if self.safe_move == False:
         self.safe_move = True
         self._safe_wait_counter = 0

      if self._safe_wait_counter >= SAFE_MOVE_WAIT_TIME:
         self._safe_wait_counter = 0
         self.safe_move = False
         return False
      else:
         self._safe_wait_counter += 1
         return True


   def initialize_fov(self, mapHeight, mapWidth, levelMap):
      self.fov_map = create_fov_map(mapHeight, mapWidth, levelMap)

   def recompute_fov(self, mapHeight, mapWidth):
      # recompute FOV fov_map, x, y, seightRadius, fov_light_walls
      compute_fov(self.fov_map, self.owner.x, self.owner.y, self.owner.seightRadius, self._fovLightWalls)
      self.fov_recompute = False


class StatComponent(Component):
   def __init__(self, owner):
      Component.__init__(self, owner)


class InventoryComponent(Component):
   def __init__(self, owner):
      Component.__init__(self, owner)


class CombatComponent(Component):
      # combat-related properties and methods (monster, player, NPC).
      def __init__(self, owner, hp, defense, power, xp, death_function=None):
         Component.__init__(self, owner)
         self.base_max_hp = hp
         self.hp = hp
         self.base_defense = defense
         self.base_power = power
         self.xp = xp
         self.death_function = death_function

      @property
      def power(self):  # return actual power, by summing up the bonuses from all equipped items
         bonus = sum(equipment.power_bonus for equipment in self.get_all_equipped(self.owner))
         return self.base_power + bonus

      @property
      def defense(self):  # return actual defense, by summing up the bonuses from all equipped items
         bonus = sum(equipment.defense_bonus for equipment in self.get_all_equipped(self.owner))
         return self.base_defense + bonus

      @property
      def max_hp(self):  # return actual max_hp, by summing up the bonuses from all equipped items
         bonus = sum(equipment.max_hp_bonus for equipment in self.get_all_equipped(self.owner))
         return self.base_max_hp + bonus

      def attack(self, target):
         # a simple formula for attack damage
         damage = self.power - target.fighter.defense

         if damage > 0:
            # make the target take some damage
            message = self.owner.name.capitalize() + ' attacks ' + target.name + ' for ' + str(damage) + ' hit points.'
            target.fighter.take_damage(damage)
         else:
            message = self.owner.name.capitalize() + ' attacks ' + target.name + ' but it has no effect!'

         return message

      def take_damage(self, damage):
         # apply damage if possible
         if damage > 0:
            self.hp -= damage

            # check for death. if there's a death function, call it
            if self.hp <= 0:
               function = self.death_function
               if function is not None:
                  function(self.owner)

               if self.owner != player:  # yield experience to the player
                  player.fighter.xp += self.xp

      def heal(self, amount):
         # heal by the given amount, without going over the maximum
         self.hp += amount
         if self.hp > self.max_hp:
            self.hp = self.max_hp

      def get_all_equipped(self, obj):  # returns a list of equipped items
         if hasattr(obj, "inventoryComponent"):
            inventory = obj.inventoryComponent.inventory
            equipped_list = []
            for item in inventory:
               if item.equipment and item.equipment.is_equipped:
                  equipped_list.append(item.equipment)
            return equipped_list
         else:
            return []  # other objects have no equipment


class TileComponent(Component):
   """A tile of the map and its properties"""
   def __init__(self, owner, blocked, block_sight = None):
      Component.__init__(self, owner)

      # by default, if a tile is blocked, it also blocks sight
      if block_sight is None: block_sight = blocked
      self.block_sight = block_sight

      owner.blocks = blocked
      owner.block_sight = block_sight

      owner.is_terrain = True

      # all tiles start unexplored
      self.explored = False


class WallComponent(Component):
   def __init__(self, owner):
      Component.__init__(self, owner)
      owner.blocks = True
      owner.block_sight = True


class FloorComponent(Component):
   def __init__(self, owner):
      Component.__init__(self, owner)
      owner.blocks = False
      owner.block_sight = False


class LevelExitComponent(Component):
   def __init__(self, owner, name, char, color=None):
      Component.__init__(self, owner)
      if color is not None:
         owner.color = color
      else:
         owner.color = COLOR_EXIT
      owner.char = char
      owner.name = name
      owner.blocks = False
      owner.block_sight = False
      owner.always_visible = True
      self.connected_level = None
