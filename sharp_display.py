import framebufferio
import sharpdisplay

# GUI
import displayio
# import adafruit_imageload
from adafruit_display_text.label import Label
from font_lib import f

class SharpDisplay():
  # styles
  OPTION_FONT  = f["HaxorNarrow-17"]
  OPTION_SCALE = 1
  BUTTON_FONT  = f["HaxorNarrow-17"]
  BUTTON_SCALE = 1
  # dimensions and colors
  WIDTH = 144
  HEIGHT = 168
  NUM_ROWS = 6
  palette = displayio.Palette(2)
  palette[0] = 0x000000
  palette[1] = 0xffffff
  BLACK = 0
  WHITE = 1
  def __init__(self, spi, chip_select_pin):
    self.spi = spi
    self.chip_select_pin = chip_select_pin
    self.display = None
    # initialize background bitmap
    self.background = displayio.Bitmap(self.WIDTH, self.HEIGHT, 2)
    background_grid = displayio.TileGrid(self.background, pixel_shader=self.palette)
    # initialize the top-level group
    self.layers = displayio.Group(max_size=3)
    self.layers.append(background_grid)             # layers[0] is background
    self.layers.append(displayio.Group(max_size=1)) # layers[1] is nav interface
    self.layers.append(displayio.Group(max_size=1)) # layers[2] is button labels
  def wake_up(self):
    ''' initiates display I/O and shows self.layers '''
    displayio.release_displays()
    framebuffer = sharpdisplay.SharpMemoryFramebuffer(self.spi, self.chip_select_pin,
                                                      baudrate=8000000,
                                                      width=self.WIDTH,
                                                      height=self.HEIGHT)
    self.display = framebufferio.FramebufferDisplay(framebuffer, auto_refresh=False)
    self.display.show(self.layers)
  def refresh(self):
    '''
    not using auto_refresh allows us to build inside layers[background] without a buffer object
    '''
    while not self.display.refresh(minimum_frames_per_second=0):
      pass # https://github.com/adafruit/circuitpython/issues/2310
  def clear_background(self):
    ''' for readability '''
    self.background.fill(0)
