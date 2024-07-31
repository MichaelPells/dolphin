import socket

ListenerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print(ListenerSocket.getsockname())