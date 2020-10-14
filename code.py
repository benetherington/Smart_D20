'''
SMART D20
Written (mostly) in 2020 by Ben Etherington

Makes DND rolls with modifiers at the touch of a button!
'''
# UTILITIES
import sys # pylint: disable=unused-import
import time
import json

# MICROCONTROLLER IO
import board
import busio
# from analogio import AnalogIn
from digitalio import DigitalInOut, Direction # pylint: disable=unused-import
import digitalio # pylint: disable=unused-import

# LOCAL
# from dnd import *
# from button import *
from sharp_display import SharpDisplay
from eink_display import EinkDisplay
from button import Buttons
from dungeon_master import DungeonMaster



'''
INIT DISPLAYS
'''
spi = board.SPI()
sharp = SharpDisplay(spi=spi, chip_select_pin=board.D4)
eink = EinkDisplay(spi=spi, chip_select_pin=board.A1, enable_pin=None)
eink.primary_display = sharp # eink.sleep() re-wakens the primary display

'''
INIT BUTTONS
'''
led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT

i2c = busio.I2C(board.SCL, board.SDA)
buttons = Buttons(i2c, display=sharp, led=led)



'''
LOAD DATA
'''
# with open('character_sheet.json') as f
#   character = json.load(f, object_hook=object_builder)

character = [ # e-ink columns are 64-2= 62 px wide
              ("Acrobatics", "+1"),
              ("Animal Handling", "+2"),
              ("Arcana", "+3"),
              ("Athletics", "+4"),
              ("Decepition", "+5"),
              ("History", "+6"),
              ("Insight", "+7"),
              ("Intimidation", "+8"),
              ("Investigation", "+9"),
              ("Medicine", "+1"),
              ("Nature", "+2"),
              ("Perception", "+3"),
              ("Performance", "+4"),
              ("Persuasion", "+5"),
              ("Religion", "+6"),
              ("Slight of Hand", "+7"),
              ("Stealth", "+8"),
              ("Survival", "+9")
            ]
character = json.



'''
TESTING
'''
def change_led():
  '''demo'''
  led.value = not led.value

def blink_led():
  '''demo'''
  for i in range(5): # pylint: disable=unused-variable
    led.value = not led.value
    time.sleep(.05)

buttons.set_callback("upper", change_led)
buttons.set_callback("lower", blink_led)


'''
INIT GAME RULES
'''
dungeon_master = DungeonMaster(eink=eink, sharp=sharp, buttons=buttons,
                               character=character, menu_structure="./menu_structure.json")
dungeon_master.update_eink()
dungeon_master.main_menu()


'''
MAIN LOOP
'''
while True:
  time.sleep(1)
  buttons.check_interrupts()

# Display loop
# while True:
#   try:
#     print(f"safe in: {eink.time_to_safe()}")
#     if eink.time_to_safe() > 0:
#       led.value = not led.value
#       time.sleep(1)
#     else:
#       print("safe!")
#       for x in range(10):
#         led.value = not led.value
#         time.sleep(.1)
#       break
#   except Exception as e:
#     sys.print_exception()
#     break
