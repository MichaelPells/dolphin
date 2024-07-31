import socket
import sys
import socketserver
import socketio
import eventlet
import threading
import copy
import json

Settings = json.loads(open("./configurables/settings.json").read())
Interface = Settings["Interface"] # Is the term 'Interface' correct for this usage?
Port = int(Settings["Port"])

dolphins = json.loads(open("./configurables/dolphins.json").read())

gateway = None

hosts = {}

ConnectionsBySID = {}
ConnectionsByPair = {}
ConnectionsForDolphins = {
   "Dan": {},
   "Deb": {}
}
ConnectionsByAddress = {
      "Dan": {},
      "Deb": {}
}

class Authentication():
   def __init__(self):
      # guest
      if sys.argv[2][0] == "1": # Change this condition to Settings later
         guest = socketio.Client()

         def guest_handshake(data):
            guest_dolphin = data["guest_dolphin"]
            host_dolphin = data["host_dolphin"]
            host = ConnectionsBySID["HOST"]

            ConnectionsByAddress[guest_dolphin][f'{host.split(":")[0]}:{data["speaker_port"]}'] = {"pair": host,
                                                                                                 "dolphin": host_dolphin
                                                                                                 }
            listener_socket = Transmitter.speakers[guest_dolphin]._listeners[host][host_dolphin]
            Transmitter.speakers[guest_dolphin].listeners[f'{host.split(":")[0]}:{data["listener_port"]}'] = listener_socket

            if host not in ConnectionsForDolphins[guest_dolphin]:
               ConnectionsForDolphins[guest_dolphin][host] = {}

            ConnectionsForDolphins[guest_dolphin][host][host_dolphin] = {
               "listener_address": (host.split(":")[0], data["listener_port"]),
               "speaker_address": (host.split(":")[0], data["speaker_port"])
            }

            print("guest -------------------")
            print(ConnectionsBySID)
            print(ConnectionsByPair)
            print(ConnectionsForDolphins)
         guest.on("handshake", guest_handshake)

         self.guest = guest

      # host
      if sys.argv[2][1] == "1": # Change this condition to Settings later
         host = socketio.Server()
         server = socketio.WSGIApp(host)

         def connect(sid, environ, auth):
            # for key in environ:
            #    print(f"{key}:             {environ[key]}\n")

            guest = f'{environ["REMOTE_ADDR"]}:{auth["Port"]}'
            if guest not in ConnectionsByPair:
               ConnectionsBySID[sid] = guest
               ConnectionsByPair[guest] = sid
            else:
               raise socketio.exceptions.ConnectionRefusedError(f'Guest \'{guest}\' is connected already.')
         host.on("connect", connect)

         def disconnect(sid):
            if sid in ConnectionsBySID:
               guest = ConnectionsBySID[sid]
               del ConnectionsBySID[sid]
               del ConnectionsByPair[guest]
         host.on("disconnect", disconnect)

         def host_handshake(sid, data):
            host_dolphin = data["host_dolphin"]
            guest_dolphin = data["guest_dolphin"]
            guest = ConnectionsBySID[sid]

            ConnectionsByAddress[host_dolphin][f'{guest.split(":")[0]}:{data["speaker_port"]}'] = {"pair": guest,
                                                                                                 "dolphin": guest_dolphin
                                                                                                 }

            if guest not in ConnectionsForDolphins[host_dolphin]:
               ConnectionsForDolphins[host_dolphin][guest] = {}

            ConnectionsForDolphins[host_dolphin][guest][guest_dolphin] = {
               "listener_address": (guest.split(":")[0], data["listener_port"]),
               "speaker_address": (guest.split(":")[0], data["speaker_port"])
            }

            ReturnHandshake(sid, data, guest, guest_dolphin, host_dolphin)

            print("host -------------------")
            print(ConnectionsBySID)
            print(ConnectionsByPair)
            print(ConnectionsForDolphins)
            print(sid)
         host.on("handshake", host_handshake)

         def ReturnHandshake(sid, data, guest, guest_dolphin, host_dolphin):
            listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener_socket.bind((Interface, 0))

            Transmitter.speakers[host_dolphin].listeners[f'{guest.split(":")[0]}:{data["listener_port"]}'] = listener_socket

            port = dolphins[host_dolphin]["Port"]
            speaker_port = listener_socket.getsockname()[1]
            host.emit("handshake", {"guest_dolphin": guest_dolphin, "host_dolphin": host_dolphin, "listener_port": port, "speaker_port": speaker_port}, room = sid)

         self.host = host

         eventlet.wsgi.server(eventlet.listen((Interface, Port)), server)

   # Issue: There must be a different guest for each connect
   def connect(self, host):
      address, port = host
      guest = copy.deepcopy(self.guest)

      def connect():
         # for attr in dir(guest):
         #    print(f"{attr}:            {guest.__getattribute__(attr)}\n")

         ConnectionsBySID["HOST"] = f'{address}:{port}'
         ConnectionsByPair[f'{address}:{port}'] = "HOST"
      guest.on("connect", connect)

      def connect_error(error):
         try: del hosts[f'{guest.host[0]}:{guest.host[1]}']
         except: pass
         print(error)
      guest.on("connect_error", connect_error)

      def disconnect():
         try: del hosts[f'{guest.host[0]}:{guest.host[1]}']
         except: pass
         print(f'{guest.host[0]}:{guest.host[1]} was disconnected.')
      guest.on("disconnect", disconnect)

      try:
         guest.connect(url = f'http://{address}:{port}', auth = {"Port": 5001}) # Replace 5001 with `Port` later.
      except: pass
      guest.host = host
      hosts[f'{address}:{port}'] = guest # Later, delete this entry when `connect_error` or `disconnect` events occur.

def InitiateHandshake(host, host_dolphin, guest_dolphin):
   try:
      listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      listener_socket.bind((Interface, 0))
      
      Transmitter.speakers[guest_dolphin]._listeners[f'{host[0]}:{host[1]}'] = {
         host_dolphin: listener_socket
      }

      port = dolphins[guest_dolphin]["Port"]
      speaker_port = listener_socket.getsockname()[1]
      guest = hosts[f'{host[0]}:{host[1]}']
      guest.emit("handshake", {"host_dolphin": host_dolphin, "guest_dolphin": guest_dolphin, "listener_port": port, "speaker_port": speaker_port})
   except KeyError:
      pass # Do something here

class Transmitter():
   def __init__(self, dolphin):
      self.dolphin = dolphin
      self.listeners = {}
      self._listeners = {}

      self.speaking = True

   speakers = {}

   def connect(self, listener):
      listener_socket = self.listeners[f'{listener[0]}:{listener[1]}']
      
      try: # Will this really work in all cases? How about disconnects due to timeout or anything else?
         listener_socket.getpeername()
      except:
         listener_socket.connect(listener)

      return listener_socket

   def speak(self, listener, data="", encoding="utf-8"):
      listener_socket = self.connect(listener)

      print(f'Sending: {data}')
      data = str(data+"\n").encode("utf-8")
      print(f'{listener_socket.sendall(data)}: {listener} - {listener_socket.getpeername()}')

   def disconnect(self):
      self.newspeaker.shutdown(socket.SHUT_RDWR)

   def stop(self):
      self.speaker.close()



class Handler(socketserver.StreamRequestHandler):
   def handle(self):
      self.data = self.rfile.readline().strip().decode("utf-8")
      print(f'Received: {self.data}')
      if not self.data.startswith("Hello"):
         speaker = Transmitter.speakers[self.dolphin]
         speaker.speak(("127.0.0.1", 8080), "Hello 10")
         return

      # Authenticate
      speaker_address = self.client_address
      if f'{speaker_address[0]}:{speaker_address[1]}' not in ConnectionsByAddress[self.dolphin]: return

      pair = ConnectionsByAddress[self.dolphin][f'{speaker_address[0]}:{speaker_address[1]}']["pair"]
      dolphin = ConnectionsByAddress[self.dolphin][f'{speaker_address[0]}:{speaker_address[1]}']["dolphin"]

      # self.data = str(self.rfile.readline().strip(), "utf-8")
      # print(self.data)

      listener_address = ConnectionsForDolphins[self.dolphin][pair][dolphin]["listener_address"]
      speaker = Transmitter.speakers[self.dolphin]
      speaker.speak(listener_address, f'{self.data.split()[0]} {int(self.data.split()[1]) + 10}')


def Processor(dolphin): # Try to change this into a class soon.
   handler = copy.deepcopy(Handler)
   handler.dolphin = dolphin
   handler.machine = dolphins[dolphin]["HandlerMachine"]
   return handler

handlers = {}

class Receiver():
   def __init__(self, dolphin):
      self.dolphin = dolphin
      self.address = (Interface, dolphins[dolphin]["Port"])
      handler = handlers[dolphin]

      self.listener = socketserver.ThreadingTCPServer(self.address, handler)
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
         try: Transmitter(self.speaker).speak_once() # Using up the last .handle_request(), if any from listen().
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

      elif self.service == "StartDolphin":
         dolphin = self.args["dolphin"]

         handler = Processor(dolphin)
         handlers[dolphin] = handler

         listener = Receiver(dolphin)
         Receiver.listeners[dolphin] = listener

         speaker = Transmitter(dolphin)
         Transmitter.speakers[dolphin] = speaker

         listener.listen()

      elif self.service == "StopListener":
         Receiver.listeners[self.args["dolphin"]].stop()


thread("Authentication").start()
thread("StartDolphin", args = {"dolphin": sys.argv[1]}).start()

if sys.argv[2][0] == "1":
   host = ("127.0.0.1", 5000)
   gateway.connect(host)
   while not hosts[f'{host[0]}:{host[1]}'].connected: pass # Is this really waiting??? Or do we even need to wait?
   else:
      InitiateHandshake(host, "Dan", "Deb")
# import time
# time.sleep(5)
# thread("StopListener", args = {"port": 8080}).start()