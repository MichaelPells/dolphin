import threading
import time
import sys

def start(**params):
    while True: print("Hello")

class process(threading.Thread):
    def __init__(self, service, handover=[]):
        threading.Thread.__init__(self)
        self.service = service
        self.handover = handover

    def start(self):
        threading.Thread.start(self)
        if self.service == "start":
            time.sleep(5)
            self.new_thread.sys.exit()

    def run(self):
        if self.service == "terminal": terminal()
        elif self.service == "dispatcher": dispatcher()

        elif self.service == "start":
            import start
            #start(handover=self.handover)
        elif self.service == "stop": stop(handover=self.handover)
        elif self.service == "server": server(handover=self.handover)
        elif self.service == "browse": browse(handover=self.handover)
        elif self.service == "history": history(handover=self.handover)

        elif self.service == "stop_server":
            time.sleep(5)
            x = 1/0

        elif self.service == "run_server_test":
            global running
            running = run_server_test()
            """run_server(
                HandlerClass=handler_class,
                ServerClass=DualStackServer,
                port=args.port,
                bind=args.bind,
            )"""

p = process("start", ["server"]).start()
print(p)








"""import multiprocessing
from multiprocessing import Process
import time

def f(**name):
    while True: print('hello',name)

if __name__ == "__main__":        
    Mine = Process(target=start, kwargs={"handover": ["server"],})
    Mine.start()

    time.sleep(5)
    Mine.terminate()
    print(Mine)

    Mine.join()

    
#process("terminal").start()
#process("dispatcher").start()"""





"""import shutil
tputfile = open("hello.py", "w")

shutil.copyfileobj(source, outputfile)

outputfile.flush()"""




"""import os

open("receive.py", "w").write("print(input('Hello: '))")
x = os.popen("Python receive.py")
print(x.read())
"""
