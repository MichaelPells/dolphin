import threading
import time

def main(): import engine

class process(threading.Thread):
   def __init__(self, name):
      threading.Thread.__init__(self)
      self.name = name
   def run(self):
      newThread(self.name)

def newThread(name):
   if name == "console": import console
   if name == "engine":
      time.sleep(5)
      main()

process("console").start()
process("engine").start()
