import socket
import requests
import threading
import time

serving = False

def server():
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("", 4000))
    listener.listen(5)

    global serving
    serving = True

    connection, address = listener.accept()
    print(address)

    message = b''

    while True:
        data = connection.recv(4096)
        # if not data:
        break

    message = b'HTTP/1.1 200 OK \r\nContent-Type: text/plain\r\nContent-Length: 5\r\n\r\nHELLO'
    connection.sendall(message + b'\n')
    connection.close()

def client():
    global serving
    while not serving: pass

    print("now sending")
    response = requests.post("http://127.0.0.1:4000", data="Hello")
    print(response.elapsed)
    print(response.text)

    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.connect(("127.0.0.1", 4000))
    # print(sock.getpeername())

    # message = "Hello"

    # sock.sendall(bytes(message, "utf-8"))
    # response = sock.recv(4096)
    # print(response)

threading.Thread(target=server).start()
threading.Thread(target=client).start()
