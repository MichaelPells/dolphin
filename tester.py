class A():
    def __init__(self):
        self.x = 20
    def y(self):
        return True

def hello():
    return False

a = A()
a.z = hello

b = A()
print(a.__dir__())