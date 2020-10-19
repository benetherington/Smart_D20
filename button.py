import board
import busio
from digitalio import Direction, Pull, DigitalInOut
from adafruit_mcp230xx.mcp23017 import MCP23017
import time


def partial(func, *args, **keywords):
  def newfunc(*fargs, **fkeywords):
    newkeywords = keywords.copy()
    newkeywords.update(fkeywords)
    return func(*(args + fargs), **newkeywords)
  return newfunc

class Button:
  # just a mutible object so we can reference the same callback with multiple keys in the same
  # dictionary
  def __init__(self, callback=None):
    self.callback = callback

class Buttons():
  def __init__(self, i2c, display, led):
    # INIT IO
    self.mcp1 = MCP23017(i2c, address=0x20)
    self.mcp2 = MCP23017(i2c, address=0x21)
    interrupts_io = {
      'mcp1': DigitalInOut(board.A4),
      'mcp2': DigitalInOut(board.A5)
      }
    # CONFIGURE MCPs
    for mcp in [self.mcp1, self.mcp2]:
      # enable interrupts
      mcp.interrupt_enable = 0xFFFF
      # configure interrupts for change from default
      mcp.inturrupt_configuration = 0xFFFF
      # set default as high, so we're notified on low
      mcp.default_value = 0xFFFF
      # interupt as open drain, mirror A and B
      mcp.io_control = 0x44
    # CONFIGURE PINS
    pins_button_names = {
      self.mcp1: {},
      self.mcp2: {
              6: "lower",
              7: "upper"
            }
      }
    # We'll need to store callbacks, and reference them by both pin number (to respond to
    # interrupt flags) as well as button name (to set them in the first place)
    self.buttons_callbacks = {}
    for mcp, pins in pins_button_names.items():
      mcp.clear_ints()
      for pin_number, button_name in pins.items():
        # INIT PIN
        pin = mcp.get_pin(pin_number)
        pin.direction = Direction.INPUT
        # MCP chip doesn't have onboard pull down. This means the button
        # value will be True when not pushed, and False when pushed.
        pin.pull = Pull.UP
        # ADD PIN TO BUTTONS_CALLBACKS
        button = Button()
        self.buttons_callbacks[pin_number] = button
        self.buttons_callbacks[button_name] = button

  def set_callback(self, button_name, callback):
    self.buttons_callbacks[button_name].callback = callback

  def check_interrupts(self):
    # called by main loop whenever we're ready to look for button presses
    for pin in self.mcp2.int_flag:
      print(f"Interrupt on pin {pin}")
      self.buttons_callbacks[pin].callback()
    self.mcp2.clear_ints()
  


    # while True:
    #   if not pin_upper.value or not pin_lower.value:
    #     print(f"upper: {pin_upper.value}, lower: {pin_lower.value}")
    #   else:
    #     print()

