print("Hi...", end=" ")

import json
import requests
import time
from pathlib import Path

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

log_last_modified = Path("data/interface_log.txt").stat().st_mtime
while True:
    #receive request
    while Path("data/interface_log.txt").stat().st_mtime == log_last_modified:
        pass
    else:
        #time.sleep(0.5)
        log = read_interface_log()

        for sender in log.keys():
            if sender == "feedback":
                for title in log[sender].keys():
                    if title == "processes":
                        if log[sender][title] != running_processes: running_processes = log[sender][title]

                        if running_processes == ["server"]:
                            commandline = input(">>> ")
                            if commandline != "":
                                log["menu"]["commandline"] = commandline
                                open("data/interface_log.txt", "w").write(json.dumps(log))
                                log_last_modified = Path("data/interface_log.txt").stat().st_mtime
                                try: requests.get("http://127.0.0.1:8000/", allow_redirects=False, timeout=(0.5,0.001))
                                except: pass
            
            elif sender == "output":
                if len(log[sender]) > 0:
                    outputs = log[sender]
                    log[sender] = []
                    open("data/interface_log.txt", "w").write(json.dumps(log))
                    log_last_modified = Path("data/interface_log.txt").stat().st_mtime
                    
                    for output in outputs:
                        print(output)
                
            else:
                for title in log[sender].keys():
                    reply = log[sender][title]
                    if reply == None:
                        sender_messages = globals()[sender+"_messages"]
                        print(sender_messages[title], end="")
                        reply = input()

                        #write response
                        log[sender][title] = reply
                        open("data/interface_log.txt", "w").write(json.dumps(log))
                        log_last_modified = Path("data/interface_log.txt").stat().st_mtime


