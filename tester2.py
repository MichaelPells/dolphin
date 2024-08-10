# import socket
# import threading
# import time

# status = {}
# status["_closed"] = True

# def create_socket(port):
#    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    sock.bind(("", port))
#    sock.listen(5)

#    while True:
#       conn, addr = sock.accept()
#       while True:
#          data = conn.recv(1024)
#          print(f'SOCK {port}: {data}')

# threading.Thread(target=create_socket, args=(3000))
# threading.Thread(target=create_socket, args=(4000))

# time.sleep(10)

class o:
    a = True

cat = o
dog = o
dog = cat

print(dog.a)
cat.a = False
print(dog.a)