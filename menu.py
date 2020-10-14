from functools import partial, partialmethod
import pprint

pp = pprint.PrettyPrinter(indent=2)

class Menu:
'''
One Menu object should exist for each display. This object stores labels
and functions, lists them on external displays, and responds to button
presses.


The major "external" function is press(), which calls the function stored
in the selected button. Next() and previous() are also important, but are
generally stored in buttons and are called by press(), not an external
call.

__init__ can be passed an item_function list to get started quickly, but
load can also be called externally. This is usefull if the menu you want
to display has nested sub-menus as well. Use updater to generate partials
that can store nested menus. Note that use of updater requires referencing
this menu object, so you'll have to instantiate the object, then build
updater objects, then load them in.
'''
  page_length = 6

  def __init__(self, item_function_list=None):
    if item_function_list is not None:
      self.load(item_function_list)
    self.pages = []
    self.current_page_num = 0
    self.current_page = []
    

  '''
  EXTERNAL
  '''
  def press(self, button_number):
    # Calls the method stored in the selected button.
    button_number = int(button_number) # input() returns strings
    if button_number > len(self.current_page):
      print("Whoops, out of range!")
    else:
      self.current_page[button_number][1]()
  def updater(self, item_function_list):
    # Returns a partial that will load a nested menu. Use
    # menu_object.updater(nested_menu) as a function in your
    # item_function_list.
    return partial(self.load, item_function_list)

  '''
  SEMI-EXTERNAL
  '''
  def next(self):
    # increments the current page number and updates the display
    self.current_page_num = min(self.current_page_num+1, len(self.pages)-1)
    self.update_current_page()
  def previous(self):
    # decrements the current page number and updates the display
    self.current_page_num = max(self.current_page_num-1, 0)
    self.update_current_page()
  def load(self, item_function_list):
    '''
    Loads menu items. Usually called by __init__, but can be called
    externally if needed, usually when a nested menu is required.
    
    item_function_list is an array of touples containing the menu
    display label and the "callback" function paired with it.
    '''
    # buid pages, set us on page 0
    self.pages = self.chunk_with_pagination(item_function_list)
    self.current_page_num = 0
    # update the display
    self.update_current_page()

  '''
  INTERNAL
  '''
  def update_current_page(self):
    # Called after page changes. Updates self.current_page according
    # to the self.current_page_num, and then updates the display.
    self.current_page = self.pages[self.current_page_num]
    self.print()
  def print(self):
    # testing stand-in, will be replaced with display code
    for x in range(len(self.current_page)):
      print(f"Option {x}: {self.current_page[x][0]}")
  def chunk_with_pagination(self, to_chunk, chunked=None, page=None):
    '''
    Recursive function used to chunk up a raw list into pages. Used
    by __init__. Returns a list of lists (pages), self.page_length
    long, with next and/or previous buttons.
    '''
    if chunked == None:
      chunked = []
    if page == None:
      page = 0
    buttons = []
    # decide if previous button is required
    if page > 0:
      buttons.append(('previous', self.previous))
    # decide if next button is required
    if len(to_chunk) > self.page_length-len(buttons):
      # add a next button
      buttons.append(('next', self.next))
      # prepend menu items to fill up the rest of the spaces
      this_chunk = to_chunk[0:self.page_length-len(buttons)]
      chunked.append(this_chunk+buttons)
      del to_chunk[0:self.page_length-1]
      # get to work on the next page
      page += 1
      return self.chunk_with_pagination(to_chunk, chunked, page)
    else:
      # no next button is required, prepend the rest of the items
      this_chunk = to_chunk+buttons
      chunked.append(this_chunk)
      # And we're done!
      return chunked

# print("\n\nfive items")
# Menu( [( x, partial(print,f"you pressed {x}") ) for x in range(5)] )

# print("\n\nsix items")
# Menu( [( x, partial(print,f"you pressed {x}") ) for x in range(6)] )

# print("\n\nseven items")
# Menu( [( x, partial(print,f"you pressed {x}") ) for x in range(7)] )

range_menu = Menu()

first_menu = [( f"first {x}",
            partial(print,f"you pressed first {x}") ) for x in range(4)]
second_menu = [( f"second {x}",
            partial(print,f"you pressed second {x}") ) for x in range(4)]

full_menu = [ ("First menu", range_menu.updater(second_menu)),
              ("Second menu", range_menu.updater(second_menu)) ]

range_menu.load(full_menu)

while True:
  print("\n\n\n")
  select = input()
  range_menu.press(select)