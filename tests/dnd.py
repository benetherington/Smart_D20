import bisect
import random

modifiers_lookup = {
  1: -5,
  3: -4,
  5: -3,
  7: -2,
  9: -1,
  11: 0,
  13: 1,
  15: 2,
  17: 3,
  19: 4,
  21: 5,
  23: 6,
  25: 7,
  27: 8,
  29: 9,
  30: 10
}

def object_builder(config):
  for category, values in config: 
    if category == 'weapons':
      for weapon in values:
        Weapons.construct(weapon)
    elif category == 'spells':
      for spell in values:
        Spells.construct(spell)
    elif category == 'ability':
      for ability in values:
        Abilities.construct(ability)

class Attackers:
  def __init__(self):
    self.items = {}
  def construct(self, d):
    klass = globals()[d['name']]
    self.items[d['name']] = klass(d)
  def roll_attack(self):
    pass

class Spells(Attackers):
  def __init__(self):
    self.items = {}
  def construct(self, d):
    klass = globals()[d['name']]
    self.items[d['name']] = klass(d)
  def roll_attack(self):
    pass

class Weapons(Attackers):
  def __init__(self):
    self.items = {}
  def construct(self, d):
    klass = globals()[d['name']]
    self.items[d['name']] = klass(d)
  def roll_attack(self):
    pass

class Spell:
  def __init__(self, d):
    self.name        = d['name']
    self.time        = d['time']
    self.range       = d['range']
    self.description = d['description']
    self.damage      = d['damage']

class Weapon:
  def __init__(self, d):
    self.damage      = d["damage"]
    self.weapon_type = d["type"]
    self.damage_type = d["damage_type"]
    self.properties  = d["properties"]
    self.modifiers   = d["modifiers"]


def modify(ability):
  bisect.bisect_left(modifiers_lookup,ability)

def roll(die): # 2d4 +3
  total = []
  # roll the dice
  for _ in range(die[0]):
    total << random.randrange(1,die[1])
  # add the bonus
  if 2<len(die):
    total << die[2]
  return total

def attack_roll(weapon):
  attack = roll(1,20,bonus)
  damage = roll(weapon["damage"])
  return {"attack": attack, "damage":damage}


def spell_roll(spell):
  pass