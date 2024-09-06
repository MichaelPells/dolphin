import io
import threading

display = io.StringIO()
integrity = threading.Lock()

def write(message="", end="\n"):
    with integrity:
        display.seek(0, io.SEEK_END)
        display.write(str(message) + end)

def all():
    with integrity:
        display.seek(0)
        logs = display.read()
        display.truncate(0)

    return logs

def last():
    with integrity:
        try:
            display.seek(0)
            logs =  display.readlines()[-1]
        except IndexError:
            logs = None

    return logs