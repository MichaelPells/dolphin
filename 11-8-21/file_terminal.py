import subprocess
import time
import json
import os
import signal
from pathlib import Path

def loadSystem():
    outputs_last_modified = Path("engine_outputs.txt").stat().st_mtime

    engine = subprocess.Popen("py engine.py", shell=False)

    while Path("engine_outputs.txt").stat().st_mtime == outputs_last_modified: pass
    else:
        while len(open("engine_outputs.txt").read().splitlines()) < 1: pass
        else:
            global engine_properties
            engine_properties = list(json.loads("{"+open("engine_outputs.txt").readline().strip()+"}").values())[0]
            global engine_pid
            engine_pid = int(engine_properties["text"])
loadSystem()
    
def exitSystem():
    try: os.kill(engine_pid, signal.SIGTERM)
    except: pass

def exitAll():
    systems = open("running_engines.pid").read().strip().splitlines()
    for engine_pid in systems:
        try:
            os.kill(int(engine_pid), signal.SIGTERM)
            systems.remove(engine_pid)
        except: pass
    open("running_engines.pid", "w").write("\n".join(systems)+"\n")

Inputbase = {}

no = 0

while True:
    no += 1
    Input = input(">>> ")

    if Input == "leave":
        exit()

    elif Input == "exit":
        exitSystem()
        exit()

    elif Input == "exit all":
        exitAll()
        exit()

    elif Input == "reload":
        exitAll()
        loadSystem()
        

    Auto = {"no": str(no), "message": Input}

    Inputbase[str(no)] = {"timestamp": time.time(), "message": Input}
    
    Terminal = open("file_terminal.txt", "w")
    Terminal.write(json.dumps(Auto))
    Terminal.close()
