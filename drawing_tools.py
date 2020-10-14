from adafruit_display_text.label import Label

'''
PIXELS
'''
def bound(low, high, value):
  '''bounds value by high and low'''
  return max(low, min(high, value))
def bounded_pixel(display, x,y, color=1):
  '''adds a pixel to display.background bitmap, bounded by display edges'''
  x = int(display.bound(0, display.WIDTH-1, x))
  y = int(display.bound(0, display.HEIGHT-1, y))
  display.background[x, y] = color

'''
ELEMENTS
'''
def draw_h_line(display, x,y,w, color=1):
  '''draws a horizontal line, starting at (x,y), continuing for w pixels'''
  for xx in range(x, x+w):
    display.bounded_pixel(xx, y, color)
def draw_v_line(display, x,y,h, color=1):
  '''draws a vertical line, starting at (x,y), continuing for h pixels'''
  for yy in range(y, y+h):
    display.bounded_pixel(x, yy, color)
def draw_box(display, x,y,w,h, color=1):
  '''draws four lines to form an empty rectangle of size (w,h), with upper left corner at (x,y)'''
  draw_h_line(display, x,   y,   w, color) # top
  draw_h_line(display, x,   y+h, w, color) # bottom
  draw_v_line(display, x,   y,   h, color) # left
  draw_v_line(display, x+w, y,   h, color) # right
def draw_hatched_area(display, x,y,w,h, offset=0, size=2, color=1):
  '''
    Draws a checkerboard pattern in a rectangular area of size (w,h), with upper left corner at
    (x,y). Checkerboard squares contain size number of pixels, with upper left corner of the first
    square at (x+offset,y)
  '''
  off_adj = (size # offset of 0 results in "centered" hatch
             -x # start first box at the X coord, not the left screen edge
             -offset) # easier to make offset move things right
  for xx in range(x, x+w):
    for yy in range(y, y+h):
      xchecked = (xx+off_adj)%size >= size/2
      ychecked = (yy+off_adj)%size >= size/2
    if xchecked != ychecked: # xor
      display.bounded_pixel(xx,yy, color)
def dimensions(label):
  ''' takes a label and returns its bounding box x, y, w and h '''
  bx, by, bw, bh = label.bounding_box
  bw, bh = (bw*label.scale, bh*label.scale) # adjust for scale
  bx, by = (bx*label.scale, by*label.scale)
  return bx, by, bw, bh

'''
STRUCTURES
'''
def draw_row_lines(display, num_rows):
  '''draws horizontal lines to divide an even num_rows across the entire display height'''
  row_height = int(display.HEIGHT/num_rows)
  for i in range(1, num_rows+1): # skip drawing a line at the top
    for x in range(0, display.WIDTH-1):
      bounded_pixel(display, x,row_height*i)
def draw_padded_row_lines(display, num_rows=18, padding=4, prime_color=1, pad_color=None):
  '''draws horizontal lines to divide an even num_rows across a subset of display height with
     hatched areas top and bottom of height padding'''
  if pad_color is None:
    try:
      pad_color = display.ORANGE
    except ValueError:
      pad_color = 1
  row_height = int(display.HEIGHT/num_rows)
  horz_list = [padding+row_height*x for x in range(1, num_rows)]
  for y in horz_list:
    draw_h_line(display, 0,y,display.WIDTH, prime_color)
  # hatched areas
  draw_hatched_area(display, 0,0,                     display.WIDTH,padding, pad_color)
  draw_hatched_area(display, 0,display.HEIGHT-padding,display.WIDTH,padding, pad_color)
def display_options_rows(display, num_rows, options=None, rich_options=None,
                         top_padding=0, ani_clock=0):
  '''
    One of the heavy lifters! Displays button options in rows.
    num_rows is the number of rows on the display, whether or not they're getting options.
    options is a list of strings to display with default fonts and scaling.
    rich_options can be used instead to specify both font and scale. This argument should be a list
    of lists of dicts. Each dict should specify option string, font, and scale int. Each inner list
    should contain all the dicts that will be displayed on a single row. This looks like:
      [
        [
          {"option": "Intelligence", "font": f["knxt-20"], "scale": 1},
          {"option": "+1", "font": f["knxt-20"], "scale": 2}
        ],
        [
          {"option": "Dexterity", "font": f["knxt-20"], "scale": 1},
          {"option": "-1", "font": f["knxt-20"], "scale": 2}
        ]
      ]
    top_padding is the number of pixels to leave blank above the first row.
    ani_clock is only used for the SHARP display, and tells us what frame we're on for scrolling
    large labels.
  '''
  if options is not None:
    rich_options = [ [{"option": option, "font": display.LABEL_FONT, "scale": display.LABEL_SCALE}]
                                                                            for option in options ]
  else:
    if rich_options is None:
      raise ValueError("display_options_rows requires either options or rich_options argument.")
  if len(rich_options[0]) > 2:
    raise ValueError("display_options_rows has not implemented >2 columns yet")

  '''CREATE LABELS'''
  rows = {"column_max_widths": [0 for column in rich_options[0]],
          "row_min_widths": []} # we will later add row_num keys to store lists of labels
  for row_num, row_options in enumerate(rich_options):
    # row_options is a list of one or two rich option dicts to display on the same row
    this_row = []
    this_row_width = 0
    for col_num, rich_option in enumerate(row_options):
      # create labels for each option
      label = Label(text=rich_option["option"],
                    font=rich_option["font"], scale=rich_option["scale"])
      bx, by, bw, bh = dimensions(label)
      rows["column_max_widths"][col_num] = max(rows["column_max_widths"][col_num], bw)
      this_row.append({"label": label, "bx": bx, "by": by, "bw": bw, "bh": bh})
      this_row_width += bw
    # save this label or pair of labels, as well as their cumulative width
    rows[row_num] = this_row
    rows["row_min_widths"].append(this_row_width)
  # rows now contains "column_max_widths", which is an array containing ints representing the
  # width of the largest item in each column, and "row_min_widths", which is an array containing
  # ints representing the width of all glyphs in each row. rows also contains integer keys for each
  # row, and values containing dicts with labels and their bounding box x,y,w,h dimensions. This
  # looks like:
  # rows = {
  #           "column_max_widths": [80,25],
  #           "row_min_widths": [100, 150, 92],
  #           0: {"label": label_object, "bx": 0, "by": 5, ...}
  #           1: {"label": label_object, "bx": 0, "by": 5, ...}
  #           2: {"label": label_object, "bx": 0, "by": 5, ...}
  #        }
  '''DETERMINE COLUMN LOCATIONS'''
  column_centers = []
  for max_width in reversed(rows["column_max_widths"]):
    # max_width is an int representing the maximum space this column will take up. We will set the
    # rightmost column as small as possible, then center justify the (optional) left column in the
    # remaining space. This math currrently does not work on more than one column!
    column_centers.append(int(
                              display.WIDTH # start from the right
                              - max_width/2 # the center of this column
                              # now account for any columns to the right
                              - (
                                  (
                                    display.WIDTH - sum(column_centers) # half the occupied space
                                  ) * 2                     # all of the space occupied by glyphs
                                  - ( 4                     # column padding ...
                                      * len(column_centers) # ... for each column to the right
                                    )
                                ) * len(column_centers)     # negate term if first column
                              # finally, center the label
                              - 4                       # add padding to the right
                              / ( 2                     # center of the empty space
                                  - len(column_centers) # first column gets right justified
                                )
                         )   )
  column_centers = list(reversed(column_centers)) # this was built right-to-left
  '''DISPLAY LABELS'''
  row_height = display.HEIGHT - (top_padding*2) / num_rows
  just_rows = { k:v for k,v in rows.items() if isinstance(k, int) }
  for row_num, labels_dimensions in just_rows.items():
    # labels_dimenions is a list of one or two label/dimentions dicts to display on row row_num
    # calculate animation offset
    if (len(labels_dimensions) == 1
        and labels_dimensions[0]["bw"]-50 > display.WIDTH):
      # animate big boys slowly
      ani_offset = int( ani_clock*(bw-display.WIDTH) )
    elif labels_dimensions[0]["bw"] > display.WIDTH:
      # animate small boys quickly
      double_clock = -abs(ani_clock*2)+1
      triple_clock = -abs(double_clock*2)+1
      quad_clock = -abs(triple_clock*2)+1
      ani_offset = int( quad_clock*(bw-display.WIDTH) )
    else:
      ani_offset = 0
    for col_num, label_dimension in enumerate(labels_dimensions):
      label = label_dimension["label"]
      # place label in the correct row
      label.y = int(
                      row_num*row_height # row number offset
                      + top_padding      # pixels to leave blank at the top
                      + row_height/2     # center of the row
                   ) # bounding box origin is already centered on text height
      # place label in the correct column
      label.x = int(
                      column_centers[col_num] # center of the column
                      - label_dimension["bw"] # center of the bounding box width
                      + ani_offset
                   )
      display.layers[2].append(label) # layers[2] is button labels
def display_nav(display, nav_options, font=None, scale=None, num_rows=5):
  '''
    One of the heavy lifters! Displays up to three nav_options strings, in order, at the bottom of
    the screen. Include an empty string in the nav_options array to skip a place.
    Intended for SHARP display.
  '''
  if font is None:
    font = display.BUTTON_FONT
  if scale is None:
    scale = display.BUTTON_SCALE
  nav_row_y = display.HEIGHT * num_rows-1/num_rows
  nav_column_width = display.WIDTH/3
  nav_column_centers = [
                        nav_column_width*0 + nav_column_width/2,
                        nav_column_width*1 + nav_column_width/2,
                        nav_column_width*2 + nav_column_width/2
                       ]
  for i, option in enumerate(nav_options):
    label = Label(text=option, font=font, scale=scale)
    _, _, bw, _ = dimensions(label)
    label.y = int(nav_row_y)
    label.x = int(
                  nav_column_centers[i] # find correct column start
                  + nav_column_width/2  # find center of column
                  + bw/2                # center text in column
                 )
    display.layers[1].append(label) # layers[1] is nav interface
# def display_battery(display, x,y,h):
#   ''' Displays a battery icon of height h, with the top center at (x,y) '''
#   pass

# def draw_padded_grid(self, refresh_now=False):
#   # hatched area on top
#   self.draw_hatched_area(0, 0, self.WIDTH,4, self.ORANGE)
#   # horizontal lines dividing nine vertical button labels
#   horz_list = [4+32*x for x in range(1, 9)]
#   for y in horz_list:
#     self.draw_h_line(0, y, self.WIDTH, self.ORANGE)
#   # hatched area on bottom
#   self.draw_hatched_area(0, 293, self.WIDTH, 4, self.ORANGE)
#   # line down center dividing left and right button labels
#   self.draw_hatched_area(63, 0, 4, self.HEIGHT, self.BLACK)
#   if refresh_now:
#     self.refresh()
