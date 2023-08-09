import subprocess
import os
import time

a = subprocess.Popen("py -m http.server", shell=False)
time.sleep(30)
print("a should close now!")

subprocess.Popen.terminate(a)
