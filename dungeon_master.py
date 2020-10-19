import json

import sys
import storage
import adafruit_hashlib as hashlib

import drawing_tools as draw

class DungeonMaster():
  LOADED_CHAR_DIGEST_FILEPATH = "./NO_TOUCH/loaded_character.txt"
  def __init__(self, eink, sharp, buttons,
                     character_filepath, menu_structure_filepath):
    self.eink = eink
    self.sharp = sharp
    self.buttons = buttons
    self.REQUESTED_CHARACTER_FILEPATH = character_filepath # pylint: disable=invalid-name
    self.MENU_STRUCTURE_FILEPATH = menu_structure_filepath # pylint: disable=invalid-name
    self.character = None
    self.menu_structure = None
    self.eink_items = None
    self.sharp_items = None
    self.load_data()

  def load_data(self):
    '''
      Loads in character_sheet json data, checking to see if there have been any changes that would
      require an e-ink refresh.
    '''
    # GET NEW CHARACTER SHEET CHECKSUM
    requested_hash = hashlib.sha256()
    with open(self.REQUESTED_CHARACTER_FILEPATH) as f:
      # load requested character_sheet file and create checksum
      char_json = f.read()
      requested_hash.update(char_json.encode('utf-8'))
      self.character = json.loads(char_json)
    print(f"requested character hash digest: {requested_hash.digest()}")
    # GET LOADED CHARACTER SHEET CHECKSUM
    try:
      with open(self.LOADED_CHAR_DIGEST_FILEPATH, "rb") as f:
        # load checksum of the character_sheet file last time we accessed it
        loaded_hash_digest = f.read()
        print(f"loaded character hash digest: {loaded_hash_digest}")
    except OSError as error:
      if error.args[0] == 2: # pylint: disable=no-member
        # File not found error. No problem, we'll need to update the loaded character, and we'll
        # create a new file when that happens.
        loaded_hash_digest = None
        print("No LOADED_CHAR_DIGEST_FILE found.")
      else:
        # woof, it was something else, better raise a fuss
        raise
    # DECIDE IF UPDATE REQUIRED
    if loaded_hash_digest != requested_hash.digest():
      # The character_sheet got updated, which means we'll have to update the e-ink display when
      # we've finished parsing the data.
      eink_refresh_required = True
      print("Hash digests don't match. E-ink update required.")
    else:
      eink_refresh_required = False
      print("Hash digests match. No E-ink update required.")
    # LOAD MENU CONFIG
    with open(self.MENU_STRUCTURE_FILEPATH) as f:
      menu_config = json.load(f)

    # LOAD DATA PER CONFIG
    self.eink_items = path_to_data(menu_config["eink"]["items"], self.character)
    self.sharp_menu = 

    if eink_refresh_required:
      # UPDATE EINK
      self.update_eink()
      # SAVE NEW HASH
      try:
        storage.remount('/', readonly=False) # steal write access from USB
        with open(self.LOADED_CHAR_DIGEST_FILEPATH, "wb") as f:
          f.write(requested_hash.digest())
        storage.remount('/', readonly=True) # hand write access back to USB
      except RuntimeError as error:
        if error.args == ("Cannot remount '/' when USB is active.",):
          print("USB is active, I can't save requested_hash.")

  def update_eink(self):
    try:
      self.eink.wake_up()
      draw.display_options_rows(self.eink, self.eink_items)
      draw.draw_padded_row_lines(self.eink)
    except Exception as e: #pylint: disable=broad-except,invalid-name
      # use serial out so we don't do an extra e-ink refresh
      sys.print_exception(e) # pylint: disable=no-member
    finally:
      self.eink.sleep()
  def main_menu(self):
    self.sharp.wake_up()

def path_to_data(path, tree, crumbs=None):
  '''
    Recursive function that initially takes a directory path and a data tree, then walks down the
    tree, following the directory path, passing the next steps to a new instance of itself. When it
    finally gets to the end of the directory path, it returns a list of the values therein.

    Recursion is horrendous, so I've used a map analogy to name variables relating to the map set
    out in the menu_structure file, and a tree analogy to name variables relating to the
    character_sheet we're searching.

    menu_structure variables:
    -- path is a list of strings and/or lists. It represents the steps ahead of us to reach the data
       we want. At each recusion, the step we just followed gets cut off, and the next steps are
       passed along. A path can fork, ie contain another list.
    -- signpost is a string. It is the current step we're handling. It might be a string to match
       exactly. It might be a string to match everything except. It might tell us to select
       everything we can. This probably needs to get changed from a string to a regex.
    -- crumbs is a list of strings. Like a trail of breadcrumbs through the woods, it represents the
       steps we've taken to get where we are. At each recursion, the step we just followed gets
       appended to crumbs.

    character_sheet variables:
    -- tree is a dictionary. The intention is to pull it straight from character_sheet.json.
    -- signpost is a touple, representing a single key/value pair from tree. If signpost is the last
       item in path, branch could represent one of the bits of data requested by path.
    -- leaves_and_crumbs is a list of dictionaries. It represents the parts of the tree ahead and
       behind this instance of path_to_data, but not the path. Each item in the list
       (leaf_and_crumb) contain a "leaves" key and a "crumbs" key. leaves are either the next subset
       of tree (branches) to operate on (if len(path) > 1) or successfully selected data (if
       len(path) == 1). crumbs are the same as defined above.

    The search process follows three steps: determine signpost, select leaf, and return or recurse.
    Each should be fairly self explanatory, though note that during determine signpost we may decide
    to skip select leaf. That happens when we've hit a fork in the path, and instead of selecting a
    leaf, we spin up two new recursive instances of load_data.
  '''
  if crumbs is None:
    crumbs = []
  leaves_and_crumbs = []
  ''' DETERMINE SIGNPOST '''
  if isinstance(path[0], list):
    # there's a fork in the path; follow each without selecting
    signpost = None
  else:
    # We'll be selecting data or the next branch.
    operators_signpost = path[0].split(":")
    if len(operators_signpost) == 1:
      # no operators were passed
      signpost = operators_signpost[0]
      operators = ""
    elif len(operators_signpost) == 2:
      # operators were passed
      operators, signpost = operators_signpost
  ''' SELECT LEAF '''
  if signpost is not None: # ie we're not forking
    if signpost == "each":
      # select all branches
      for branch in tree.items():
        new_crumbs = crumbs.copy()
        new_crumbs.append(branch[0])
        leaves_and_crumbs.append( {"crumbs": new_crumbs, "leaves": branch[1],
                                    "operators": operators} )
    elif "!" in operators:
      # select all keys that don't match
      for branch in tree.items():
        if signpost != branch[0]:
          new_crumbs = crumbs.copy()
          new_crumbs.append(branch[0])
          leaves_and_crumbs.append( {"crumbs": new_crumbs, "leaves": branch[1],
                                      "operators": operators} )
    else:
      # select all keys that match
      for branch in tree.items():
        if signpost == branch[0]:
          new_crumbs = crumbs.copy()
          new_crumbs.append(branch[0])
          leaves_and_crumbs.append( {"crumbs": new_crumbs, "leaves": branch[1],
                                      "operators": operators} )
  ''' RETURN OR RECURSE '''
  if signpost is None:
    # we're forking, no leaves have been set
    branches = []
    for fork in path[0]:
      branches += path_to_data([fork], tree, crumbs)
    return branches
  if len(path) == 1:
    # we've reached the final step, leaves are data to return
    data_to_return = []
    for leaf_and_crumb in leaves_and_crumbs:
      if "<" in leaf_and_crumb['operators']:
        key = leaf_and_crumb['crumbs'][-2] # -1 is this signpost, need to go back one more
      else:
        key = leaf_and_crumb['crumbs'][-1]
      value = leaf_and_crumb['leaves']

      data_to_return.append( {key: value} )
    return data_to_return
  else:
    # there are more steps to go, leaves are branches to recurse upon

    branches = []
    for branch_and_crumb in leaves_and_crumbs:
      branches += path_to_data( path[1:],
                              branch_and_crumb['leaves'],
                              branch_and_crumb['crumbs']
                            )
    return branches
