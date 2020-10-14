# pylint: skip-file

import board
import displayio
import framebufferio
import sharpdisplay
import adafruit_il0373
import busio
from analogio import AnalogIn
import digitalio
import gamepad
import time

import adafruit_imageload
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font

'''
INIT BATTERY
'''
bat_voltage = AnalogIn(board.VOLTAGE_MONITOR)
def get_battery_percentage():
  vBat = bat_voltage.value*3.3/65536*2
  return round((vBat-3.3)*(4.2-3.3)*100)

'''
INIT DISPLAYS
'''
displayio.release_displays()
bus = board.SPI()

font = bitmap_font.load_font("fonts/bitbuntu.bdf")

# config SHARP
sharp_chip_select = board.A0
sharp_disp_width = 144
sharp_disp_height = 168

# config e-ink
eink_chip_select = board.A1
eink_data_command = board.A2
# eink reset
# eink busy
EINK_FLEXIBLE = False
eink_highlight = 0xff0000 # third color is red (0xff0000)
EINK_ROTATION = 90
eink_disp_width = 128
eink_disp_height =296

# initialize e-ink display
eink_bus = displayio.FourWire(bus, command=eink_data_command, chip_select=eink_chip_select,
                                 reset=None, baudrate=1000000)
 
time.sleep(1)  # Wait a bit
e_inkdisplay = adafruit_il0373.IL0373(eink_bus, width=eink_disp_height, height=eink_disp_width,
                                      swap_rams=EINK_FLEXIBLE, busy_pin=None, rotation=EINK_ROTATION, 
                                      highlight_color=eink_highlight)
displayio.release_displays()

# initialize sharp display
framebuffer = sharpdisplay.SharpMemoryFramebuffer(bus, sharp_chip_select, baudrate=8000000,
                                                  width=sharp_disp_width, height=sharp_disp_height)
sharp_display= framebufferio.FramebufferDisplay(framebuffer, auto_refresh=True)



'''
EINK DEMO
g = displayio.Group()
 
# Display a ruler graphic from the root directory of the CIRCUITPY drive
f = open("/display-ruler.bmp", "rb")
 
pic = displayio.OnDiskBitmap(f)
# Create a Tilegrid with the bitmap and put in the displayio group
t = displayio.TileGrid(pic, pixel_shader=displayio.ColorConverter())
g.append(t)
 
# Place the display group on the screen
eink_display.show(g)
 
# Refresh the display to have it actually show the image
# NOTE: Do not refresh eInk displays sooner than 180 seconds
# eink_display.refresh()
print("refreshed")
 
time.sleep(180)
print("sleep over")
'''


# initialize background bitmap
background_bitmap = displayio.Bitmap(sharp_disp_width, sharp_disp_height, 2)
palette = displayio.Palette(2)
palette[0] = 0x000000
palette[1] = 0xffffff
background_grid = displayio.TileGrid(background_bitmap, pixel_shader=palette)
# initialize the top-level group
background_nav_options = displayio.Group(max_size=3)
background_nav_options.append(background_grid)
background_nav_options.append(displayio.Group(max_size=1))
background_nav_options.append(displayio.Group(max_size=1))

def bound(low, high, value):
  return max(low, min(high, value))

def bounded_pixel(x,y):
  x = int(bound(0, sharp_disp_width-1, x))
  y = int(bound(0, sharp_disp_height-1, y))
  background_bitmap[x, y] = 1

def draw_box(x, y, w, h):
  # top
  for xx in range(x, x+w):
    bounded_pixel(xx, y)
  # bottom
  for xx in range(x, x+w):
    bounded_pixel(xx, y+h)
  # left
  for yy in range(y, y+h):
    bounded_pixel(x, yy)
  # right
  for yy in range(y, y+h):
    bounded_pixel(x+w, yy)

def draw_corner_dots():
  corners = [(x,y) for x in [0, sharp_disp_width-1] for y in [0, sharp_disp_height-1]]
  for corner in corners:
    background_bitmap[corner[0], corner[1]] = 1

def draw_row_lines(num_rows):
  row_height = int(sharp_disp_height/7)
  for i in range(1, num_rows+1): # skip drawing a line at the top
    for x in range(0, sharp_disp_width-1):
      bounded_pixel(x,row_height*i)

def build_option_rows(options, ani_clock):
  # make a new group
  options_group = displayio.Group(max_size=6)
  # determine the height of each row and the correct scale
  row_height = int(sharp_disp_height/7)
  # build labels
  for i, option in enumerate(options):
    label = Label(font=font, text=option, scale=2)
    bx, by, bw, bh = label.bounding_box
    bw, bh = (bw*label.scale, bh*label.scale) # adjust for scale
    bx, by = (bx*label.scale, by*label.scale)
    # calculate animation offset
    if bw-50 > sharp_disp_width:
      # animate big boys slowly
      ani_offset = int( ani_clock*(bw-sharp_disp_width) )
    elif bw > sharp_disp_width:
      # animate small boys quickly
      double_clock = -abs(ani_clock*2)+1
      triple_clock = -abs(double_clock*2)+1
      quad_clock = -abs(triple_clock*2)+1
      ani_offset = int( quad_clock*(bw-sharp_disp_width) )
    else:
      ani_offset = 0
    # center the text, add animation offset
    label.x = int(
                    sharp_disp_width/2 # center of the display
                    - bw/2 # center of the bounding box
                    + ani_offset
                  )
    # place text in correct row
    label.y = int(
                    i*row_height # row number offset
                    + (row_height/2) # center of the row
                  ) # bounding box origin is already centered on text height
    options_group.append(label)
  return options_group

def build_nav_buttons(_next=True, _prev=True):
  nav_row_y = int(sharp_disp_height*13/14)
  nav_group = displayio.Group(max_size=3)
  if _next:
    label = Label(font=font, text="Next", scale=2)
    bx, by, bw, bh = label.bounding_box
    bw, bh = (bw*label.scale, bh*label.scale) # adjust for scale
    bx, by = (bx*label.scale, by*label.scale)
    # center the text
    label.x = int(
                    sharp_disp_width/4 # center of this half of the navbar
                    - bw/2 # center of the bounding box
                  )
    # place text in correct row
    label.y = int(nav_row_y)
    # find best fit
    nav_group.append(label)
  if _prev:
    label = Label(font=font, text="Prev", scale=2)
    bx, by, bw, bh = label.bounding_box
    bw, bh = (bw*label.scale, bh*label.scale) # adjust for scale
    bx, by = (bx*label.scale, by*label.scale)
    # center the text
    label.x = int(
                    sharp_disp_width*3/4 # center of this half of the navbar
                    - bw/2 # center of the bounding box
                  )
    # place text in correct row
    label.y = int(nav_row_y)
    # find best fit
    nav_group.append(label)
  # draw vertical divider
  if _next or _prev:
    for y in range( int(sharp_disp_height*6/7), sharp_disp_height):
      bounded_pixel(int(sharp_disp_width/2), y)
  else:
    nav_group.append(display_battery_percentage())
  return nav_group

def display_battery_percentage():
  nav_row_y = int(sharp_disp_height*13/14)
  label = Label(font=font, text=f"{get_battery_percentage()}%")
  label.y = nav_row_y
  label.x = int( sharp_disp_width/2 - label.bounding_box[2]/2 )
  return label



page1 = ["Sword", "Club", "Daggar"]
page2 = ["Magic Missile", "Fireball", "Heal", "Curse"]
pages = [page1, page2]
draw_row_lines(len(page1))
background_nav_options[1] = build_nav_buttons()
sharp_display.show(background_nav_options)

ani_clock = 0
ani_direction = 1



pad = gamepad.GamePad(
                       digitalio.DigitalInOut(board.D13)
                     )

current_page = 0
cleared = True
options = pages[current_page]

while True:
  ani_clock += ani_direction*0.05
  if abs(ani_clock) > 2:
    ani_direction = -ani_direction
  buttons = pad.get_pressed()
  if buttons and cleared:
    cleared = False
    current_page = (current_page+1)%2
    options = pages[current_page]
  if not buttons and not cleared:
    cleared = True
  background_nav_options[2] = build_option_rows(options, ani_clock/2)
