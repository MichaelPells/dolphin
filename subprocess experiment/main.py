import subprocess
import os
import time

a = subprocess.Popen("py -m http.server", shell=True)

print(a.pid)
time.sleep(10)
subprocess.Popen.kill(a)
