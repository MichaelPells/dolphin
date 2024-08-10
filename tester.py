import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", 8000))

message = """
DOLPHIN
{"content-length": 2}
Hi"""

sock.sendall(bytes(message, "utf-8"))