import json

class DungeonMaster():
  loaded_character = "./state_data/loaded_character.json"
  def __init__(self,eink, sharp, buttons, character):
    self.eink = eink
    self.sharp = sharp
    self.buttons = buttons
    self.requested_character = character

  def update_eink(self):
    with open(loaded_character) as f:
      loaded_character = json.load(f)
    if self.requested_character == self.loaded_character:
      # e-ink doesn't need to get updated
      return
    # update e-ink
    abilities = 
    try:
      eink.wake_up()
    except Exception as e:
      sys.print_exception(e)
  def main_menu(self):
    self.sharp.wake_up()
