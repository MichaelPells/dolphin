def x():
    global s
    import s

def y():
    global s
    print(globals())

x()
y()
print("a")
#time.sleep(2)
print(globals())
