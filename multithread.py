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
from multiprocessing import Process
#import threading
from pathlib import Path

def f(**name):
    while True: print('hello', name)

if __name__ == '__main__':
    p = Process(target=f, kwargs={"handover": ["server"],})
    p.start()
   
    time.sleep(5)
    p.terminate()
    print(p)
    
    p.join()
