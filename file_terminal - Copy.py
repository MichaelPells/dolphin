import subprocess
import time
import json
import os
import signal
from pathlib import Path
from multiprocessing import Process

def f():
    open("hello.txt", "a").write("2\n")
    import engine_fake
    
if __name__ == "__main__":
    p = Process(target=f, args=())
    p.start()
    print(p.pid)
