import copy
import datetime
import email.utils
import html
import http.client
import io
import mimetypes
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
import signal
import threading
from pathlib import Path

from pathos.helpers import mp
Process = mp.Process

import dill

global modules
modules = [dill, copy, datetime, email.utils, html, http.client, io, mimetypes, posixpath, select, shutil, socket, socketserver, sys, time, urllib.parse, contextlib, partial, HTTPStatus, argparse, json, requests, signal, Path]

for module in modules:
    try: x = dill.dumps(module)
    except Exception as e: print(module.__name__+": "+str(e))
