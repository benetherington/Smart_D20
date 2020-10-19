# UTILITIES
import time

# BOARD IO
import board
import adafruit_il0373
from digitalio import DigitalInOut, Direction # pylint: disable=unused-import

# GUI
import displayio
# import adafruit_imageload
from adafruit_display_text.label import Label
from font_lib import f

class EinkDisplay:
  # dimensions and colors
  WIDTH = 128
  HEIGHT = 296
  NUM_ROWS = 18
  p = displayio.Palette(3)
  p[0] = 0xffffff # white
  p[1] = 0xff0000 # actually orange on the display
  p[2] = 0x000000 # black
  WHITE = 0
  ORANGE = 1
  BLACK = 2

  def __init__(self, spi, chip_select_pin, data_command_pin, enable_pin, primary_display=None):
    # HANDLE ARGUMENTS
    self.spi = spi
    self.cs_pin = chip_select_pin
    self.dc_pin = data_command_pin
    if enable_pin is None:
      self.enable_pin = None
    else:
      self.enable_pin = DigitalInOut(enable_pin) # pylint: disable=undefined-variable
      # self.enable_pin.value = False
    if primary_display is None:
      self.primary_display = None # will be set after sharp is initiated
    else:
      self.primary_display = primary_display
    # HOUSEKEEPING
    self.display = None # will be set on wake_up
    self.next_safe_refresh = time.time()
    # INIT BACKGROUND BMP
    self.background = displayio.Bitmap(self.WIDTH, self.HEIGHT, 3)
    background_grid = displayio.TileGrid(self.background, pixel_shader=self.p)
    # INIT DISPLAY GROUP
    self.layers = displayio.Group(max_size=3)
    self.layers.append(background_grid)             # layers[0] is background
    self.layers.append(displayio.Group(max_size=10)) # layers[1] is nav interface
    self.layers.append(displayio.Group(max_size=36)) # layers[2] is button labels
    self.background = self.layers[0]
    self.nav =        self.layers[1]
    self.labels =     self.layers[2]

  '''
  CONTROL FUNCTIONS
  '''
  def wake_up(self):
    '''
    Releases other displays and connects to the E-ink. Should be used in conjunction with sleep()
    so that downstream errors don't get displayed here.
    '''
    displayio.release_displays()
    # self.enable_pin.value = True
    bus = displayio.FourWire(self.spi, chip_select=self.cs_pin, command=self.dc_pin,
                             baudrate=1000000)
    time.sleep(1)  # Wait a bit
    self.display = adafruit_il0373.IL0373(bus, busy_pin=None, rotation=0,
                                     highlight_color=0xff0000,
                                     width=self.WIDTH, height=self.HEIGHT)
  def sleep(self):
    ''' safes this display and re-wakes the primary '''
    displayio.release_displays()
    # self.enable_pin.value = False
    if self.primary_display is not None:
      self.primary_display.wake_up()
  def refresh(self):
    '''
    Updates the display with self.layers. Calling display.refresh() will always need to be escaped
    so that errors don't get displayed here, so a method is easier.
    '''
    try:
      self.display.show(self.layers)
      print(f"sleeping {self.time_to_safe()} sec until safe to refresh")
      time.sleep(self.time_to_safe())
      self.display.refresh()
      self.next_safe_refresh = time.time() + self.display.time_to_refresh
    except AttributeError:
      pass
  def time_to_safe(self):
    ''' handy way to access next_safe_refresh in context '''
    try:
      print(f"time: {time.time()}")
      print(f"self.next_safe_refresh: {int(self.next_safe_refresh)}")
      print(f"next-time: {int(self.next_safe_refresh)-int(time.time())}\n")
      return max(int(self.next_safe_refresh)-int(time.time()), 0) # no floating!
    except AttributeError:
      return 0
  def clear_display(self):
    ''' clears the screen independent of all other GUI logic for quick maintainance '''
    group = displayio.Group()
    bitmap = displayio.Bitmap(self.WIDTH, self.HEIGHT, 3)
    bitmap.fill(self.WHITE)
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=self.p)
    group.append(tile_grid)
    self.display.show(group)
    print(f"sleeping  {self.display.time_to_refresh} sec until safe to refresh")
    time.sleep(self.display.time_to_refresh)
    self.display.refresh()
    self.sleep()

  '''
  DRAWING TOOLS
  '''
  def show_labels_rows(self, options, refresh_now=False):
    '''
    Takes a list of labels (stats and their modifiers), formats them, and updates the E-ink. Needs
    to be used in conjunction with draw_padded_row_lines.
    '''
    labels = self.layers[2]
    row_height = 16 # 296/18 leaves 8px leftover
    space = 4 # space between stat and modifer
    for row, option in enumerate(options):
      stat = Label(font=f['HaxorNarrow-15'], text=option[0], scale=1,
                   color=self.p[2])
      mod = Label(font=f['knxt-20'], text=option[1], scale=1,
                  color=self.p[2])
      # find statistic boundary box sizes
      sbx, sby, sbw, sbh = stat.bounding_box
      sbw, sbh = (sbw*stat.scale, sbh*stat.scale) # adjust for scale
      sbx, sby = (sbx*stat.scale, sby*stat.scale)
      # find modifier boundary box sizes
      mbx, mby, mbw, mbh = mod.bounding_box
      mbw, mbh = (mbw*mod.scale, mbh*mod.scale) # adjust for scale
      mbx, mby = (mbx*mod.scale, mby*mod.scale)
      # center both labels
      if True: # if alternating, use i%2:
        # button is on the left
        stat.x = int(
                     0
                     + space
                     # self.WIDTH/2 # center of the screen
                     # - (sbw # width of the stat
                     #    + space # gap in the middle
                     #    + mbw) # width of the modifier
                     #    /2 # center of the two
                    )
        mod.x = int(
                    self.WIDTH
                    - mbw
                    - space
                    # stat.x # left side of the statistic
                    # + sbw # width of the statistic
                    # + space # gap in the middle
                    )
      # place both labels on the row
      stat.y = mod.y = int(
                           row_height*row # correct row
                           + (row_height/2) # bounding box is centered on vertical height
                           + 4 # padding at the top of the screen
                           + 1 # grid line
                           )
      labels.append(stat)
      labels.append(mod)
    if refresh_now:
      self.refresh()

  # def show_labels_grid(self, options, refresh_now=False):
  #   labels = self.layers[2]
  #   row_height = 32 # 296/9 leaves 8px leftover

  #   for i, option in enumerate(options):
  #     # determine column and row (we populate left to right, top to bottom)
  #     left_column = i%2
  #     row_number = floor(i/2)
  #     # build Label objects
  #     stat = Label(font=self.FONT, text=option[0], scale=1, color=self.BLACK,
  #                  line_spacing=0.7)
  #     mod = Label(font=self.FONT, text=option[1], scale=2,
  #                 color=self.ORANGE)
  #     # find statistic sizes
  #     bx, by, bw, bh = stat.bounding_box
  #     bw, bh = (bw*stat.scale, bh*stat.scale) # adjust for scale
  #     bx, by = (bx*stat.scale, by*stat.scale)
  #     # center statistic text
  #     if left_column:
  #       stat.x = int(
  #                       self.WIDTH*3/4 # center of the left column
  #                       - bw/2 # center of the bounding box
  #                     )
  #     else:
  #       stat.x = int(
  #                       self.WIDTH*1/4 # center of the right column
  #                       - bw/2 # center of the bounding box
  #                     )
  #     # place statistic text in correct row
  #     if "\n" in option[0]:
  #       line_adjustment = -7
  #     else:
  #       line_adjustment = 0
  #     stat.y = int(
  #                     4 # four padding pixels at the top of the screen
  #                     + (row_number*row_height) # move down i number of rows
  #                     + 3 # add a gap on top
  #                     + (bh/2) # bounding box is centered on text height
  #                     + line_adjustment # multi-line rows have headspace
  #                   )
  #     # find modifier sizes
  #     bx, by, bw, bh = mod.bounding_box
  #     bw, bh = (bw*mod.scale, bh*mod.scale) # adjust for scale
  #     bx, by = (bx*mod.scale, by*mod.scale)
  #     # center modifier text
  #     if left_column:
  #       mod.x = int(
  #                       self.WIDTH*3/4 # center of the left column
  #                       - bw/2 # center of the bounding box
  #                     )
  #     else:
  #       mod.x = int(
  #                       self.WIDTH*1/4 # center of the right column
  #                       - bw/2 # center of the bounding box
  #                     )
  #     # place modifier text in correct row
  #     mod.y = int(
  #                     4 # four padding pixels at the top of the screen
  #                     + (row_number*row_height) # move down i number of rows
  #                     + row_height # start at the bottom of the row
  #                     - 3 # add a gap on bottom
  #                     - (bh/2) # bounding box is centered on text height
  #                   )
  #     # get everything over to the display group!
  #     labels.append(stat)
  #     labels.append(mod)
  #   if refresh_now:
  #     self.refresh()
