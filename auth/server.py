# import socketio
# import eventlet

# class Auth():
#    def __init__(self): pass
#    authenticators = {}

Auth.authenticators[8080] = Auth()

Auth.authenticators[8080].ConnectionsSID = {}
Auth.authenticators[8080].ConnectionsIP = {}

Auth.authenticators[8080].sio = socketio.Server()
Auth.authenticators[8080].app = socketio.WSGIApp(Auth.authenticators[8080].sio)

def do_handshake(sid, port):
   Auth.authenticators[8080].sio.emit("handshake", {"port": port}, room = sid)

@Auth.authenticators[8080].sio.event
def connect(sid, environ, _):
   ip = environ['REMOTE_ADDR']
   Auth.authenticators[8080].ConnectionsSID[sid] = ip
   Auth.authenticators[8080].ConnectionsIP[ip] = {
      "sid": sid,
      "port": None,
      "handshake_complete": False
      }

@Auth.authenticators[8080].sio.event
def disconnect(sid):
   ip = Auth.authenticators[8080].ConnectionsSID[sid]
   del Auth.authenticators[8080].ConnectionsSID[sid]
   del Auth.authenticators[8080].ConnectionsIP[ip]

@Auth.authenticators[8080].sio.event
def handshake(sid, data):
   ip = Auth.authenticators[8080].ConnectionsSID[sid]
   Auth.authenticators[8080].ConnectionsIP[ip]["port"] = data["port"]
   do_handshake(sid, 8080)

   Auth.authenticators[8080].ConnectionsIP[ip]["handshake_complete"] = True

eventlet.wsgi.server(eventlet.listen(("", 5000)), Auth.authenticators[8080].app)