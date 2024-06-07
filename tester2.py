import socketio
import eventlet

# class Auth():
#    def __init__(self): pass
#    authenticators = {}

# Auth.authenticators[8080] = Auth()

ConnectionsSID = {}
ConnectionsIP = {}

sio = socketio.Server()
app = socketio.WSGIApp(sio)

def do_handshake(sid, port):
   sio.emit("handshake", {"port": port}, room = sid)

   print(f"Handshake accepted:   {ConnectionsIP}")

@sio.event
def connect(sid, environ, _):
   print("connected:", sid)
   sio.emit("hello", {"port": "port"}, room = sid)
   ip = environ['REMOTE_ADDR']
   ConnectionsSID[sid] = ip
   ConnectionsIP[ip] = {
      "sid": sid,
      "port": None,
      "handshake_complete": False
      }

@sio.event
def disconnect(sid):
   ip = ConnectionsSID[sid]
   del ConnectionsSID[sid]
   del ConnectionsIP[ip]
   print("disconnected")

@sio.event
def handshake(sid, data):
   ip = ConnectionsSID[sid]
   ConnectionsIP[ip]["port"] = data["port"]
   do_handshake(sid)

   ConnectionsIP[ip]["handshake_complete"] = True

   print(f"Handshake complete:   {ConnectionsIP}")

eventlet.wsgi.server(eventlet.listen(("", 5000)), app)