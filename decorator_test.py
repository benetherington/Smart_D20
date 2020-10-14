import time

BOOT_TIME = time.time()

def refresh_safely(Cls):
  class NewCls(object):
    def safe_to_refresh(self):
      if (time.time() > self.last_refresh_time + 1):
        self.last_refresh_time = time.time()
        return True
      else:
        return False
    def __init__(self, *args, **kwargs):
      self.last_refresh_time = max(BOOT_TIME, time.time())
      self.oInstance = Cls(*args, **kwargs)
    def __getattribute__(self, s):
      try:
        x = super(NewCls, self).__getattribute__(s)
      except AttributeError:
        pass
      else:
        return x
      x = self.oInstance.__getattribute__(s)
      if type(x) == type(self.__init__) and self.safe_to_refresh():
        return x
      else:
        return lambda *args, **kwargs: print("wrapper failed")
  return NewCls




@refresh_safely
class Refresh():
  def __init__(self):
    pass
  def prnt(self, string):
    print(string)

ref = Refresh()
ref2 = Refresh()

ref.prnt("1 it's too early")
ref2.prnt("2 it's too early")
ref2.prnt("2 still too early")
time.sleep(1)

ref.prnt("1 now it's just right")
ref.prnt("1 it's too early again")
ref2.prnt("2 should be just right")
time.sleep(1)

ref.prnt("1 better again")
ref2.prnt("2 better again")

'''
expect:
failed
failed
failed
1 just right
failed
2 just right
1 better
2 better
'''