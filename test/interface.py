import os

path = os.getcwd().split("\\")
for d in range(0, len(path)):
    try:
        open("\\".join(path[:d+1])+"\\jumper", "w").close()
        os.remove("\\".join(path[:d+1])+"\\jumper")
        path = "\\".join(path[:d+1])
        print(path)
        break
    except: pass
