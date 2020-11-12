# UTILITIES
import time
from random import randint
from math import pi, sin, cos

# BOARD IO
import board
import framebufferio
import sharpdisplay

# GUI
import displayio

class Grain:
  def __init__(self, bmp, size, resolution, x,y, vx=0,vy=0, verbose=False):
    self.bmp = bmp
    self.size = size
    self.size_range = range(-size, +size)
    self.resolution = resolution
    # NOTE that the four values below are in "grainspace", which is potentially much larger than
    # "bmpspace," ie, the pixels on the screen.
    self.x,  self.y  =  x,  y
    self.vx, self.vy = vx, vy
    self.pixels = []
    self.verbose = verbose

  def move_and_render(self, new_x,new_y):
    # erase old position
    self.render(color=0)
    # move
    self.x = new_x
    self.y = new_y
    # fill in new position
    self.render(color=1)

  def render(self, color=1):
    self.pixels = []
    for x_delta in self.size_range:
      for y_delta in self.size_range:
        self.bmp[self.x+x_delta, self.y+y_delta] = color
        self.pixels.append([self.x+x_delta, self.y+y_delta])

  def mock_render(self, x,y):
    pixels = []
    for x_delta in self.size_range:
      for y_delta in self.size_range:
        pixels.append([x+x_delta,y+y_delta])
    return pixels


class Sand:
  palette = displayio.Palette(2)
  palette[0] = 0x000000
  palette[1] = 0xffffff
  BLACK = 0
  WHITE = 1
  PHYSICS_RESOLUTION = 2           # additional resolution for calculating physics
  GRAVITY = 2 * PHYSICS_RESOLUTION # downward acceleration
  BOUNCE = .5                      # rebound factor after collision
  TERMINAL_VELOCITY = 8            # maximum downward velocity

  def __init__(self, display, dimensions, num_grains, size):
    self.display = display
    self.w, self.h = dimensions
    self.gw, self.gh = (self.w-size)*self.PHYSICS_RESOLUTION, (self.h-size)*self.PHYSICS_RESOLUTION
    self.gravity_direction = 2*pi #straight down
    self.grav_x = 0
    self.grav_y = -1
    self.grains = []
    self.bmp = displayio.Bitmap(self.w, self.h, 2)
    self.bmp.fill(0)
    tile = displayio.TileGrid(self.bmp, pixel_shader=self.palette)
    group = displayio.Group(max_size=1)
    group.append(tile)
    display.show(group)
    self.last_tick = time.monotonic()
    self.start_grains(num_grains, size)
  
  def start_grains(self, num_grains, size):
    self.grains = []
    locations = []
    while len(self.grains) < num_grains:
      y = randint(0+size, self.h-size)
      x = randint(0+size, self.w-size)
      if not len(locations):
        self.grains.append(Grain(self.bmp, size, self.PHYSICS_RESOLUTION, x,y,
                                 verbose=True))
      elif not (x,y) in locations:
        self.grains.append(Grain(self.bmp, size, self.PHYSICS_RESOLUTION, x,y))
        locations.append( (x,y) )
    for grain in self.grains:
      grain.render()

  def tick(self, tick_length):
    while time.monotonic() < self.last_tick+tick_length:
      pass
    self.last_tick = time.monotonic()
    if randint(0,100)>90:
      print("new gravity!")
      self.gravity_direction = randint(0,6)
      self.grav_x = -sin(self.gravity_direction)*self.GRAVITY
      self.grav_y = -cos(self.gravity_direction)*self.GRAVITY
    self.physics_tick()

  def physics_tick(self):
    for grain in self.grains:
      # update velocities
      grain.vx = min(grain.vx+self.grav_x, self.TERMINAL_VELOCITY)
      grain.vy = min(grain.vy+self.grav_y, self.TERMINAL_VELOCITY)
      # find the prospective new location
      new_x = int(grain.x + grain.vx)
      new_y = int(grain.y + grain.vy)
      blocked_pixels = self.blocked_pixels(grain, new_x, new_y)
      if (new_x, new_y) != (grain.x, grain.y) and blocked_pixels:
        # grain is moving to a new position that's blocked!
        block_direction = self.direction(grain.x, grain.y, blocked_pixels)
        if block_direction['y']:
          new_y = grain.y
          grain.vy = round(grain.vy/block_direction['y']*self.GRAVITY*self.BOUNCE)
        if block_direction['x']:
          new_x = grain.x
          grain.vx = round(grain.vx/block_direction['x']*self.BOUNCE)
      grain.move_and_render(new_x, new_y)

  def to_bmp(self, grid):
    return grid // self.PHYSICS_RESOLUTION

  def blocked_pixels(self, grain, x,y):
    check_pixels = [ x_y for x_y in grain.mock_render(x,y) if x_y not in grain.pixels ]
    blocked_pixels = []
    for check_x_y in check_pixels:
      try:
        if self.bmp[check_x_y]:
          blocked_pixels.append(check_x_y)
      except IndexError:
        # we went off the edge of the screen!
        blocked_pixels.append(check_x_y)
    return blocked_pixels
  
  def direction(self, origin_x, origin_y, relative_blocks):
    # since we only move one pixel at a time, we'll never be blocked on opposing sides
    absolute_blocks = [ (x-origin_x,y-origin_y) for x,y in relative_blocks ]
    x, y = map(
      lambda dirs: (-1,1)[sum(dirs)>0], # get sign of sums
      zip(*absolute_blocks)               # group Xs and Ys and feed to above lambda
    )
    return { 'x':x, 'y':y }
    

  def bound(self, _min, check, _max):
    return max(_min, min(check, _max))





if __name__ == "__main__":
  displayio.release_displays()
  spi = board.SPI()
  framebuffer = sharpdisplay.SharpMemoryFramebuffer(
    spi, board.D4,
    baudrate=8000000,
    width=144,
    height=168)
  sharp_display = framebufferio.FramebufferDisplay(framebuffer)
  sand = Sand(sharp_display, dimensions=(144,168), num_grains=10, size=2)
  while True:
    sand.tick(0.1)
