# import socketio
# import eventlet

# class Auth():
#    def __init__(self): pass
#    authenticators = {}

Auth.authenticators[8000] = Auth()

Auth.authenticators[8000].ConnectionsSID = {}
Auth.authenticators[8000].ConnectionsIP = {}

Auth.authenticators[8000].sio = socketio.Client()

def do_handshake():
   Auth.authenticators[8000].sio.emit("handshake", {"port": 8000})

@Auth.authenticators[8000].sio.event
def connect():
   do_handshake()

@Auth.authenticators[8000].sio.event
def connect_error():
   pass

@Auth.authenticators[8000].sio.event
def disconnect():
   pass

@Auth.authenticators[8000].sio.event
def handshake(data):
   Auth.authenticators[8000].ConnectionsSID["HOST"] = "localhost"
   Auth.authenticators[8000].ConnectionsIP["localhost"] = {
      "sid": "HOST",
      "port": data["port"],
      "handshake_complete": True
      }

Auth.authenticators[8000].sio.connect("http://localhost:5000") # Address and port should be arguments, here and everywhere else
