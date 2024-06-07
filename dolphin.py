import socket
import sys
import socketserver
import socketio
import eventlet
import threading
import copy
import json

Settings = json.loads(open("./configurables/settings.json").read())
Port = int(Settings["port"])

dolphins = json.loads(open("./configurables/dolphins.json").read())

gateway = None

hosts = {}

ConnectionsBySID = {}
ConnectionsByGuest = {}
ConnectionsForDolphins = {
   "Dan": {},
   "Deb": {}
}

class Authentication():
   def __init__(self):
      # guest
      if sys.argv[2][0] == "1": # Change this condition to settings later
         guest = socketio.Client()

         def guest_handshake(data):
            GuestDolphin = data["GuestDolphin"]
            HostDolphin = data["HostDolphin"]
            host = ConnectionsBySID["HOST"]

            if host not in ConnectionsForDolphins[GuestDolphin]:
               ConnectionsForDolphins[GuestDolphin][host] = {}

            ConnectionsForDolphins[GuestDolphin][host][HostDolphin] = {
               "port": data["port"]
            }

            print("guest -------------------")
            print(ConnectionsBySID)
            print(ConnectionsByGuest)
            print(ConnectionsForDolphins)
         guest.on("handshake", guest_handshake)

         self.guest = guest

      # host
      if sys.argv[2][1] == "1": # Change this condition to settings later
         host = socketio.Server()
         server = socketio.WSGIApp(host)

         def connect(sid, environ, auth):
            # for key in environ:
            #    print(f"{key}:             {environ[key]}\n")

            guest = f"{environ['REMOTE_ADDR']}:{auth['Port']}"
            if guest not in ConnectionsByGuest:
               ConnectionsBySID[sid] = guest
               ConnectionsByGuest[guest] = sid
            else:
               raise socketio.exceptions.ConnectionRefusedError(f"Guest '{guest}' is connected already.")
         host.on("connect", connect)

         def disconnect(sid):
            if sid in ConnectionsBySID:
               guest = ConnectionsBySID[sid]
               del ConnectionsBySID[sid]
               del ConnectionsByGuest[guest]
         host.on("disconnect", disconnect)

         def host_handshake(sid, data):
            HostDolphin = data["HostDolphin"]
            GuestDolphin = data["GuestDolphin"]
            guest = ConnectionsBySID[sid]

            if guest not in ConnectionsForDolphins[HostDolphin]:
               ConnectionsForDolphins[HostDolphin][guest] = {}

            ConnectionsForDolphins[HostDolphin][guest][GuestDolphin] = {
               "port": data["port"]
            }
            ReturnHandshake(sid, GuestDolphin, HostDolphin)

            print("host -------------------")
            print(ConnectionsBySID)
            print(ConnectionsByGuest)
            print(ConnectionsForDolphins)
            print(sid)
         host.on("handshake", host_handshake)

         def ReturnHandshake(sid, GuestDolphin, HostDolphin):
            port = dolphins[HostDolphin]["port"]
            host.emit("handshake", {"GuestDolphin": GuestDolphin, "HostDolphin": HostDolphin, "port": port}, room = sid)

         self.host = host

         eventlet.wsgi.server(eventlet.listen(("", Port)), server) # Port here should be a variable (settings)

   # Issue: There must be a different guest for each connect
   def connect(self, host):
      address, port = host
      newguest = copy.deepcopy(self.guest)

      def connect():
         # for attr in dir(newguest):
         #    print(f"{attr}:            {newguest.__getattribute__(attr)}\n")

         ConnectionsBySID["HOST"] = f"{address}:{port}"
         ConnectionsByGuest[f"{address}:{port}"] = "HOST"
      newguest.on("connect", connect)

      def connect_error(error):
         try: del hosts[f"{newguest.host[0]}:{newguest.host[1]}"]
         except: pass
         print(error)
      newguest.on("connect_error", connect_error)

      def disconnect():
         try: del hosts[f"{newguest.host[0]}:{newguest.host[1]}"]
         except: pass
         print(f"{newguest.host[0]}:{newguest.host[1]} was disconnected.")
      newguest.on("disconnect", disconnect)
      
      try:
         newguest.connect(url = f"http://{address}:{port}", auth = {"Port": 5001}) # Replace 5001 with `Port` later.
      except: pass
      newguest.host = host
      hosts[f"{address}:{port}"] = newguest # Later, delete this entry when `connect_error` or `disconnect` events occur.

def InitiateHandshake(host, HostDolphin, GuestDolphin):
   try:
      guest = hosts[f"{host[0]}:{host[1]}"]
      port = dolphins[GuestDolphin]["port"]
      guest.emit("handshake", {"HostDolphin": HostDolphin, "GuestDolphin": GuestDolphin, "port": port})
   except KeyError:
      pass # Do something here

class Transmitter():
   def __init__(self, listener):
      self.listener = listener

      self.speaker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.speaker.connect(self.listener)

      self.speaking = True

   def speak(self, data="", encoding="utf-8"):
      data = bytes(data + "\n", encoding)

      self.speaker.sendall(data)

   def speakonce(self, data="", encoding="utf-8"):
      self.speak(data, encoding)

      self.stop()

   def stop(self):
      self.speaker.close()

class Handler(socketserver.StreamRequestHandler):
   def handle(self):
      # Authenticate
      listener = self.client_address
      if listener not in Authentication.ConnectionsByGuest: return  # Port should be an argument, here and everywhere else
      if not Authentication.ConnectionsByGuest[listener]["handshake_complete"]: return

      self.data = str(self.rfile.readline().strip(), "utf-8")
      print(self.data)
      try:
         speaker = Transmitter((listener[0], 8080))
      except:
         return # Later, report failure to reach listener
      speaker.speak("Hello")
      speaker.stop()

      # print(dir(self))
      # print(self.client_address)

class Receiver():
   def __init__(self, speaker = ("", 8080)):
      self.speaker = speaker

      self.listener = socketserver.ThreadingTCPServer(self.speaker, Handler)
      # self.listener.timeout = 0.5 # Later

      self.listening = False

   listeners = {}

   def listen(self):
      self.listening = True
      try:
         while self.listening:
            self.listener.handle_request()
         
      except KeyboardInterrupt:
         self.stop()

   def listenonce(self):
      self.listener.handle_request()

      self.stop()

   def stop(self):
      if self.listening:
         self.listening = False
         try: Transmitter(self.speaker).speakonce() # Using up the last .handle_request(), if any from listen().
         except: pass
         print("trying to close the server")
         self.listener.server_close()
         print("Server stopped!")

class thread(threading.Thread):
   def __init__(self, service, args = {}):
      threading.Thread.__init__(self)
      self.service = service
      self.args = args

   def run(self):
      if self.service == "Authentication":
         global gateway
         gateway = Authentication()

      elif self.service == "StartListener":
         address = dolphins[self.args["dolphin"]]["address"]
         port = dolphins[self.args["dolphin"]]["port"]
         listener = Receiver((address, port))
         Receiver.listeners[self.args["dolphin"]] = listener

         listener.listen()

      elif self.service == "StopListener":
         Receiver.listeners[self.args["dolphin"]].stop()




thread("Authentication").start()
thread("StartListener", args = {"dolphin": sys.argv[1]}).start()

if sys.argv[2][0] == "1":
   host = ("localhost", 5000)
   gateway.connect(host)
   while not hosts[f"{host[0]}:{host[1]}"].connected: pass # Is this really waiting??? Or do we even need to wait?
   else:
      InitiateHandshake(host, "Dan", "Deb")
# import time
# time.sleep(5)
# thread("StopListener", args = {"port": 8080}).start()