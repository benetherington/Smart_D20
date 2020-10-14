import sys
import re
import board
import busio
from digitalio import Direction, Pull, DigitalInOut
from adafruit_mcp230xx.mcp23017 import MCP23017

# INITIALIZE PORT EXPANDERS
mcp1 = MCP23107(i2c, address=0x20)
mcp2 = MCP23107(i2c, address=0x21)
interrupts_io = {
  'mcp1': digitalio.DigitalInOut(board.A4),
  'mcp2': digitalio.DigitalInOut(board.A5)
  }

for mcp in [mcp1, mcp2]:
  # enable interrupts
  mcp.interrupt_enable = 0xFFFF
  # configure interrupts for change from default
  mcp.inturrupt_configuration = 0xFFFF
  # set default as high, so we're notified on low
  mcp.default_value = 0xFFFF
  # interupt as open drain, mirror A and B
  mcp.io_control = 0x44

# INITIALIZE BUTTONS
buttons_directory = {
  'eink': {
    'left': [
      'ink_L_1',
      'ink_L_2',
      'ink_L_3',
      'ink_L_4',
      'ink_L_5',
      'ink_L_6',
      'ink_L_7',
      'ink_L_8',
      'ink_L_9'
    ],
    'right': [
      'ink_R_1',
      'ink_R_2',
      'ink_R_3',
      'ink_R_4',
      'ink_R_5',
      'ink_R_6',
      'ink_R_7',
      'ink_R_8',
      'ink_R_9'
    ]
  },
  'sharp': {
    'left': [
      'shp_L_1',
      'shp_L_2',
      'shp_L_3'
    ],
    'right': [
      'shp_R_1',
      'shp_R_2',
      'shp_R_3'
    ]
  }
}

pins_buttons = {
  'mcp1':{
    # GPA pins 0-7
    0:  'ink_R_9',
    1:  'ink_R_8',
    2:  'ink_R_7',
    3:  'ink_R_6',
    4:  'ink_R_5',
    5:  'ink_R_4',
    6:  'ink_R_3',
    7:  'ink_R_2',
    # GPB pins 0-7
    8:  'ink_R_1',
    9:  'shp_L_3',
    10: 'shp_L_2',
    11: 'shp_L_1',
    12: 'mode_select'
    # 13:
    # 14:
    # 15:
  },
  'mcp2':{
    # GPA pins 0-7
    # 0:
    # 1:
    # 2:
    # 3:
    4:  'shp_R_3',
    5:  'shp_R_2',
    6:  'shp_R_1',
    7:  'ink_L_1',
    # GPB pins 0-7
    8:  'ink_L_2',
    9:  'ink_L_3',
    10: 'ink_L_4',
    11: 'ink_L_5',
    12: 'ink_L_6',
    13: 'ink_L_7',
    14: 'ink_L_8',
    15: 'ink_L_9'
    }
}

for pin in pins_buttons:
  pin.direction = Direction.INPUT
  pin.pull = Pull.UP

for pin in interrupts_io:
  pin.direction = Direction.INPUT
  pin.pull = Pull.UP


class Button:
  '''
  There should be only one button object. It has a class variable, buttons_callbacks,
  that stores button name strings and their assigned callback functions. Don't access
  this dict, instead, call set_button(). The main loop continually calls
  check_inturrupts(), which polls the port expanders for changed pins, then performs
  callbacks.
  '''
  def __init__(self):
    # builds the callback list, initially empty, but updated depending on the current mode
    self.button_callbacks = {}
    for button in buttons.values():
      buttons_callbacks[button] = lambda: None
    buttons_callbacks['mode_select'] = "Mode.next"

  def check_interrupts(self):
    # called by main loop continually, performs callbacks for pushed buttons
    for mcp_name, mcp_io in interrupts_io.items():
      if mcp_io.value(): # check the inturrupt pin for a signal
        for pin_flag in mcp_io.int_flag: # poll the MCP for flags
          self.buttons_callbacks[pins_buttons[mcp][pin]]() # do each assigned callback

  def set_button(self, button_name, callback):
    # called to update a single button
    self.buttons_callbacks[button_name] = callback

  def set_buttons(self, button_group_name, callbacks):
    # Set eink or sharp buttons all at once from a list of callbacks. Returns True
    # if we used up the entire list, False if there were any left over.
    button_group = buttons_directory[button_group_name]['left']
    button_group += buttons_directory[button_group_name]['right']
    for button_name in button_group:
      try:
        self.set_button(button_name, callbacks.pop(0))
      except IndexError:
        return True
    return len(callbacks) > 0

  def set_buttons_with_pagination(self, button_group_name, callbacks):
    # Set eink or sharp buttons all at once from a list of callbacks. If there are
    # more callbacks than can fit on the button group, sets n-1 callbacks, and returns
    # the touple (next button, [remaining list]) allowing the calling function to set
    # the next button as appropriate. Returns False if no pagination is required.
    button_group = buttons_directory[button_group_name]['left']
    button_group += buttons_directory[button_group_name]['right']
    if len(callbacks) > len(button_group):
      # if we need to paginate, save the last button for the next page command
      next_group = button_group.pop(-1)
    for button_name in button_group:
      if len(callbacks) > 0:
        self.set_button(button_name, callbacks.pop(0))
      else:
        # if there are no callbacks left
        return False
    if next_group is None
      # callbacks all fit on the button group
      return False
    else:
      # we need to paginate
      return next_group, callbacks

  def clear_buttons(self):
    for mcp in pins_buttons:
      for button in mcp.values():
        buttons_callbacks[button] = None

  def clear_eink_buttons(self):
    for mcp in pins_buttons.values():
      for button in mcp.values():
        if re.match(r"ink_[LR]_\d", button):
          buttons_callbacks[button] = None

  def clear_sharp_buttons(self):
    for mcp in pins_buttons.values():
      for button in mcp.values():
        if re.match(r"shp_[LR]_\d", button):
          buttons_callbacks[button] = None
