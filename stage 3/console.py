from pathlib import Path

log_last_modified = Path("data/interface_log.txt").stat().st_mtime

print("Hi...", end=" ")

import json
import os
import requests
import time

info = "Welcome to Cross-device file copier!\n"
for i in info:
    print(i, end="")
    time.sleep(0.02)

menu_messages = {
    "start": "\nRun Program: ",
    }

client_messages = {
    "lastCoord": "Enter last coordinate of server (Press Enter key if unknown.): 192.x.x.",
    "files": "File(s): ",
    "reuse": "\nDo you have another file(s) to transfer? (Yes/No): "
    }

server_messages = {

    }

history_messages = {
    "option": "Choose an option: ",
    }


running_processes = []

def read_interface_log():
    try: return json.loads(open("data/interface_log.txt").read())
    except: return read_interface_log()

def hold_interface_log(held=False):
    try:
        if not held:
            open("data/interface_log - temp.txt", "x").close()
            held = True
        return json.loads(open("data/interface_log.txt").read())
    except: return hold_interface_log(held)

def release_interface_log(log=None, timestamp=False):
    if log != None: open("data/interface_log.txt", "w").write(json.dumps(log))
    if timestamp:
        global log_last_modified
        log_last_modified = Path("data/interface_log.txt").stat().st_mtime
    if os.path.exists("data/interface_log - temp.txt"): os.remove("data/interface_log - temp.txt")
    return True

while True:
    #receive request
    while Path("data/interface_log.txt").stat().st_mtime == log_last_modified:
        pass
    else:
        #time.sleep(0.5)
        log = hold_interface_log()
        released = False

        for sender in log.keys():
            if sender == "feedback":
                for title in log[sender].keys():
                    if title == "processes":

                        if "server" in log[sender][title] and "server" not in running_processes:
                            log["menu"]["commandline"] = "menu"
                            released = release_interface_log(log, True)
                            try: requests.get("http://127.0.0.1:8000/", allow_redirects=False, timeout=(0.5,0.001))
                            except: pass
                                
                        running_processes = log[sender][title]
            
            elif sender == "output":
                if len(log[sender]) > 0:
                    outputs = log[sender]
                    log[sender] = []
                    
                    for output in outputs:
                        print(output)

                    released = release_interface_log(log, True)
                
            else:
                for title in log[sender].keys():
                    reply = log[sender][title]
                    if reply == None:
                        sender_messages = globals()[sender+"_messages"]
                        print(sender_messages[title], end="")
                        reply = input()

                        #write response
                        log[sender][title] = reply
                        released = release_interface_log(log, True)

        if not released: release_interface_log(None, True)


