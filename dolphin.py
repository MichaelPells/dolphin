import sys
import socket
import http.server
import eventlet
import socketserver
import socketio
import eventlet
import threading
import copy
import json
from multiprocessing import Process
from wsgiref import simple_server
import urllib

Settings = json.loads(open("./configurables/settings.json").read())
Interface = Settings["Interface"] # Is the term 'Interface' correct for this usage?
Port = int(sys.argv[1]) if len(sys.argv) > 1 else int(Settings["Port"]) # This solution has not considered other use cases yet.
Role = Settings["Role"]

protocol_delimeter = "\nDOLPHIN\n".encode("utf-8")
socketio_path = "auth"

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
      if Role == "guest" or Role == "any":
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
            # del Transmitter.speakers[guest_dolphin]._listeners[host] # Check for and do this later

            # Implement this: If handshake instruction specifies remote will be transmitting
            Transmitter.speakers[guest_dolphin].speak((host.split(":")[0], data["listener_port"]))

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
      if Role == "host" or Role == "any":
         host = socketio.Server()

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
            
            # Implement this: If handshake instruction specifies remote will be transmitting
            Transmitter.speakers[host_dolphin].speak((guest.split(":")[0], data["listener_port"]))

            port = dolphins[host_dolphin]["Port"]
            speaker_port = listener_socket.getsockname()[1]
            host.emit("handshake", {"guest_dolphin": guest_dolphin, "host_dolphin": host_dolphin, "listener_port": port, "speaker_port": speaker_port}, room = sid)

         self.host = host

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
         guest.connect(url = f'http://{address}:{port}', auth = {"Port": 5001}, socketio_path=socketio_path) # Replace 5001 with `Port` later.
         guest.host = host
         hosts[f'{address}:{port}'] = guest # Later, delete this entry when `connect_error` or `disconnect` events occur.
      except:
         pass # Return an error here later

def InitiateHandshake(host, host_dolphin, guest_dolphin):
   try:
      listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      listener_socket.bind((Interface, 0))
      
      Transmitter.speakers[guest_dolphin]._listeners[host] = {
         host_dolphin: listener_socket
      }

      port = dolphins[guest_dolphin]["Port"]
      speaker_port = listener_socket.getsockname()[1]
      guest = hosts[host]
      guest.emit("handshake", {"host_dolphin": host_dolphin, "guest_dolphin": guest_dolphin, "listener_port": port, "speaker_port": speaker_port})
   except KeyError:
      pass # Do something here



class Receiver():
   def __init__(self, dolphin):
      self.dolphin = dolphin
      self.address = (Interface, dolphins[dolphin]["Port"])
      
      self.speakers = {}
      self.buffers = {}
      self.messages = {}

      self.listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.listener.bind(self.address)
      self.listener.listen(5)

      self.listening = False

   listeners = {}

   class thread(threading.Thread):
      def __init__(_self, self, stage, connection, address):
         threading.Thread.__init__(_self)
         _self.self = self
         _self.stage = stage
         _self.connection = connection
         _self.address = address

      def run(_self):
         stages = {
            1: Receiver.listeners[_self.self.dolphin],
            2: Processor.handlers[_self.self.dolphin],
         }

         stages[_self.stage].action(_self.connection, _self.address)

   def listen(self):
      self.listening = True
      try:
         while self.listening:
            self.listen_once()

      except KeyboardInterrupt: # Hasn't been working. Why?
         pass

   def listen_once(self):
      connection, address = self.listener.accept()

      # # Authenticate
      # if f'{address[0]}:{address[1]}' not in ConnectionsByAddress[self.dolphin]: pass

      # speaker = ConnectionsByAddress[self.dolphin][f'{address[0]}:{address[1]}']
      self.thread(self, 1, connection, address).start()
      self.thread(self, 2, connection, address).start()

   def action(self, connection, address):
      self.buffers[f'{address[0]}:{address[1]}'] = b''
      self.messages[f'{address[0]}:{address[1]}'] = []

      state = "new"

      while True:
         data = connection.recv(4096)

         if not data: # Don't joke with this part... To capture shutdown advisories, failures, broken connections etc.
            connection.close()
            # Take further actions here.
            # Also verify what happens when client closes the connection.
            break

         self.buffers[f'{address[0]}:{address[1]}'] += data

         # Application-Layer Protocol:
         if state == "new":
            if protocol_delimeter in self.buffers[f'{address[0]}:{address[1]}']:
               self.buffers[f'{address[0]}:{address[1]}'] = self.buffers[f'{address[0]}:{address[1]}'].removeprefix(protocol_delimeter)
               
               state = "headers"

         if state == "headers":
            if b"\n" in self.buffers[f'{address[0]}:{address[1]}']:
               raw_headers = self.buffers[f'{address[0]}:{address[1]}'][:self.buffers[f'{address[0]}:{address[1]}'].index(b"\n") + 1]
               self.buffers[f'{address[0]}:{address[1]}'] = self.buffers[f'{address[0]}:{address[1]}'].removeprefix(raw_headers)

               headers = json.loads(raw_headers.decode("utf-8").strip())

               state = "content"

         if state == "content":
            if len(self.buffers[f'{address[0]}:{address[1]}']) >= headers["content-length"]:
               content = self.buffers[f'{address[0]}:{address[1]}'][:headers["content-length"]]
               self.buffers[f'{address[0]}:{address[1]}'] = self.buffers[f'{address[0]}:{address[1]}'].removeprefix(content)

               content = content.decode(headers["content-encoding"] if "content-encoding" in headers else "utf-8")
               message = {
                  "headers": headers,
                  "content": content
               }
               self.messages[f'{address[0]}:{address[1]}'].append(message)

               state = "new"

   def stop(self):
      if self.listening:
         self.listening = False
         try: Transmitter(self.speaker).speak_once() # Using up the last .accept(), if any from listen_once().
         except: pass

   def close(self):
         self.stop()
         print("trying to close the server")
         self.listener.shutdown(socket.SHUT_RD)
         self.listener.close()
         # Close all child sockets too
         print("Server stopped!")

class Processor():
   def __init__(self, dolphin):
      self.dolphin = dolphin
      self.handler = dolphins[dolphin]["Handler"]

   handlers = {}

   def action(self, connection, speaker_address):
      while True:
         if len(Receiver.listeners[self.dolphin].messages[f'{speaker_address[0]}:{speaker_address[1]}']) > 0:
            message = Receiver.listeners[self.dolphin].messages[f'{speaker_address[0]}:{speaker_address[1]}'].pop(0)
            # print(message)
            # print(f"Message: {Receiver.listeners[self.dolphin].messages[f'{speaker_address[0]}:{speaker_address[1]}']}")
            # print(f"Buffer: {Receiver.listeners[self.dolphin].buffers[f'{speaker_address[0]}:{speaker_address[1]}']}")

            def speak(address, message):
               Transmitter.speakers[self.dolphin].messages[f'{address[0]}:{address[1]}'].append(message)

            # ------------------- handler subroutine
            content = message["content"]

            print(content)

            if not content.startswith("Hello"):
               response = "Hello 10"
               reply = {
                  "headers": {"content-length": len(response)},
                  "content": response
               }
               speak(("127.0.0.1", 8080), reply)
               return

            pair = ConnectionsByAddress[self.dolphin][f'{speaker_address[0]}:{speaker_address[1]}']["pair"]
            dolphin = ConnectionsByAddress[self.dolphin][f'{speaker_address[0]}:{speaker_address[1]}']["dolphin"]

            listener_address = ConnectionsForDolphins[self.dolphin][pair][dolphin]["listener_address"]

            response = f'{content.split()[0]} {int(content.split()[1]) + 10}'
            reply = {
               "headers": {"content-length": len(response)},
               "content": response
            }

            speak(listener_address, reply)
            # ------------------- handler subroutine

class Transmitter():
   def __init__(self, dolphin):
      self.dolphin = dolphin

      self.listeners = {}
      self._listeners = {}
      self.messages = {}

      self.speaking = True

   speakers = {}

   class thread(threading.Thread):
      def __init__(_self, self, address):
         threading.Thread.__init__(_self)
         _self.self = self
         _self.address = address

      def run(_self):
         Transmitter.speakers[_self.self.dolphin].action(_self.address)

   def speak(self, address):
      self.thread(self, address).start()

   def connect(self, listener):
      listener_socket = self.listeners[f'{listener[0]}:{listener[1]}']
      
      try: # Will this really work in all cases? How about disconnects due to timeout or anything else?
         listener_socket.getpeername()
      except:
         listener_socket.connect(listener)

      return listener_socket

   def action(self, address):
      self.messages[f'{address[0]}:{address[1]}'] = []

      while True:
         if len(self.messages[f'{address[0]}:{address[1]}']) > 0:
            message = self.messages[f'{address[0]}:{address[1]}'].pop(0)
            headers = f'{json.dumps(message["headers"])}\n'.encode("utf-8")
            content = message["content"].encode(message["headers"]["content-encoding"] if "content-encoding" in message["headers"] else "utf-8")
            data = protocol_delimeter + headers + content
            
            listener_socket = self.connect(address)

            listener_socket.sendall(data)

   def disconnect(self):
      self.newspeaker.shutdown(socket.SHUT_RDWR)

   def stop(self):
      self.speaker.close()



class thread(threading.Thread):
   def __init__(self, service, args = {}):
      threading.Thread.__init__(self)
      self.service = service
      self.args = args

   def run(self):
      if self.service == "StartDolphin":
         dolphin = self.args["dolphin"]

         handler = Processor(dolphin)
         Processor.handlers[dolphin] = handler

         listener = Receiver(dolphin)
         Receiver.listeners[dolphin] = listener

         speaker = Transmitter(dolphin)
         Transmitter.speakers[dolphin] = speaker

         listener.listen()

      elif self.service == "StopListener":
         Receiver.listeners[self.args["dolphin"]].stop()


def start(args):
   dolphin = args[0]
   thread("StartDolphin", args = {"dolphin": dolphin}).start()

def connect(args):
   host = args[0]
   host_addr = host.split(":")
   host_ip = host_addr[0]
   host_port = int(host_addr[1])
   gateway.connect((host_ip, host_port))

def handshake(args):
   host = args[2]
   if hosts[host].connected:
      InitiateHandshake(host, args[1], args[0])
   else:
      pass # Report error here

commands = [
   "start",
   "stop",
   "connect",
   "handshake"
]

def run(raw_input):
   Input = raw_input.split(" ") # Work on this
   command = Input[0].lower()
   args = Input[1:]

   if command in commands:
      globals()[command](args)

gateway = Authentication()

def Input(environ, start_response):
   raw_input = environ["wsgi.input"].read().strip().decode('utf-8')

   threading.Thread(target=run, args=[raw_input]).start()

   status = "200 OK"
   headers = [
      ("Content-Type", "text/plain")
   ]

   start_response(status, headers)
   return [raw_input.encode()]

def listen():
   app = socketio.WSGIApp(gateway.host, Input, socketio_path=socketio_path)
   eventlet.wsgi.server(eventlet.listen((Interface, Port)), app, log_output=False)

threading.Thread(target=listen).start()
