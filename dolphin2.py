import socket
import sys
import socketserver
import socketio
import eventlet
import threading
import copy

# class Auth():
#    def __init__(self): pass
#    authenticators = {}

ConnectionsSID = {}
ConnectionsIP = {}

# role: server
server = socketio.Server()
serverapp = socketio.WSGIApp(server)

def DoHandshakeAsServer(sid, port):
   server.emit("handshake", {"port": port}, room = sid)

@server.event
def connect(sid, environ, _):
   ip = environ['REMOTE_ADDR']
   ConnectionsSID[sid] = ip
   ConnectionsIP[ip] = {
      "sid": sid,
      "port": None,
      "handshake_complete": False
      }

@server.event
def disconnect(sid):
   ip = ConnectionsSID[sid]
   del ConnectionsSID[sid]
   del ConnectionsIP[ip]

@server.event
def handshake(sid, data):
   ip = ConnectionsSID[sid]
   ConnectionsIP[ip]["port"] = data["port"]
   DoHandshakeAsServer(sid, 8080)

   ConnectionsIP[ip]["handshake_complete"] = True

   print("server -------------------")
   print(ConnectionsSID)
   print(ConnectionsIP)
   print(sid)


# role: client
client = socketio.Client()

@client.event
def connect():
   DoHandshakeAsClient()

@client.event
def connect_error():
   pass

@client.event
def disconnect():
   pass

@client.event
def handshake(data):
   ConnectionsSID["HOST"] = "localhost"
   ConnectionsIP["localhost"] = {
      "sid": "HOST",
      "port": data["port"],
      "handshake_complete": True
      }
   
   print("client -------------------")
   print(ConnectionsSID)
   print(ConnectionsIP)


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
      if listener not in Authentication.authenticators[8080].ConnectionsIP: return  # Port should be an argument, here and everywhere else
      if not Authentication.authenticators[8080].ConnectionsIP[listener]["handshake_complete"]: return

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
         if self.args["role"] == "server":
            eventlet.wsgi.server(eventlet.listen(("", 5000)), serverapp)

         elif self.args["role"] == "client":
            # global DoHandshakeAsClient
            def DoHandshakeAsClient():
               newclient.emit("handshake", {"port": 8000})

            newclient = socketio.Client()

            def connect():
               DoHandshakeAsClient()
            newclient.on("connect", connect)

            def handshake(data):
               ConnectionsSID["HOST"] = "localhost"
               ConnectionsIP["localhost"] = {
                  "sid": "HOST",
                  "port": data["port"],
                  "handshake_complete": True
                  }
               
               print("client -------------------")
               print(ConnectionsSID)
               print(ConnectionsIP)
            newclient.on("handshake", handshake)

            # newclient = copy.deepcopy(client)
            newclient.connect("http://localhost:5000") # Address and port should be arguments, here and everywhere else

      elif self.service == "StartListener":
         listener = Receiver(self.args["speaker"])
         Receiver.listeners[self.args["speaker"][1]] = listener

         listener.listen()

      elif self.service == "StopListener":
         Receiver.listeners[self.args["port"]].stop()




thread("Authentication", args = {"port": int(sys.argv[1]), "role": sys.argv[2]}).start()
thread("StartListener", args = {"speaker": ("", int(sys.argv[1]))}).start()
# import time
# time.sleep(5)
# thread("StopListener", args = {"port": 8080}).start()