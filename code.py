'''
SMART D20
Written (mostly) in 2020 by Ben Etherington

Makes DND rolls with modifiers at the touch of a button!
'''
# UTILITIES
import sys # pylint: disable=unused-import
import time

# MICROCONTROLLER IO
import board
import busio
# from analogio import AnalogIn
import digitalio # pylint: disable=unused-import
import displayio # pylint: disable=unused-import

# LOCAL
# from dnd import *
# from button import *
from sharp_display import SharpDisplay
from eink_display import EinkDisplay
from button import Buttons
from dungeon_master import DungeonMaster



'''
CONFIGURE PINS
'''
displayio.release_displays()
i2c = busio.I2C(board.SCL, board.SDA)
spi = board.SPI()
SHARP_CS_PIN = board.D4
EINK_CS_PIN = board.A1
EINK_DC_PIN = board.A4
EINK_ENABLE_PIN = None # will be A2
led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT


'''
INIT DISPLAYS
'''
sharp = SharpDisplay(spi=spi, chip_select_pin=SHARP_CS_PIN)
eink = EinkDisplay(spi=spi, chip_select_pin=EINK_CS_PIN, data_command_pin=EINK_DC_PIN,
                   enable_pin=EINK_ENABLE_PIN)
eink.primary_display = sharp # eink.sleep() re-wakens the primary display


'''
INIT BUTTONS
'''
buttons = Buttons(i2c, display=sharp, led=led)


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
                               character_filepath="./character_sheet.json",
                               menu_structure_filepath="./menu_structure.json")
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
