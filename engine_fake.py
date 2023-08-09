import copy
import datetime
import email.utils
import html
import http.client
import io
import mimetypes
import os
import posixpath
import select
import shutil
import socket # For gethostbyaddr()
import socketserver
import sys
import time
import urllib.parse
import contextlib
from functools import partial

from http import HTTPStatus

import argparse

import json
import requests
import threading
from pathlib import Path
from multiprocessing import Process


def output(*message):
    if len(message) > 0:
        Input = message[0]
        message = {"service": Input["service"], "level": Input["level"], "no": Input["no"], "code": message[1], "text": message[2], "timestamp": time.time()}
        open("engine_outputs.txt", "a").write('"'+str(message["timestamp"])+'": '+json.dumps(message)+'\n')

def outpu(*message):
    if len(message) > 0:
        message = {"service": None, "level": None, "no": "server", "code": message[0], "text": message[1], "timestamp": time.time()}
        open("engine_outputs.txt", "a").write('"'+str(message["timestamp"])+'": '+json.dumps(message)+'\n')


def start(**params):
    Input = params["handover"]
    if len(Input["flow"]) > 0: header = Input["flow"][0]
    else:
        output(Input, "CODE", "Incomplete parameters given!")
        return
    Input["flow"].pop(0)
    Input["level"] += 1

    allowed_headers_1 = ["client", "server"]
    if header in allowed_headers_1:
        if header == "client": run_client()
        elif header == "server":
            run_server(
                HandlerClass=handler_class,
                ServerClass=DualStackServer,
                port=args.port,
                bind=args.bind,
            )
        elif header == "test": test()
n = 0
def test():
    open("hello_test.txt", "w").close()
    open("hello_test.txt", "a").write(str(os.getpid())+"\n")
    while True:
        global n
        n += 1
        open("hello_test.txt", "a").write(str(n)+"\n")

def stop(**params):
    Input = params["handover"]
    if len(Input["flow"]) > 0: header = Input["flow"][0]
    else:
        output(Input, "CODE", "Incomplete parameters given!")
        return
    Input["flow"].pop(0)
    Input["level"] += 1

    allowed_headers_1 = ["client", "server"]
    if header in allowed_headers_1:
        if header == "server": close_server()

def a():
    open("hello_test.txt", "a").write(str(os.getpid())+"\n")
    while True:
        global n
        n += 1
        open("hello_test.txt", "a").write(str(n)+"\n")

def b(**params):
    open("hello_test.txt", "w").write(str(params))
    a()


def roll(service, handover={"flow": []}):   
    if service == "start": Process(target=b, kwargs=({"handover": handover, })).start()
    elif service == "stop": stop(handover=handover)
    elif service == "server": server(handover=handover)
    elif service == "browse": browse(handover=handover)
    elif service == "history": history(handover=handover)


def main():
    InputFlowBase = {}

    open("engine_outputs.txt", "w").close()


    open("hello.txt", "a").write("1\n")
    output({"service": None, "level": 0, "no": "0"}, __name__, str(os.getpid()))
    open("running_engines.pid", "a").write(str(os.getpid())+"\n")

    global Terminal
    global NewInput

    Terminal = ""
    NewInput = False

    def terminal():

        #Reading Input from the File Terminal:

        if os.path.exists("data/file_terminal.txt"): os.remove("data/file_terminal.txt")
        
        global terminal_last_modified
        terminal_last_modified = Path("file_terminal.txt").stat().st_mtime

        def hold_file_terminal(held=False):
            try:
                if not held:
                    open("data/file_terminal.txt", "x").close()
                    held = True
                Input = open("file_terminal.txt", "r+").read()
                return json.loads(Input)
            except: return hold_file_terminal(held)

        def release_file_terminal():
            #open("file_terminal.txt", "w").close()
            global terminal_last_modified
            terminal_last_modified = Path("file_terminal.txt").stat().st_mtime
            if os.path.exists("data/file_terminal.txt"):
                os.remove("data/file_terminal.txt")

        global Terminal
        global NewInput

        while True:    
            while Path("file_terminal.txt").stat().st_mtime == terminal_last_modified: pass
            else:
                Terminal_temp = hold_file_terminal()
                while NewInput: pass
                else:
                    Terminal = Terminal_temp
                    NewInput = True
                release_file_terminal()

    def dispatcher():

        """Dispatching Input"""

        global Terminal
        global NewInput

        allowed_services = ["start", "stop", "server", "browse", "history"]

        while True:
            if NewInput:
                Input = Terminal
                Input["flow"] = Input["message"].split(" ")
                Input["level"] = 0
                service = Input["flow"][0]
                Input["flow"].pop(0)
                if service in allowed_services:
                    Input["service"] = service
                    Input["level"] += 1
                    roll(service, Input)
                NewInput = False

       

    class process(threading.Thread):
       def __init__(self, service, handover={"flow": []}):
          threading.Thread.__init__(self)
          self.service = service
          self.handover = handover

       def run(self):
           if self.service == "terminal": terminal()
           elif self.service == "dispatcher": dispatcher()

    process("terminal").start()
    process("dispatcher").start()


