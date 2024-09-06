import json
import sys
import requests
import subprocess
import os
from urllib.parse import urlparse

Settings = json.loads(open("./configurables/settings.json").read())

url = sys.argv[1] if len(sys.argv) > 1 else f'http://127.0.0.1:{int(Settings["Port"])}'
URL = urlparse(url)

try:
    # Asserting that Dolphin@url is online
    remote = True
    ping = requests.post(url, data="ping")
    assert (ping.status_code == 200 and ping.json()["code"] == 0)
except Exception:
    # Attempt to launch Dolphin, if target is on localhost
    if URL.hostname == "127.0.0.1" or URL.hostname == "localhost":
        remote = False
        Dolphin = subprocess.Popen(["dolphin.py"], cwd=os.getcwd(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
        # If error starting Dolphin
        if Dolphin.stderr.readline().strip():
            print("Dolphin failed while starting.")
            sys.exit(1)
    else:
        print("Dolphin failed to respond.")
        sys.exit(1)

def Exit():
    print("Exiting...")
    # Do a proper logout here,
    # or even kill Dolphin if necessary.
    sys.exit(0)

local_commands = {
    "exit": Exit
}

if remote:
    while True:
        Input = input("\ndolphin >>> ")

        command = Input.split(" ")[0]
        if command in local_commands:
            Output = local_commands[command]()
        else:
            response = requests.post(url, data=Input)
            Output = response.text.strip()

        print(Output)
else:
    while True:
        Input = input("\ndolphin >>> ")

        command = Input.split(" ")[0]
        if command in local_commands:
            Output = local_commands[command]()
        else:
            Dolphin.stdin.write(Input + '\n')
            Dolphin.stdin.flush()

            content_length = int(Dolphin.stdout.readline())
            Output = Dolphin.stdout.read(content_length + 1).strip()

        print(Output)
    
