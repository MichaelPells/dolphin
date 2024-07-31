import socket
import sys
import socketserver
import socketio
import eventlet
import threading
import copy
import json

settings = json.loads(open("./configurables/settings.json").read())
interface = settings["interface"] # Is the term 'interface' correct for this usage?
port = int(settings["port"])

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
      if sys.argv[2][0] == "1": # Change this condition to settings later
         guest = socketio.Client()

         def guest_handshake(data):
            GuestDolphin = data["GuestDolphin"]
            HostDolphin = data["HostDolphin"]
            host = ConnectionsBySID["HOST"]

            ConnectionsByAddress[GuestDolphin][f'{host.split(":")[0]}:{data["SpeakerPort"]}'] = {"pair": host,
                                                                                                 "dolphin": HostDolphin
                                                                                                 }
            ListenerSocket = Transmitter.speakers[GuestDolphin].ListenersTemp[host][HostDolphin]
            Transmitter.speakers[GuestDolphin].listeners[f'{host.split(":")[0]}:{data["ListenerPort"]}'] = ListenerSocket

            if host not in ConnectionsForDolphins[GuestDolphin]:
               ConnectionsForDolphins[GuestDolphin][host] = {}

            ConnectionsForDolphins[GuestDolphin][host][HostDolphin] = {
               "ListenerAddress": (host.split(":")[0], data["ListenerPort"]),
               "SpeakerAddress": (host.split(":")[0], data["SpeakerPort"])
            }

            print("guest -------------------")
            print(ConnectionsBySID)
            print(ConnectionsByPair)
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
            HostDolphin = data["HostDolphin"]
            GuestDolphin = data["GuestDolphin"]
            guest = ConnectionsBySID[sid]

            ConnectionsByAddress[HostDolphin][f'{guest.split(":")[0]}:{data["SpeakerPort"]}'] = {"pair": guest,
                                                                                                 "dolphin": GuestDolphin
                                                                                                 }

            if guest not in ConnectionsForDolphins[HostDolphin]:
               ConnectionsForDolphins[HostDolphin][guest] = {}

            ConnectionsForDolphins[HostDolphin][guest][GuestDolphin] = {
               "ListenerAddress": (guest.split(":")[0], data["ListenerPort"]),
               "SpeakerAddress": (guest.split(":")[0], data["SpeakerPort"])
            }

            ReturnHandshake(sid, data, guest, GuestDolphin, HostDolphin)

            print("host -------------------")
            print(ConnectionsBySID)
            print(ConnectionsByPair)
            print(ConnectionsForDolphins)
            print(sid)
         host.on("handshake", host_handshake)

         def ReturnHandshake(sid, data, guest, GuestDolphin, HostDolphin):
            ListenerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ListenerSocket.bind((interface, 0))

            Transmitter.speakers[HostDolphin].listeners[f'{guest.split(":")[0]}:{data["ListenerPort"]}'] = ListenerSocket

            port = dolphins[HostDolphin]["Port"]
            SpeakerPort = ListenerSocket.getsockname()[1]
            host.emit("handshake", {"GuestDolphin": GuestDolphin, "HostDolphin": HostDolphin, "ListenerPort": port, "SpeakerPort": SpeakerPort}, room = sid)

         self.host = host

         eventlet.wsgi.server(eventlet.listen((interface, port)), server)

   # Issue: There must be a different guest for each connect
   def connect(self, host):
      address, port = host
      newguest = copy.deepcopy(self.guest)

      def connect():
         # for attr in dir(newguest):
         #    print(f"{attr}:            {newguest.__getattribute__(attr)}\n")

         ConnectionsBySID["HOST"] = f'{address}:{port}'
         ConnectionsByPair[f'{address}:{port}'] = "HOST"
      newguest.on("connect", connect)

      def connect_error(error):
         try: del hosts[f'{newguest.host[0]}:{newguest.host[1]}']
         except: pass
         print(error)
      newguest.on("connect_error", connect_error)

      def disconnect():
         try: del hosts[f'{newguest.host[0]}:{newguest.host[1]}']
         except: pass
         print(f'{newguest.host[0]}:{newguest.host[1]} was disconnected.')
      newguest.on("disconnect", disconnect)

      try:
         newguest.connect(url = f'http://{address}:{port}', auth = {"Port": 5001}) # Replace 5001 with `Port` later.
      except: pass
      newguest.host = host
      hosts[f'{address}:{port}'] = newguest # Later, delete this entry when `connect_error` or `disconnect` events occur.

def InitiateHandshake(host, HostDolphin, GuestDolphin):
   try:
      ListenerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      ListenerSocket.bind((interface, 0))
      
      Transmitter.speakers[GuestDolphin].ListenersTemp[f'{host[0]}:{host[1]}'] = {
         HostDolphin: ListenerSocket
      }

      port = dolphins[GuestDolphin]["Port"]
      SpeakerPort = ListenerSocket.getsockname()[1]
      guest = hosts[f'{host[0]}:{host[1]}']
      guest.emit("handshake", {"HostDolphin": HostDolphin, "GuestDolphin": GuestDolphin, "ListenerPort": port, "SpeakerPort": SpeakerPort})
   except KeyError:
      pass # Do something here

class Transmitter():
   def __init__(self, dolphin):
      self.dolphin = dolphin
      self.listeners = {}
      self.ListenersTemp = {}

      self.speaking = True

   speakers = {}

   def connect(self, listener):
      ListenerSocket = self.listeners[f'{listener[0]}:{listener[1]}']
      
      try: # Will this really work in all cases? How about disconnects due to timeout or anything else?
         ListenerSocket.getpeername()
      except:
         ListenerSocket.connect(listener)

      return ListenerSocket

   def speak(self, listener, data="", encoding="utf-8"):
      ListenerSocket = self.connect(listener)

      print(f'Sending: {data}')
      data = str(data+"\n").encode("utf-8")
      print(f'{ListenerSocket.sendall(data)}: {listener} - {ListenerSocket.getpeername()}')

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
      SpeakerAddress = self.client_address
      if f'{SpeakerAddress[0]}:{SpeakerAddress[1]}' not in ConnectionsByAddress[self.dolphin]: return

      pair = ConnectionsByAddress[self.dolphin][f'{SpeakerAddress[0]}:{SpeakerAddress[1]}']["pair"]
      dolphin = ConnectionsByAddress[self.dolphin][f'{SpeakerAddress[0]}:{SpeakerAddress[1]}']["dolphin"]

      # self.data = str(self.rfile.readline().strip(), "utf-8")
      # print(self.data)

      ListenerAddress = ConnectionsForDolphins[self.dolphin][pair][dolphin]["ListenerAddress"]
      speaker = Transmitter.speakers[self.dolphin]
      speaker.speak(ListenerAddress, f'{self.data.split()[0]} {int(self.data.split()[1]) + 10}')


def Processor(dolphin): # Try to change this into a class soon.
   handler = copy.deepcopy(Handler)
   handler.dolphin = dolphin
   handler.machine = dolphins[dolphin]["HandlerMachine"]
   return handler

handlers = {}

class Receiver():
   def __init__(self, dolphin):
      self.dolphin = dolphin
      self.address = (interface, dolphins[dolphin]["Port"])
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